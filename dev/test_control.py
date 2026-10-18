"""Exercises control.lua with a mocked Factorio API (no players exist in a headless server).

Run: pip install lupa && python3 dev/test_control.py
"""
import os
import sys

from lupa import lua54 as lupa

MOD = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lua = lupa.LuaRuntime(unpack_returned_tuples=True)
lua.globals().MOD_DIR = MOD
lua.execute(r'''
package.path = MOD_DIR .. "/?.lua;" .. package.path
handlers = {}
defines = {events = setmetatable({}, {__index = function(_, k) return k end})}
script = {
  on_init = function(f) handlers.init = f end,
  on_configuration_changed = function(f) handlers.config = f end,
  on_event = function(e, f)
    if type(e) == "table" then for _, x in pairs(e) do handlers[x] = f end else handlers[e] = f end
  end,
}
storage = {}
settings = {global = {
  ["inserter-hover-throughput-prepare-ahead"] = {value = true},
  ["inserter-hover-throughput-show-details"] = {value = true},
  ["inserter-hover-throughput-show-measured"] = {value = true},
}}
logs, printed = {}, {}
function log(s) logs[#logs + 1] = s end
remote = {add_interface = function() end}
renders = {}
rendering = {draw_text = function(p)
  local o = {valid = true, text = p.text}
  function o.destroy() o.valid = false end
  renders[#renders + 1] = o
  return o
end}
prototypes = {get_entity_filtered = function()
  return {inserter = {inserter_pickup_position = {0, -1}, inserter_drop_position = {0, 1.2}},
          long = {inserter_pickup_position = {0, -2}, inserter_drop_position = {0, 2.2}}}
end}

-- World: entities on one surface, found by position.
entities = {}
surface = {}
function surface.find_entities_filtered(f)
  local out = {}
  for _, e in pairs(entities) do
    if e.valid then
      local kind_ok = (f.type and e.type == f.type) or (f.ghost_type and e.type == "entity-ghost" and e.ghost_type == f.ghost_type)
      local force_ok = f.force == nil or f.force == e.force
      local area_ok = true
      if f.area then
        area_ok = e.position.x >= f.area[1][1] and e.position.x <= f.area[2][1]
              and e.position.y >= f.area[1][2] and e.position.y <= f.area[2][2]
      end
      if kind_ok and force_ok and area_ok then out[#out + 1] = e end
    end
  end
  return out
end
force_a = {index = 1, inserter_stack_size_bonus = 0, bulk_inserter_capacity_bonus = 0, belt_stack_size_bonus = 0}
players = {}
game = {surfaces = {surface}, forces = {force_a}, tick = 0,
        get_player = function(i) return players[i] end,
        print = function(m) printed[#printed + 1] = m end}
for i = 1, 2 do players[i] = {index = i, mod_settings = {["inserter-hover-throughput-show-label"] = {value = false}}} end

local next_unit = 100
function make_entity(kind, x, y)
  next_unit = next_unit + 1
  local e = {valid = true, unit_number = next_unit, force = force_a, name = kind, surface = surface,
             position = {x = x, y = y}, fields = {}, next_id = 1, analyzed = 0,
             held_stack = {valid_for_read = false, count = 0}}
  if kind == "inserter" then e.type = "inserter"
  elseif kind == "ghost" then e.type = "entity-ghost"; e.ghost_type = "inserter"
  else e.type = kind end
  e.bounding_box = {left_top = {x = x - 0.4, y = y - 0.4}, right_bottom = {x = x + 0.4, y = y + 0.4}}
  function e.set_tooltip_field(f)
    assert(f.name and f.value, "name/value required")
    local id = f.id or e.next_id
    if id >= e.next_id then e.next_id = id + 1 end
    e.fields[id] = {id = id, name = f.name, value = f.value, order = f.order or 100}
    return id
  end
  function e.clear_tooltip_field(id) e.fields[id] = nil end
  function e.get_tooltip_fields()
    local out = {}
    for _, f in pairs(e.fields) do out[#out + 1] = f end
    table.sort(out, function(a, b) return a.id < b.id end)
    return out
  end
  entities[#entities + 1] = e
  return e
end
function names(e)
  local out = {}
  for _, f in ipairs(e.get_tooltip_fields()) do out[#out + 1] = type(f.name) == "table" and f.name[1] or f.name end
  return table.concat(out, ",")
end
function count(e) return #e.get_tooltip_fields() end

package.preload["scripts.calc"] = function()
  return {
    is_inserter = function(e)
      return e ~= nil and e.valid and (e.type == "inserter" or (e.type == "entity-ghost" and e.ghost_type == "inserter"))
    end,
    analyze = function(e)
      e.analyzed = e.analyzed + 1
      if e.broken then error("boom") end
      return {ghost = e.type == "entity-ghost", rate = 7.5, max_rate = 15, approximate = true, pickup_kind = "belt",
              drop_kind = "entity", limiter = "swing", hand_max = 3 + force_a.inserter_stack_size_bonus, hand_base = 1,
              hand_research = 2, hand_current = 3, hand_limited = false, items_per_swing = 3, half_swing = 12,
              pickup_extra = 0.3, drop_extra = 0, cycle = 24.3, dynamic = e.dynamic}
    end,
  }
end

-- Entities that exist before the mod is added.
A = make_entity("inserter", 0, 0)
B = make_entity("inserter", 10, 0)
G = make_entity("ghost", 20, 0)
other = make_entity("assembling-machine", 40, 40)
other.set_tooltip_field{name = "Other mod", value = "keep me"}

dofile(MOD_DIR .. "/control.lua")

function tick(n)
  for _ = 1, n do
    game.tick = game.tick + 1
    handlers.on_tick({tick = game.tick})
  end
end
function hover(player_index, entity)
  local p = players[player_index]
  p.selected = entity
  handlers.on_selected_entity_changed({player_index = player_index, tick = game.tick})
end
function tracked_count() local n = 0 for _ in pairs(storage.tracked) do n = n + 1 end return n end
function set_setting(name, value)
  settings.global[name].value = value
  handlers.on_runtime_mod_setting_changed({setting = name, tick = game.tick})
end
''')
g = lua.globals()
failed = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failed.append(msg)


g.handlers.init()
check(g.count(g.A) == 0, "nothing written synchronously in on_init (work is queued)")
g.tick(2)
check(g.count(g.A) == 4 and g.count(g.B) == 4 and g.count(g.G) == 4,
      "existing inserters and ghosts get their tooltip in the background without any hover")
check(g.count(g.other) == 1, "other entities and other mods' lines are untouched")

# Hover shows the measured line, unhover keeps the prepared tooltip.
g.hover(1, g.A)
check(g.count(g.A) == 5 and "measured" in g.names(g.A), "hover adds the measured line")
lua.execute(r'''
for _ = 1, 700 do
  local phase = (game.tick + 1) % 24
  A.held_stack.valid_for_read = phase < 12
  A.held_stack.count = phase < 12 and 3 or 0
  tick(1)
end
''')
measured = [f for f in g.A.get_tooltip_fields().values() if f.name[1] == "inserter-hover-throughput.measured"][0]
check(abs(float(measured.value[2]) - 7.5) < 0.2, "measured rate ~7.5/s, got %s" % measured.value[2])
g.hover(1, None)
check(g.count(g.A) == 4 and "measured" not in g.names(g.A), "unhover keeps the prepared tooltip, drops the measured line")
check(g.tracked_count() == 0, "nothing tracked after unhover")

# Building a belt next to B re-analyzes B (and not the far away ghost).
before_b, before_g = g.B.analyzed, g.G.analyzed
belt = lua.eval("make_entity('transport-belt', 10, 1)")
g.handlers.on_built_entity(lua.eval("function(e) return {entity = e} end")(belt))
g.tick(1)
check(g.B.analyzed == before_b + 1 and g.G.analyzed == before_g, "a new belt updates only the inserters in reach")

# A newly built inserter gets its tooltip.
C = lua.eval("make_entity('inserter', 30, 0)")
g.handlers.on_built_entity(lua.eval("function(e) return {entity = e} end")(C))
g.tick(1)
check(g.count(C) == 4, "newly built inserter gets a tooltip")

# Research: bonus change re-queues the force, unrelated research does not.
before = g.A.analyzed
g.handlers.on_research_finished(lua.eval("{research = {force = force_a}}"))
g.tick(2)
check(g.A.analyzed == before, "research that does not change bonuses does nothing")
lua.execute("force_a.inserter_stack_size_bonus = 1")
g.handlers.on_research_finished(lua.eval("{research = {force = force_a}}"))
g.tick(2)
check(g.A.analyzed == before + 1, "inserter capacity research rebuilds the tooltips")

# Inserters whose inputs change without events (empty belt, circuit hand size) are rechecked when idle.
g.A.dynamic = True
g.handlers.on_player_rotated_entity(lua.eval("function(e) return {entity = e} end")(g.A))
g.tick(1)
before_a, before_c = g.A.analyzed, C.analyzed
g.tick(600)
check(g.A.analyzed > before_a and C.analyzed == before_c, "dynamic inserters are rechecked periodically, static ones are not")
g.A.dynamic = False
g.tick(600)
after = g.A.analyzed
g.tick(600)
check(g.A.analyzed == after, "an inserter stops being rechecked once its inputs are known")

# Pasting a blueprint over an existing inserter updates it.
before = C.analyzed
g.handlers.on_blueprint_settings_pasted(lua.eval("function(e) return {entity = e} end")(C))
g.tick(1)
check(C.analyzed == before + 1, "blueprint settings paste re-analyzes the inserter")

# Turning preparing off while someone hovers: the announcement waits until the hovered inserter is cleared.
g.hover(2, g.A)
g.set_setting("inserter-hover-throughput-prepare-ahead", False)
g.tick(2)
check(len(list(g.printed.values())) == 0, "no cleanup announcement while an inserter is still hovered")
g.hover(2, None)
check(g.count(g.A) == 0 and len(list(g.printed.values())) == 1, "announcement comes after the hovered inserter is cleared")
g.set_setting("inserter-hover-throughput-prepare-ahead", True)
g.tick(2)
lua.execute("printed = {}")

# Turning preparing off removes every line and says so; turning it on brings them back.
g.set_setting("inserter-hover-throughput-prepare-ahead", False)
g.tick(2)
check(g.count(g.A) == 0 and g.count(g.B) == 0 and g.count(g.G) == 0 and g.count(C) == 0,
      "disabling 'prepare in advance' removes the lines from all inserters")
check(g.count(g.other) == 1, "other mods' lines survive the cleanup")
check(len(list(g.printed.values())) == 1, "cleanup completion is announced once")
g.hover(2, g.B)
check(g.count(g.B) == 5, "with preparing off, hover still shows the tooltip")
g.hover(2, None)
check(g.count(g.B) == 0, "with preparing off, unhover removes the lines")
belt2 = lua.eval("make_entity('transport-belt', 0, 1)")
g.handlers.on_built_entity(lua.eval("function(e) return {entity = e} end")(belt2))
g.tick(1)
check(g.count(g.A) == 0, "with preparing off, building does not write tooltips")
g.set_setting("inserter-hover-throughput-prepare-ahead", True)
g.tick(2)
check(g.count(g.A) == 4 and g.count(C) == 4, "re-enabling writes the tooltips again")

# Labels, destroyed entities, analysis errors, players leaving.
lua.execute('players[1].mod_settings["inserter-hover-throughput-show-label"].value = true')
g.hover(1, g.B)
check(len(list(g.renders.values())) == 1 and g.renders[1].valid, "label drawn for player 1")
g.hover(1, None)
check(not g.renders[1].valid, "label removed on unhover")
g.hover(1, g.B)
g.B.valid = False
g.tick(3)
check(g.tracked_count() == 0, "destroyed hovered entity is dropped without errors")
D = lua.eval("make_entity('inserter', 50, 0)")
D.broken = True
g.handlers.on_built_entity(lua.eval("function(e) return {entity = e} end")(D))
g.tick(1)
check(g.count(D) == 0 and len(list(g.logs.values())) == 1, "analysis error is logged, no lines left")
g.hover(2, C)
g.handlers.on_player_left_game(lua.eval("{player_index = 2}"))
check(g.tracked_count() == 0 and g.count(C) == 4, "player leaving stops tracking, prepared tooltip stays")

sys.exit(1 if failed else 0)
