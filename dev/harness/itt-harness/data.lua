local c = table.deepcopy(data.raw.inserter["fast-inserter"])
c.name = "itt-custom"
c.allow_custom_vectors = true
data:extend{c}
local s = table.deepcopy(data.raw.inserter["inserter"])
s.name = "itt-custom-slow"
s.allow_custom_vectors = true
data:extend{s}
local function bulkify(base, name)
  local p = table.deepcopy(data.raw.inserter[base])
  p.name = name
  p.bulk = true
  p.stack_size_bonus = 0
  data:extend{p}
end
bulkify("inserter", "itt-bulk-slow")
bulkify("long-handed-inserter", "itt-bulk-long")
for _, file in pairs{"protos1", "protos2", "protos3", "protos4", "protos5", "protos6", "protos7", "protos8"} do
  local ok, list = pcall(require, file)
  if ok then
    for _, d in pairs(list) do
      local p = table.deepcopy(data.raw.inserter["fast-inserter"])
      p.name = d.name
      p.bulk = true
      p.rotation_speed = d.rot
      p.extension_speed = d.ext
      p.pickup_position = {0, -d.r}
      p.insert_position = {0, d.r + 0.2}
      data:extend{p}
    end
  end
end
