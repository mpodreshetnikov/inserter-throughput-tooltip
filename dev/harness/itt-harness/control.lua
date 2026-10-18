local cfg = require("cases")
local display = require("__inserter-hover-throughput__/scripts/display")
local cases = cfg.cases
local CELL = 24
local WARM = cfg.warm or 600
local MEASURE = cfg.measure or 3600
local COLS = 20

local dirs = {
  [defines.direction.north] = {0, -1}, [defines.direction.east] = {1, 0},
  [defines.direction.south] = {0, 1}, [defines.direction.west] = {-1, 0},
}
local function vec_to_dir(x, y)
  if math.abs(x) > math.abs(y) then
    return x > 0 and defines.direction.east or defines.direction.west
  end
  return y > 0 and defines.direction.south or defines.direction.north
end

local function get_force(fc)
  local name = "t_" .. fc[1] .. "_" .. fc[2] .. "_" .. fc[3]
  local f = game.forces[name] or game.create_force(name)
  f.inserter_stack_size_bonus = fc[1]
  f.bulk_inserter_capacity_bonus = fc[2]
  f.belt_stack_size_bonus = fc[3]
  return f
end

local function tile_center(p)
  return {x = math.floor(p.x) + 0.5, y = math.floor(p.y) + 0.5}
end

local function build_belt(surface, force, belt, p, axis, run_len)
  local d = {-axis[2], axis[1]}
  local dir = vec_to_dir(d[1], d[2])
  local tc = tile_center(p)
  local ents = {}
  for k = -run_len, run_len do
    local e = surface.create_entity{name = belt, position = {tc.x + k * d[1], tc.y + k * d[2]}, direction = dir, force = force}
    ents[#ents + 1] = e
  end
  return ents
end

local function build(c, idx)
  local surface = game.surfaces.itt
  local force = get_force(c.force or {0, 0, 0})
  local col = (idx - 1) % COLS
  local row = math.floor((idx - 1) / COLS)
  local cx, cy = col * CELL + 0.5, row * CELL + 0.5
  local ins
  if c.ghost then
    ins = surface.create_entity{name = "entity-ghost", inner_name = c.ins, position = {cx, cy}, direction = c.dir or defines.direction.north, force = force, quality = c.q or "normal"}
  else
    ins = surface.create_entity{name = c.ins, position = {cx, cy}, direction = c.dir or defines.direction.north, force = force, quality = c.q or "normal"}
  end
  assert(ins, "failed to build " .. c.ins)
  if c.ovr and c.ovr > 0 then ins.inserter_stack_size_override = c.ovr end
  if c.pick then ins.pickup_position = {cx + c.pick[1], cy + c.pick[2]} end
  if c.drop then ins.drop_position = {cx + c.drop[1], cy + c.drop[2]} end
  if c.lanes == "left" then ins.pickup_from_right_lane = false end
  if c.filter then ins.use_filters = true; ins.inserter_filter_mode = "whitelist"; ins.set_filter(1, {name = c.filter}) end
  local fuel = not c.ghost and ins.get_fuel_inventory()
  if fuel then fuel.insert{name = "coal", count = 50} end
  local pp, dp = ins.pickup_position, ins.drop_position
  local axis_x, axis_y = dp.x - cx, dp.y - cy
  local axis = (math.abs(axis_x) > math.abs(axis_y)) and {axis_x > 0 and 1 or -1, 0} or {0, axis_y > 0 and 1 or -1}
  local st = {c = c, ins = ins, prev = 0, moved = 0, drops = {}, item = c.item or "iron-plate"}
  if c.src == "chest" then
    local ch = surface.create_entity{name = "infinity-chest", position = tile_center(pp), force = force}
    ch.set_infinity_container_filter(1, {name = st.item, count = 100, mode = "exactly"})
    st.src_chest = ch
  elseif c.src == "belt" then
    st.src_belt = build_belt(surface, force, c.srcbelt, pp, axis, 6)
    st.src_stack = c.src_stack or 1
  elseif c.src == "furnace" then
    -- unused
  end
  if c.dst == "chest" then
    local ch = surface.create_entity{name = "infinity-chest", position = tile_center(dp), force = force}
    ch.remove_unfiltered_items = true
    st.dst_chest = ch
  elseif c.dst == "belt" then
    st.dst_belt = build_belt(surface, force, c.dstbelt, dp, axis, 6)
  end
  return st
end

local function setup()
  local surface = game.create_surface("itt")
  surface.generate_with_lab_tiles = true
  surface.always_day = true
  local rows = math.ceil(#cases / COLS)
  for x = -1, math.ceil(COLS * CELL / 32) + 1 do
    for y = -1, math.ceil(rows * CELL / 32) + 1 do
      surface.request_to_generate_chunks({x * 32 + 16, y * 32 + 16}, 0)
    end
  end
  surface.force_generate_chunk_requests()
  for _, e in pairs(surface.find_entities()) do if e.valid and e.type ~= "character" then e.destroy() end end
  surface.create_global_electric_network()
  local eei = surface.create_entity{name = "electric-energy-interface", position = {-20, -20}, force = "player"}
  eei.power_production = 1e12
  eei.electric_buffer_size = 1e13
  storage.st = {}
  for i, c in ipairs(cases) do
    storage.st[i] = build(c, i)
  end
  storage.t0 = game.tick
end

local function feed(st)
  if st.src_belt then
    local first = st.src_belt[1]
    for lane = 1, 2 do
      local line = first.get_transport_line(lane)
      if line.can_insert_at_back() then line.insert_at_back({name = st.item, count = st.src_stack}, st.src_stack) end
    end
    local last = st.src_belt[#st.src_belt]
    last.get_transport_line(1).clear(); last.get_transport_line(2).clear()
  end
  if st.dst_belt then
    local last = st.dst_belt[#st.dst_belt]
    last.get_transport_line(1).clear(); last.get_transport_line(2).clear()
  end
end

script.on_event(defines.events.on_tick, function(e)
  if not storage.st then setup() return end
  local rel = e.tick - storage.t0
  local measuring = rel > WARM and rel <= WARM + MEASURE
  for _, st in pairs(storage.st) do
    feed(st)
    if st.c.ghost then goto continue end
    local hs = st.ins.held_stack
    local c = hs.valid_for_read and hs.count or 0
    if measuring then
      if c < st.prev then
        st.moved = st.moved + (st.prev - c)
        if c == 0 then st.drops[#st.drops + 1] = rel end
      end
    end
    st.prev = c
    ::continue::
  end
  if rel == WARM + MEASURE then
    for i, st in pairs(storage.st) do
      local deltas = {}
      for k = 2, #st.drops do
        local d = st.drops[k] - st.drops[k - 1]
        deltas[d] = (deltas[d] or 0) + 1
      end
      local dl = {}
      for d, n in pairs(deltas) do dl[#dl + 1] = d .. "x" .. n end
      table.sort(dl)
      local ins = st.ins
      local pred = remote.call("inserter-hover-throughput", "analyze", ins)
      local fields = display.fields(pred, {rate = st.moved / MEASURE * 60, seconds = MEASURE / 60})
      local ids = display.apply(ins, {}, fields)
      local nfields = #ins.get_tooltip_fields()
      if i <= 40 or st.c.ghost or st.c.filter or st.c.lanes then print("FIELDS " .. st.c.id .. " " .. helpers.table_to_json(ins.get_tooltip_fields())) end
      local ghost_rate
      print("RESULT " .. helpers.table_to_json({
        pred = pred.rate, pmax = pred.max_rate, pcycle = pred.cycle, plim = pred.limiter, papprox = pred.approximate or false,
        case = st.c, phalf = pred.half_swing, pextra = pred.pickup_extra, dextra = pred.drop_extra, pstack = pred.pickup_belt_stack,
        pk = pred.pickup_kind, dk = pred.drop_kind, pitems = pred.items_per_swing, nfields = nfields, ghost = ghost_rate,
        id = st.c.id, rate = st.moved / MEASURE * 60, moved = st.moved, cycles = #st.drops,
        deltas = table.concat(dl, ","), tpc = not st.c.ghost and ins.inserter_target_pickup_count or -1,
        rot = ins.prototype.get_inserter_rotation_speed(ins.quality), ext = ins.prototype.get_inserter_extension_speed(ins.quality),
        status = not st.c.ghost and ins.status or -1,
      }))
    end
    print("DONE")
  end
end)
