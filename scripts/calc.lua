-- Inserter throughput model.
--
-- All constants below were calibrated against Factorio 2.1.22 by measuring real
-- inserters tick by tick in a headless server (see README.md for the numbers).
--
--  * A half swing (pickup -> drop or back) takes
--      max(ceil(angle / rotation_speed) - 1, ceil(|r_drop - r_pickup| / extension_speed) - 1)
--    ticks, where angle is in revolutions and r is the hand distance from the inserter.
--  * Taking from / putting into a chest or machine adds no time.
--  * Dropping k stacks onto a belt lane adds max(k - 1, floor((k - 2) * 0.25 / belt_speed)) ticks
--    (k >= 2). A lane carries at most belt_speed / 0.25 stacks per tick.
--  * Taking k stacks from a fully compressed belt: the physics estimate 2 * half_swing +
--    (k - 1) * max(1, 0.2 / extension_speed) is corrected by a small gradient boosted tree model
--    (scripts/pickup_model.lua) trained on engine measurements, because the hand chases items on the
--    belt. Mean error ~2% on vanilla inserters, so the value is shown as approximate.

local pickup_model = require("scripts.pickup_model")

local calc = {}

local ITEM_SPACING = 0.25   -- tiles between two items on a belt lane
local PICKUP_REACH = 0.2    -- tiles; empirical average hand travel between two belt pickups
local UPSTREAM_BELTS = 4    -- belts inspected to find out how items are stacked on the input belt
local STACK_SAMPLE = 8      -- item stacks that are enough to tell the stack size on a belt
local PICKUP_CACHE_LIMIT = 4096 -- remembered pickup model results
local EPSILON = 1e-6

calc.belt_types = {
  ["transport-belt"] = true,
  ["underground-belt"] = true,
  ["splitter"] = true,
  ["lane-splitter"] = true,
  ["loader"] = true,
  ["loader-1x1"] = true,
  ["linked-belt"] = true,
}
local belt_type_list = {}
for type in pairs(calc.belt_types) do belt_type_list[#belt_type_list + 1] = type end

function calc.is_inserter(entity)
  if not (entity and entity.valid) then return false end
  if entity.type == "inserter" then return true end
  return entity.type == "entity-ghost" and entity.ghost_type == "inserter"
end

local function is_ghost(entity)
  return entity.type == "entity-ghost"
end

--- Ticks needed to cover `distance` at `speed` per tick for one half swing.
local function half_swing_ticks(distance, speed)
  if distance <= EPSILON then return 0 end
  if not speed or speed <= 0 then return math.huge end
  return math.ceil(distance / speed - EPSILON) - 1
end

local function vector_length(v)
  return math.sqrt(v.x * v.x + v.y * v.y)
end

--- Angle between two vectors in revolutions, always the short way round (0..0.5).
local function angle_between(a, b)
  if vector_length(a) <= EPSILON or vector_length(b) <= EPSILON then return 0 end
  local diff = math.abs(math.atan2(a.y, a.x) - math.atan2(b.y, b.x))
  if diff > math.pi then diff = 2 * math.pi - diff end
  return diff / (2 * math.pi)
end

--- Finds a belt-like entity (or belt ghost) under a map position.
local function find_belt_at(surface, position)
  local found = surface.find_entities_filtered{position = position, type = belt_type_list, limit = 1}[1]
  if found then return found end
  return surface.find_entities_filtered{position = position, ghost_type = belt_type_list, limit = 1}[1]
end

local function belt_prototype(entity)
  if is_ghost(entity) then return entity.ghost_prototype end
  return entity.prototype
end

--- Finds something an inserter could take from or put into (or its ghost) under a map position.
local function find_container_at(surface, position, inserter)
  for _, entity in pairs(surface.find_entities_filtered{position = position}) do
    if entity ~= inserter then
      if entity.type == "entity-ghost" then
        if entity.ghost_type ~= "inserter" then return entity end
      elseif entity.get_max_inventory_index() > 0 then
        return entity
      end
    end
  end
  return nil
end

--- Classifies what sits at one end of the inserter: "belt", "entity" or "none".
local function classify_target(inserter, target, position)
  if target and target.valid then
    if calc.belt_types[target.type] then
      return "belt", target
    end
    if target.type == "entity-ghost" and calc.belt_types[target.ghost_type] then
      return "belt", target
    end
    return "entity", target
  end
  local belt = find_belt_at(inserter.surface, position)
  if belt then return "belt", belt end
  local container = find_container_at(inserter.surface, position, inserter)
  if container then return "entity", container end
  return "none", nil
end

--- Evaluates the pickup model: log(measured cycle / physics cycle).
local function evaluate_pickup_model(features)
  local sum = 0
  for _, tree in pairs(pickup_model.trees) do
    local feature, threshold, left, right = tree.f, tree.t, tree.l, tree.r
    local node = 1
    while feature[node] ~= 0 do
      if features[feature[node]] <= threshold[node] then
        node = left[node]
      else
        node = right[node]
      end
    end
    sum = sum + tree.v[node]
  end
  return pickup_model.base + pickup_model.rate * sum
end

--- Same features, in the same order, as train_pickup_model.py.
local function pickup_features(half_swing, rotation_speed, extension_speed, radius, belt_speed, pickups, lanes, stack)
  local step = math.max(1, PICKUP_REACH / extension_speed)
  local tangential = 2 * math.pi * radius * rotation_speed
  return {
    half_swing, math.log(rotation_speed), math.log(extension_speed), radius, belt_speed, pickups, lanes, stack,
    belt_speed / extension_speed,
    belt_speed / tangential,
    ITEM_SPACING / (lanes * belt_speed) / step,
    (pickups - 1) * step,
    (pickups - 1) * ITEM_SPACING / (lanes * belt_speed),
  }
end

-- Model results by input; a base has few distinct combinations and the model takes ~0.2 ms to evaluate.
-- The cache only saves time, results are the same with or without it.
local pickup_cache = {}
local pickup_cache_size = 0

local function predict_pickup_correction(half_swing, rotation_speed, extension_speed, radius, belt_speed, pickups, lanes, stack)
  local key = table.concat({half_swing, rotation_speed, extension_speed, radius, belt_speed, pickups, lanes, stack}, ",")
  local cached = pickup_cache[key]
  if cached then return cached end
  local correction = evaluate_pickup_model(pickup_features(half_swing, rotation_speed, extension_speed, radius,
    belt_speed, pickups, lanes, stack))
  if pickup_cache_size >= PICKUP_CACHE_LIMIT then
    pickup_cache, pickup_cache_size = {}, 0
  end
  pickup_cache[key] = correction
  pickup_cache_size = pickup_cache_size + 1
  return correction
end

--- Average stack size of the items on the input belt, 1 if it is empty. Looks at the pickup belt first
--- and then at the belts feeding it, until it has seen enough items. The second result is false when the
--- belt is empty, so the stack size is not known yet.
local function belt_item_stack(belt)
  if is_ghost(belt) then return 1, true end
  local stacks, items = 0, 0
  local visited = {}
  local current = belt
  for _ = 0, UPSTREAM_BELTS do
    visited[current.unit_number] = true
    for index = 1, current.get_max_transport_line_index() do
      local line = current.get_transport_line(index)
      stacks = stacks + #line
      items = items + line.get_item_count()
    end
    if stacks >= STACK_SAMPLE then break end
    local inputs = current.belt_neighbours.inputs
    local previous = inputs[1]
    for _, input in pairs(inputs) do
      -- Prefer the belt directly behind over side-loading ones.
      if input.direction == current.direction then
        previous = input
        break
      end
    end
    if not previous or visited[previous.unit_number] then break end
    current = previous
  end
  if stacks == 0 then return 1, false end
  return math.max(1, math.floor(items / stacks + 0.5)), true
end

--- The item the inserter moves, when it can be known.
local function moved_item(inserter)
  if not is_ghost(inserter) then
    local held = inserter.held_stack
    if held and held.valid_for_read then return held.prototype end
  end
  local ok, use_filters = pcall(function() return inserter.use_filters end)
  if ok and use_filters and inserter.inserter_filter_mode == "whitelist" then
    local only
    for slot = 1, inserter.filter_slot_count do
      local filter = inserter.get_filter(slot)
      if filter then
        if only or not filter.name then return nil end
        only = filter.name
      end
    end
    if only then return prototypes.item[only] end
  end
  return nil
end

--- Hand size: maximum from the prototype and research, and the value currently used.
local function hand_size(inserter, proto, force)
  local base = 1 + (proto.inserter_stack_size_bonus or 0)
  local research = 0
  if proto.uses_inserter_stack_size_bonus ~= false then
    if proto.bulk then
      research = force.bulk_inserter_capacity_bonus
    else
      research = math.floor(force.inserter_stack_size_bonus + EPSILON)
    end
  end
  local max = base + research
  local current = max
  if is_ghost(inserter) then
    local ok, override = pcall(function() return inserter.inserter_stack_size_override end)
    if ok and override and override > 0 then current = math.min(max, override) end
  else
    -- Takes manual override, circuit network and research into account.
    current = math.min(max, inserter.inserter_target_pickup_count)
  end
  local behavior = not is_ghost(inserter) and inserter.get_control_behavior()
  local circuit = behavior and behavior.circuit_set_stack_size or false
  return {base = base, research = research, max = max, current = math.max(1, current), circuit = circuit}
end

--- Full analysis of one inserter (real or ghost). `dynamic` is set when the result depends on things that
--- change without an event: an input belt that is still empty, or a hand size set by the circuit network.
function calc.analyze(inserter)
  local proto = is_ghost(inserter) and inserter.ghost_prototype or inserter.prototype
  local quality = inserter.quality
  local force = inserter.force

  local result = {ghost = is_ghost(inserter)}

  -- Geometry of the swing.
  local origin = inserter.position
  local pickup_position = inserter.pickup_position
  local drop_position = inserter.drop_position
  local pickup_vector = {x = pickup_position.x - origin.x, y = pickup_position.y - origin.y}
  local drop_vector = {x = drop_position.x - origin.x, y = drop_position.y - origin.y}
  local rotation_speed = proto.get_inserter_rotation_speed(quality)
  local extension_speed = proto.get_inserter_extension_speed(quality)
  local turns = angle_between(pickup_vector, drop_vector)
  local reach = math.abs(vector_length(drop_vector) - vector_length(pickup_vector))
  result.rotation_speed = rotation_speed
  result.extension_speed = extension_speed
  result.rotation_ticks = half_swing_ticks(turns, rotation_speed)
  result.extension_ticks = half_swing_ticks(reach, extension_speed)
  result.half_swing = math.max(1, result.rotation_ticks, result.extension_ticks)

  -- Hand size.
  local hand = hand_size(inserter, proto, force)
  local known, item = pcall(moved_item, inserter)
  if not known then item = nil end
  result.item = item
  result.hand_base = hand.base
  result.hand_research = hand.research
  result.hand_max = hand.max
  result.hand_current = hand.current
  -- The circuit network can change the hand size at any time.
  if hand.circuit then result.dynamic = true end
  result.hand_limited = hand.current < hand.max
  local items = hand.current
  local max_items = hand.max
  if item then
    result.item_stack_size = item.stack_size
    if item.stack_size < items then result.hand_capped_by_item = true end
    items = math.min(items, item.stack_size)
    max_items = math.min(max_items, item.stack_size)
  end

  -- What is at both ends.
  local pickup_kind, pickup_entity = classify_target(inserter, not result.ghost and inserter.pickup_target or nil, pickup_position)
  local drop_kind, drop_entity = classify_target(inserter, inserter.drop_target, drop_position)
  result.pickup_kind = pickup_kind
  result.drop_kind = drop_kind

  local limit_per_tick = math.huge
  local limiter = "swing"

  -- Dropping onto a belt: stack inserters build stacks, the rest place items one by one.
  local drop_extra = 0
  if drop_kind == "belt" then
    local belt_speed = belt_prototype(drop_entity).belt_speed
    local belt_stack = 1
    local proto_belt_stack = proto.inserter_max_belt_stack_size or 1
    if proto_belt_stack > 1 then
      belt_stack = math.min(proto_belt_stack, 1 + force.belt_stack_size_bonus)
    end
    if item then belt_stack = math.max(1, math.min(belt_stack, item.stack_size)) end
    if proto.grab_less_to_match_belt_stack and belt_stack > 1 and items >= belt_stack then
      -- Grabs only whole belt stacks so it never drops a partial one.
      items = math.floor(items / belt_stack) * belt_stack
    end
    local drops = math.ceil(items / belt_stack)
    if drops >= 2 then
      local gap = ITEM_SPACING / belt_speed
      drop_extra = math.max(drops - 1, math.floor((drops - 2) * gap + EPSILON))
    end
    local lane_limit = belt_speed / ITEM_SPACING * belt_stack
    if lane_limit < limit_per_tick then
      limit_per_tick = lane_limit
      limiter = "lane"
    end
    result.drop_belt_speed = belt_speed
    result.drop_belt_stack = belt_stack
  end

  -- Taking from a belt, assumed fully compressed (the best case): approximate.
  local swing = 2 * result.half_swing
  local pickup_extra = 0
  if pickup_kind == "belt" then
    local belt_speed = belt_prototype(pickup_entity).belt_speed
    local left_lane, right_lane = true, true
    if not result.ghost then
      left_lane = inserter.pickup_from_left_lane
      right_lane = inserter.pickup_from_right_lane
    end
    local lanes = (left_lane and 1 or 0) + (right_lane and 1 or 0)
    local source_stack, stack_known = belt_item_stack(pickup_entity)
    if not stack_known then result.dynamic = true end
    if item then source_stack = math.max(1, math.min(source_stack, item.stack_size)) end
    if lanes == 0 then
      limit_per_tick = 0
      limiter = "supply"
    else
      local pickups = math.ceil(items / source_stack)
      local physics = swing + (pickups - 1) * math.max(1, PICKUP_REACH / extension_speed)
      local correction = predict_pickup_correction(result.half_swing, rotation_speed, extension_speed,
        vector_length(pickup_vector), belt_speed, pickups, lanes, source_stack)
      correction = math.max(-0.7, math.min(0.7, correction))
      pickup_extra = physics * math.exp(correction) - swing
      local supply_limit = lanes * belt_speed / ITEM_SPACING * source_stack
      if supply_limit < limit_per_tick then
        limit_per_tick = supply_limit
        limiter = "supply"
      end
    end
    result.pickup_belt_speed = belt_speed
    result.pickup_belt_stack = source_stack
    result.approximate = true
  end

  result.items_per_swing = items
  result.pickup_extra = pickup_extra
  result.drop_extra = drop_extra
  result.cycle = swing + pickup_extra + drop_extra

  local per_tick = items / result.cycle
  if per_tick <= limit_per_tick then
    limiter = "swing"
  else
    per_tick = limit_per_tick
  end
  result.limiter = limiter
  result.rate = per_tick * 60
  -- Best case: chest to chest with a full hand.
  result.max_rate = max_items / (2 * result.half_swing) * 60
  return result
end

return calc
