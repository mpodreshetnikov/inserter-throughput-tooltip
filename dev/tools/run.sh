#!/bin/bash
# usage: run.sh <cases.lua> <ticks> <outfile>
S=/tmp/claude-0/-home-user/c1c47c97-0f0f-5391-8da1-71e629f8ed70/scratchpad
F=$S/fx/opt/factorio/bin/x64/factorio
cp "$1" $S/fwrite/mods/itt-harness/cases.lua
rm -f $S/fwrite/saves/itt.zip
$F --create $S/fwrite/saves/itt.zip > $S/create.log 2>&1 || { tail -30 $S/create.log; exit 1; }
$F --benchmark $S/fwrite/saves/itt.zip --benchmark-ticks "$2" --benchmark-runs 1 > "$3" 2>&1
grep -c RESULT "$3"; grep -i -E "error|DONE" "$3" | head -5
