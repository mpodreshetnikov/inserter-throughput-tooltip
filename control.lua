local calc = require("scripts.calc")
local display = require("scripts.display")

local REFRESH_INTERVAL = 30   -- ticks between tooltip updates while hovered
local MEASURE_WINDOW = 600    -- ticks of history used for the measured rate
local MIN_MEASURE = 60        -- ticks to wait before showing a measured rate

-- storage.tracked[unit_number] = {
--   entity, players = {[player_index] = true}, ids = {tooltip field ids},
--   labels = {[player_index] = LuaRenderObject}, measurement = {start, previous, events}, cycle
-- }

local function init_storage()
  storage.tracked = storage.tracked or {}
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

local function show_label(player)
  return player.mod_settings["inserter-throughput-show-label"].value
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
  local entity = entry.entity
  local ok, result = pcall(calc.analyze, entity)
  if not ok then
    log("Inserter throughput: failed to analyze " .. entity.name .. ": " .. tostring(result))
    display.clear(entity, entry.ids)
    entry.ids = {}
    update_labels(entry, nil)
    return
  end
  entry.cycle = result.cycle
  local measurement = measured_rate(entry.measurement, tick, result.cycle)
  entry.ids = display.apply(entity, entry.ids, display.fields(result, measurement))
  update_labels(entry, result)
end

local function drop_entry(key, entry)
  display.clear(entry.entity, entry.ids)
  for _, label in pairs(entry.labels) do
    if label.valid then label.destroy() end
  end
  storage.tracked[key] = nil
end

local function track(player, entity, tick)
  local key = entity.unit_number
  if not key then return end
  local entry = storage.tracked[key]
  if not entry then
    entry = {entity = entity, players = {}, ids = {}, labels = {}, measurement = new_measurement(entity, tick)}
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
  local tracked = storage.tracked
  if not next(tracked) then return end
  local tick = event.tick
  for key, entry in pairs(tracked) do
    local entity = entry.entity
    if not entity.valid then
      drop_entry(key, entry)
    else
      if entry.measurement then sample(entry.measurement, entity, tick) end
      if (tick + key) % REFRESH_INTERVAL == 0 then refresh(entry, tick) end
    end
  end
end)

script.on_event({defines.events.on_player_left_game, defines.events.on_pre_player_removed}, function(event)
  untrack_player(event.player_index)
end)

local function refresh_all(tick)
  for _, entry in pairs(storage.tracked) do
    if entry.entity.valid then refresh(entry, tick) end
  end
end

script.on_event(defines.events.on_runtime_mod_setting_changed, function(event)
  if event.setting:find("^inserter%-throughput%-") then refresh_all(event.tick) end
end)

script.on_event(defines.events.on_research_finished, function(event)
  refresh_all(event.tick)
end)

remote.add_interface("inserter-throughput", {
  --- Returns the throughput analysis of an inserter (or inserter ghost) as a table, nil otherwise.
  analyze = function(entity)
    if not calc.is_inserter(entity) then return nil end
    return calc.analyze(entity)
  end,
})
