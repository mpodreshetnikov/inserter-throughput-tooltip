"""Exercises control.lua hover logic with mocked Factorio API (no players exist in a headless server)."""
import os
import sys
from lupa import lua54 as lupa

MOD = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lua = lupa.LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
MOD_DIR = ...
''', MOD)
lua.globals().MOD_DIR = MOD
lua.execute(r'''
package.path = MOD_DIR .. "/?.lua;" .. package.path
handlers, nth = {}, {}
defines = {events = setmetatable({}, {__index = function(t, k) return k end})}
script = {
  on_init = function(f) handlers.init = f end,
  on_configuration_changed = function(f) handlers.config = f end,
  on_event = function(e, f) if type(e) == "table" then for _, x in pairs(e) do handlers[x] = f end else handlers[e] = f end end,
}
storage = {}
settings = {global = {
  ["inserter-hover-throughput-show-details"] = {value = true},
  ["inserter-hover-throughput-show-measured"] = {value = true},
}}
logs = {}
function log(s) logs[#logs + 1] = s end
remote = {add_interface = function() end}
renders = {}
rendering = {draw_text = function(p)
  local o = {valid = true, text = p.text, players = p.players}
  function o.destroy() o.valid = false end
  renders[#renders + 1] = o
  return o
end}
players = {}
game = {get_player = function(i) return players[i] end}
local function new_player(i)
  players[i] = {index = i, mod_settings = {["inserter-hover-throughput-show-label"] = {value = false}}}
  return players[i]
end
new_player(1); new_player(2)

local next_unit = 100
function make_entity(kind)
  next_unit = next_unit + 1
  local e = {valid = true, unit_number = next_unit, type = kind == "ghost" and "entity-ghost" or "inserter",
             ghost_type = "inserter", name = "fast-inserter", surface = {}, fields = {}, next_id = 1,
             held_stack = {valid_for_read = false, count = 0}}
  function e.set_tooltip_field(f)
    assert(f.name and f.value, "name/value required")
    local id = f.id or e.next_id
    if id >= e.next_id then e.next_id = id + 1 end
    e.fields[id] = f
    return id
  end
  function e.clear_tooltip_field(id) e.fields[id] = nil end
  function e.count_fields() local n = 0 for _ in pairs(e.fields) do n = n + 1 end return n end
  return e
end

-- calc is mocked: the real one is validated against the engine separately.
package.preload["scripts.calc"] = function()
  return {
    is_inserter = function(e) return e ~= nil and e.valid and (e.type == "inserter" or e.ghost_type == "inserter") end,
    analyze = function(e)
      if e.broken then error("boom") end
      return {ghost = e.type == "entity-ghost", rate = 7.5, max_rate = 15, approximate = true, pickup_kind = "belt",
              drop_kind = "entity", limiter = "swing", hand_max = 3, hand_base = 1, hand_research = 2, hand_current = 3,
              hand_limited = false, items_per_swing = 3, half_swing = 12, pickup_extra = 0.3, drop_extra = 0,
              cycle = 24.3}
    end,
  }
end
dofile(MOD_DIR .. "/control.lua")
handlers.init()

function hover(player_index, entity, tick)
  local p = players[player_index]
  local last = p.selected
  p.selected = entity
  handlers.on_selected_entity_changed({player_index = player_index, last_entity = last, tick = tick})
end
function run_ticks(from, to, f)
  for t = from, to do
    if f then f(t) end
    handlers.on_tick({tick = t})
  end
end
function tracked_count() local n = 0 for _ in pairs(storage.tracked) do n = n + 1 end return n end
''')
g = lua.globals()
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: check.failed = True
check.failed = False

A = lua.eval("make_entity('real')"); B = lua.eval("make_entity('real')"); G = lua.eval("make_entity('ghost')")
lua.eval("hover")(1, A, 10)
check(A.count_fields() == 5, "hover sets 4 fields + \"measuring...\" placeholder: %d" % A.count_fields())
# simulate an inserter dropping 3 items every 24 ticks
lua.execute('''
A_ = ...
''', A)
lua.execute(r'''
run_ticks(11, 700, function(t)
  local phase = t % 24
  A_.held_stack.valid_for_read = phase < 12
  A_.held_stack.count = phase < 12 and 3 or 0
end)
''')
fields = [lua.eval("function(e) local out = {} for id, f in pairs(e.fields) do out[#out+1] = f end return out end")(A)]
names = [str(f.name[1]) for f in fields[0].values()]
check("inserter-hover-throughput.measured" in names, "measured field appears after hovering for a while")
meas = [f for f in fields[0].values() if f.name[1] == "inserter-hover-throughput.measured"][0]
check(meas.value[1] == "inserter-hover-throughput.measured-value" and abs(float(meas.value[2]) - 7.5) < 0.2,
      "measured rate ~7.5/s, got %s" % meas.value[2])
lua.eval("hover")(2, A, 701)
lua.eval("hover")(1, B, 702)
check(A.count_fields() > 0, "A keeps fields while player 2 still hovers it")
check(B.count_fields() >= 4, "B has fields for player 1")
lua.eval("hover")(2, None, 703)
check(A.count_fields() == 0, "A cleared when nobody hovers it")
check(lua.eval("tracked_count()") == 1, "only B tracked")
# label on/off
lua.execute('players[1].mod_settings["inserter-hover-throughput-show-label"].value = true')
g.handlers.on_runtime_mod_setting_changed(lua.eval('{setting = "inserter-hover-throughput-show-label", tick = 704}'))
check(len(list(g.renders.values())) == 1 and g.renders[1].valid, "label drawn for player 1")
lua.execute('players[1].mod_settings["inserter-hover-throughput-show-label"].value = false')
g.handlers.on_runtime_mod_setting_changed(lua.eval('{setting = "inserter-hover-throughput-show-label", tick = 705}'))
check(not g.renders[1].valid, "label removed when setting disabled")
# entity destroyed while hovered
B.valid = False
lua.eval("run_ticks")(706, 710)
check(lua.eval("tracked_count()") == 0, "destroyed entity dropped from tracking without errors")
# ghost: no measurement, still fields
lua.eval("hover")(1, G, 720)
lua.eval("run_ticks")(721, 900)
gnames = [str(f.name[1]) for f in lua.eval("function(e) local out = {} for id, f in pairs(e.fields) do out[#out+1] = f end return out end")(G).values()]
check("inserter-hover-throughput.measured" not in gnames and len(gnames) == 4, "ghost shows estimate without measured line: %s" % gnames)
# analysis failure is logged, not fatal
C = lua.eval("make_entity('real')"); C.broken = True
lua.eval("hover")(1, C, 901)
check(C.count_fields() == 0 and len(list(g.logs.values())) == 1, "analysis error logged and no fields left")
# player leaves
lua.eval("hover")(2, G, 902)
g.handlers.on_player_left_game(lua.eval('{player_index = 2, tick = 903}'))
check(G.count_fields() == 0 or lua.eval("players[1].selected") == G, "player leaving handled")
lua.eval("hover")(1, None, 904)
check(G.count_fields() == 0 and lua.eval("tracked_count()") == 0, "everything cleared at the end")
sys.exit(1 if check.failed else 0)
