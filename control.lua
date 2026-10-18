local calc = require("scripts.calc")
local display = require("scripts.display")

local REFRESH_INTERVAL = 30   -- ticks between tooltip updates while hovered
local MEASURE_WINDOW = 600    -- ticks of history used for the measured rate
local MIN_MEASURE = 60        -- ticks to wait before showing a measured rate
local UPDATES_PER_TICK = 10   -- inserters whose tooltip is prepared in the background each tick (~0.5 ms)
local CLEARS_PER_TICK = 200   -- inserters whose tooltip lines are removed each tick when preparing is off
local MIN_REACH = 3           -- tiles around a changed entity searched for inserters that may use it

-- Tooltips are written into every inserter ahead of time, so hovering shows them at once. Waiting for
-- on_selected_entity_changed instead costs a full network round trip in multiplayer.
--
-- storage.tracked[unit_number] = {
--   entity, players = {[player_index] = true}, labels = {[player_index] = LuaRenderObject},
--   measurement = {start, previous, events}, cycle
-- }                                      inserters someone hovers: refreshed often, measured
-- storage.queue, storage.queue_keys      inserters waiting for a background update (entity, unit_number)
-- storage.queue_position                 next queue index to process
-- storage.queued[unit_number] = true     inserters already in the queue
-- storage.bonuses[force_index]           research bonuses the queued updates were based on
-- storage.announce_cleanup               tell players when all lines are removed (preparing was turned off)
-- storage.reach                          tiles from an inserter to its farthest pickup or drop point

local function prepare_ahead()
  return settings.global["inserter-hover-throughput-prepare-ahead"].value
end

local function max_reach()
  local reach = MIN_REACH
  for _, proto in pairs(prototypes.get_entity_filtered{{filter = "type", type = "inserter"}}) do
    for _, vector in pairs{proto.inserter_pickup_position, proto.inserter_drop_position} do
      local length = math.sqrt(vector[1] * vector[1] + vector[2] * vector[2]) + 1
      if length > reach then reach = length end
    end
  end
  return reach
end

local function bonuses(force)
  return {force.inserter_stack_size_bonus, force.bulk_inserter_capacity_bonus, force.belt_stack_size_bonus}
end

local function enqueue(entity)
  local key = entity.unit_number
  if not key or storage.queued[key] then return end
  storage.queued[key] = true
  local position = #storage.queue + 1
  storage.queue[position] = entity
  storage.queue_keys[position] = key
end

--- Queues every inserter and inserter ghost, of one force or of all forces.
local function enqueue_all(force)
  for _, surface in pairs(game.surfaces) do
    for _, entity in pairs(surface.find_entities_filtered{type = "inserter", force = force}) do
      enqueue(entity)
    end
    for _, entity in pairs(surface.find_entities_filtered{ghost_type = "inserter", force = force}) do
      enqueue(entity)
    end
  end
end

--- Queues the inserters that may pick up from or drop into the given entity.
local function enqueue_near(entity)
  local box = entity.bounding_box
  local reach = storage.reach
  local area = {
    {box.left_top.x - reach, box.left_top.y - reach},
    {box.right_bottom.x + reach, box.right_bottom.y + reach},
  }
  local surface = entity.surface
  for _, inserter in pairs(surface.find_entities_filtered{area = area, type = "inserter"}) do
    enqueue(inserter)
  end
  for _, inserter in pairs(surface.find_entities_filtered{area = area, ghost_type = "inserter"}) do
    enqueue(inserter)
  end
end

local function init_storage()
  storage.tracked = storage.tracked or {}
  storage.queue = storage.queue or {}
  storage.queue_keys = storage.queue_keys or {}
  storage.queue_position = storage.queue_position or 1
  storage.queued = storage.queued or {}
  storage.bonuses = {}
  for _, force in pairs(game.forces) do
    storage.bonuses[force.index] = bonuses(force)
  end
  storage.reach = max_reach()
  -- Prototypes, settings or the mod itself may have changed: rebuild every tooltip (or remove them).
  enqueue_all(nil)
end

local function new_measurement(entity, tick)
  if entity.type ~= "inserter" then return nil end
  local held = entity.held_stack
  return {start = tick, previous = held.valid_for_read and held.count or 0, events = {}}
end

--- Counts items leaving the hand. Called every tick for hovered inserters only.
local function sample(measurement, entity, tick)
  local held = entity.held_stack
  local count = held.valid_for_read and held.count or 0
  if count < measurement.previous then
    local events = measurement.events
    events[#events + 1] = {tick, measurement.previous - count}
    while events[1][1] <= tick - MEASURE_WINDOW do
      table.remove(events, 1)
    end
  end
  measurement.previous = count
end

local function measured_rate(measurement, tick, cycle)
  if not measurement then return nil end
  local window = math.min(tick - measurement.start, MEASURE_WINDOW)
  if window < math.max(MIN_MEASURE, 2 * (cycle or 0)) then
    return {}
  end
  local moved = 0
  for _, event in ipairs(measurement.events) do
    if event[1] > tick - window then moved = moved + event[2] end
  end
  return {rate = moved / window * 60, seconds = window / 60}
end

--- Writes the tooltip of one inserter. Returns the analysis, nil if it failed.
local function write_tooltip(entity, measurement)
  local ok, result = pcall(calc.analyze, entity)
  if not ok then
    log("Inserter throughput: failed to analyze " .. entity.name .. ": " .. tostring(result))
    display.clear(entity)
    return nil
  end
  display.apply(entity, display.fields(result, measurement))
  return result
end

--- Background update of an inserter nobody hovers: the tooltip without the measured line.
local function update_idle(entity)
  if prepare_ahead() then
    write_tooltip(entity, nil)
  else
    display.clear(entity)
  end
end

local function process_queue()
  local queue, keys = storage.queue, storage.queue_keys
  local first = storage.queue_position
  local last = math.min(#queue, first + (prepare_ahead() and UPDATES_PER_TICK or CLEARS_PER_TICK) - 1)
  for index = first, last do
    local entity, key = queue[index], keys[index]
    storage.queued[key] = nil
    -- Hovered inserters are kept up to date by the hover loop.
    if entity.valid and not storage.tracked[key] then
      update_idle(entity)
    end
  end
  if last >= #queue then
    storage.queue, storage.queue_keys, storage.queue_position = {}, {}, 1
    if storage.announce_cleanup and not prepare_ahead() then
      storage.announce_cleanup = nil
      game.print({"inserter-hover-throughput.cleanup-done"})
    end
  else
    storage.queue_position = last + 1
  end
end

local function show_label(player)
  return player.mod_settings["inserter-hover-throughput-show-label"].value
end

local function update_labels(entry, result)
  for player_index in pairs(entry.players) do
    local player = game.get_player(player_index)
    local label = entry.labels[player_index]
    if player and show_label(player) and result then
      local text = display.label(result)
      if label and label.valid then
        label.text = text
      else
        entry.labels[player_index] = rendering.draw_text{
          text = text,
          surface = entry.entity.surface,
          target = {entity = entry.entity, offset = {0, -0.6}},
          color = {1, 1, 1},
          players = {player},
          alignment = "center",
          vertical_alignment = "bottom",
          scale = 1.2,
          use_rich_text = true,
        }
      end
    elseif label then
      if label.valid then label.destroy() end
      entry.labels[player_index] = nil
    end
  end
end

local function refresh(entry, tick)
  local result = write_tooltip(entry.entity, measured_rate(entry.measurement, tick, entry.cycle))
  if result then entry.cycle = result.cycle end
  update_labels(entry, result)
end

local function drop_entry(key, entry)
  for _, label in pairs(entry.labels) do
    if label.valid then label.destroy() end
  end
  storage.tracked[key] = nil
  if entry.entity.valid then update_idle(entry.entity) end
end

local function track(player, entity, tick)
  local key = entity.unit_number
  if not key then return end
  local entry = storage.tracked[key]
  if not entry then
    entry = {entity = entity, players = {}, labels = {}, measurement = new_measurement(entity, tick)}
    storage.tracked[key] = entry
  end
  entry.players[player.index] = true
  refresh(entry, tick)
end

local function untrack(player_index, key)
  local entry = storage.tracked[key]
  if not entry then return end
  entry.players[player_index] = nil
  local label = entry.labels[player_index]
  if label then
    if label.valid then label.destroy() end
    entry.labels[player_index] = nil
  end
  if not next(entry.players) then
    drop_entry(key, entry)
  end
end

local function untrack_player(player_index)
  for key, entry in pairs(storage.tracked) do
    if entry.players[player_index] then untrack(player_index, key) end
  end
end

local function refresh_tracked(tick)
  for _, entry in pairs(storage.tracked) do
    if entry.entity.valid then refresh(entry, tick) end
  end
end

script.on_init(init_storage)
script.on_configuration_changed(init_storage)

script.on_event(defines.events.on_selected_entity_changed, function(event)
  local player = game.get_player(event.player_index)
  if not player then return end
  untrack_player(event.player_index)
  local selected = player.selected
  if calc.is_inserter(selected) then
    track(player, selected, event.tick)
  end
end)

script.on_event(defines.events.on_tick, function(event)
  local tick = event.tick
  local tracked = storage.tracked
  if next(tracked) then
    for key, entry in pairs(tracked) do
      local entity = entry.entity
      if not entity.valid then
        drop_entry(key, entry)
      else
        if entry.measurement then sample(entry.measurement, entity, tick) end
        if (tick + key) % REFRESH_INTERVAL == 0 then refresh(entry, tick) end
      end
    end
  end
  if storage.queue_position <= #storage.queue then
    process_queue()
  end
end)

--- Something was built, removed, rotated or flipped: update it if it is an inserter, else the
--- inserters around it, because their pickup or drop target may have changed.
local function on_entity_changed(entity)
  if not (entity and entity.valid) or not prepare_ahead() then return end
  if calc.is_inserter(entity) then
    enqueue(entity)
  else
    enqueue_near(entity)
  end
end

script.on_event({
  defines.events.on_built_entity,
  defines.events.on_robot_built_entity,
  defines.events.on_space_platform_built_entity,
  defines.events.script_raised_built,
  defines.events.script_raised_revive,
  defines.events.on_player_mined_entity,
  defines.events.on_robot_mined_entity,
  defines.events.on_space_platform_mined_entity,
  defines.events.on_entity_died,
  defines.events.script_raised_destroy,
  defines.events.on_player_rotated_entity,
  defines.events.on_player_flipped_entity,
}, function(event)
  on_entity_changed(event.entity)
end)

script.on_event(defines.events.on_entity_cloned, function(event)
  on_entity_changed(event.destination)
end)

script.on_event(defines.events.on_entity_settings_pasted, function(event)
  if calc.is_inserter(event.destination) and prepare_ahead() then enqueue(event.destination) end
end)

-- The inserter GUI can change the manual stack size limit.
script.on_event(defines.events.on_gui_closed, function(event)
  if calc.is_inserter(event.entity) and prepare_ahead() then enqueue(event.entity) end
end)

--- Research changed a force: rebuild its tooltips only when a bonus that matters changed.
local function on_force_changed(force)
  local current = bonuses(force)
  local previous = storage.bonuses[force.index]
  storage.bonuses[force.index] = current
  if previous and previous[1] == current[1] and previous[2] == current[2] and previous[3] == current[3] then
    return
  end
  if prepare_ahead() then enqueue_all(force) end
  refresh_tracked(game.tick)
end

script.on_event({defines.events.on_research_finished, defines.events.on_research_reversed}, function(event)
  on_force_changed(event.research.force)
end)

script.on_event({defines.events.on_technology_effects_reset, defines.events.on_force_reset}, function(event)
  on_force_changed(event.force)
end)

script.on_event(defines.events.on_forces_merged, function()
  for _, force in pairs(game.forces) do
    storage.bonuses[force.index] = bonuses(force)
  end
  enqueue_all(nil)
end)

script.on_event({defines.events.on_player_left_game, defines.events.on_pre_player_removed}, function(event)
  untrack_player(event.player_index)
end)

script.on_event(defines.events.on_runtime_mod_setting_changed, function(event)
  local setting = event.setting
  if not setting:find("^inserter%-hover%-throughput%-") then return end
  if setting == "inserter-hover-throughput-prepare-ahead" or setting == "inserter-hover-throughput-show-details" then
    -- Write (or remove) the tooltip of every inserter.
    storage.announce_cleanup = not prepare_ahead()
    enqueue_all(nil)
  end
  refresh_tracked(event.tick)
end)

remote.add_interface("inserter-hover-throughput", {
  --- Returns the throughput analysis of an inserter (or inserter ghost) as a table, nil otherwise.
  analyze = function(entity)
    if not calc.is_inserter(entity) then return nil end
    return calc.analyze(entity)
  end,
})
