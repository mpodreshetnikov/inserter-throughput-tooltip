-- Turns a calc.analyze() result into tooltip fields and label text.

local display = {}

local ORDER_BASE = 150

local function format_number(x)
  if x ~= x or x == math.huge then return "∞" end
  local text
  if x >= 100 then
    text = string.format("%.0f", x)
  elseif x >= 10 then
    text = string.format("%.1f", x)
  else
    text = string.format("%.2f", x)
  end
  if text:find("%.") then
    text = text:gsub("0+$", "")
    text = text:gsub("%.$", "")
  end
  return text
end
display.format_number = format_number

local function format_ticks(x)
  local text = string.format("%.1f", x)
  return (text:gsub("%.0$", ""))
end

local function rate_string(rate, approximate)
  local value = {"inserter-hover-throughput.rate", format_number(rate), format_number(rate * 60)}
  if approximate then
    return {"inserter-hover-throughput.approximate", value}
  end
  return value
end

local function throughput_value(r)
  local value = {"", rate_string(r.rate, r.approximate), ", ", {"inserter-hover-throughput.route",
    {"inserter-hover-throughput.kind-" .. r.pickup_kind},
    {"inserter-hover-throughput.kind-" .. r.drop_kind}}}
  if r.limiter ~= "swing" then
    value[#value + 1] = ", "
    value[#value + 1] = {"inserter-hover-throughput.limiter-" .. r.limiter}
  end
  return value
end

local function hand_value(r)
  local value
  if r.hand_limited then
    value = {"inserter-hover-throughput.hand-limited", r.hand_current, r.hand_max}
  elseif r.hand_research > 0 then
    value = {"inserter-hover-throughput.hand-research", r.hand_max, r.hand_base, r.hand_research}
  else
    value = {"inserter-hover-throughput.hand-base", r.hand_max}
  end
  local result = {"", value}
  if r.hand_capped_by_item then
    result[#result + 1] = ", "
    result[#result + 1] = {"inserter-hover-throughput.hand-item", r.item.name, r.item_stack_size}
  end
  if r.drop_belt_stack and r.drop_belt_stack > 1 then
    result[#result + 1] = ", "
    result[#result + 1] = {"inserter-hover-throughput.belt-stack", r.drop_belt_stack}
  end
  if r.items_per_swing ~= math.min(r.hand_current, r.item_stack_size or math.huge) then
    result[#result + 1] = ", "
    result[#result + 1] = {"inserter-hover-throughput.per-swing", r.items_per_swing}
  end
  return result
end

local function cycle_value(r)
  local breakdown = {"", {"inserter-hover-throughput.cycle-swing", r.half_swing}}
  if math.abs(r.pickup_extra) >= 0.05 then
    -- Negative when the hand meets items coming towards it on the belt.
    breakdown[#breakdown + 1] = r.pickup_extra > 0 and " + " or " − "
    breakdown[#breakdown + 1] = {"inserter-hover-throughput.cycle-pickup", format_ticks(math.abs(r.pickup_extra))}
  end
  if r.drop_extra > 0 then
    breakdown[#breakdown + 1] = " + "
    breakdown[#breakdown + 1] = {"inserter-hover-throughput.cycle-drop", format_ticks(r.drop_extra)}
  end
  return {"", {"inserter-hover-throughput.cycle-value", format_ticks(r.cycle), format_number(r.cycle / 60)}, " (", breakdown, ")"}
end

local function measured_value(measurement)
  if not measurement then return nil end
  if not measurement.rate then
    return {"inserter-hover-throughput.measuring"}
  end
  return {"inserter-hover-throughput.measured-value", format_number(measurement.rate), format_number(measurement.seconds)}
end

--- List of {name, value} pairs to show, in order.
function display.fields(r, measurement)
  local show_details = settings.global["inserter-hover-throughput-show-details"].value
  local show_measured = settings.global["inserter-hover-throughput-show-measured"].value
  local fields = {}
  fields[#fields + 1] = {{"inserter-hover-throughput.throughput"}, throughput_value(r)}
  if show_details then
    if math.abs(r.max_rate - r.rate) > 0.005 * r.max_rate then
      fields[#fields + 1] = {{"inserter-hover-throughput.max-throughput"},
        {"", rate_string(r.max_rate, false), " (", {"inserter-hover-throughput.max-hint"}, ")"}}
    end
    fields[#fields + 1] = {{"inserter-hover-throughput.hand"}, hand_value(r)}
    fields[#fields + 1] = {{"inserter-hover-throughput.cycle"}, cycle_value(r)}
  end
  if show_measured and not r.ghost then
    local value = measured_value(measurement)
    if value then
      fields[#fields + 1] = {{"inserter-hover-throughput.measured"}, value}
    end
  end
  return fields
end

local FIELD_PREFIX = "inserter-hover-throughput."

--- Ids of the tooltip fields this mod wrote into the entity, in id order.
local function own_field_ids(entity)
  local ids = {}
  for _, field in pairs(entity.get_tooltip_fields()) do
    local name = field.name
    if type(name) == "table" and type(name[1]) == "string" and name[1]:sub(1, #FIELD_PREFIX) == FIELD_PREFIX then
      ids[#ids + 1] = field.id
    end
  end
  table.sort(ids)
  return ids
end

--- Writes the fields into the entity tooltip, reusing the lines this mod wrote before.
function display.apply(entity, fields)
  local ids = own_field_ids(entity)
  for index, field in ipairs(fields) do
    entity.set_tooltip_field{
      id = ids[index],
      name = field[1],
      value = field[2],
      order = ORDER_BASE + index,
    }
  end
  for index = #fields + 1, #ids do
    entity.clear_tooltip_field(ids[index])
  end
end

--- Removes every line this mod wrote into the entity tooltip.
function display.clear(entity)
  if not entity.valid then return end
  for _, id in ipairs(own_field_ids(entity)) do
    entity.clear_tooltip_field(id)
  end
end

--- One-line text for the optional label drawn above the inserter.
function display.label(r)
  return {"", "⇄ ", rate_string(r.rate, r.approximate)}
end

return display
