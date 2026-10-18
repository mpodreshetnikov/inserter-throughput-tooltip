import sys; sys.path.insert(0, sys.argv[1])
from lua import emit
cases=[
 dict(id="show|1|stack-inserter|legendary", ins="stack-inserter", q="legendary", ovr=0, force=[2,11,3], src="chest", dst="belt", dstbelt="turbo-transport-belt"),
 dict(id="show|2|bulk-inserter|rare", ins="bulk-inserter", q="rare", ovr=0, force=[2,11,3], src="belt", srcbelt="turbo-transport-belt", src_stack=1, dst="chest"),
 dict(id="show|3|fast-inserter|normal", ins="fast-inserter", q="normal", ovr=0, force=[0,0,0], src="chest", dst="chest"),
 dict(id="show|4|long-handed-inserter|epic", ins="long-handed-inserter", q="epic", ovr=0, force=[1,4,1], src="chest", dst="belt", dstbelt="express-transport-belt", ghost=True),
 dict(id="show|5|stack-inserter|normal", ins="stack-inserter", q="normal", ovr=8, force=[2,11,3], src="chest", dst="chest"),
 dict(id="show|6|bulk-inserter|normal", ins="bulk-inserter", q="normal", ovr=0, force=[2,11,3], src="chest", dst="chest", item="locomotive", filter="locomotive"),
 dict(id="show|7|inserter|uncommon", ins="inserter", q="uncommon", ovr=0, force=[2,11,3], src="belt", srcbelt="transport-belt", src_stack=1, dst="belt", dstbelt="fast-transport-belt"),
]
print(emit(cases, warm=600, measure=3600))
