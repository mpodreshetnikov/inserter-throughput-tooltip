# Dev tools for Inserter Throughput Tooltip

Not part of the mod zip (`../build.sh` packs only the mod files into `dist/<name>_<version>.zip`).

* `PUBLISHING.md`: how to publish on the Factorio Mod Portal.
* `harness/itt-harness/`: test mod. In a headless Factorio 2.1.22 server it builds inserters with chests and
  belts (built from `cases.lua`), measures how many items they actually move per tick, and prints the mod's
  prediction next to each measurement.
* `tools/`: research scripts used during development. Paths inside them still point to the session
  scratch directory; adjust before reuse.
  * `gen_*.py`: case generators (chest/belt combinations, random modded inserter prototypes, validation sets).
  * `run.sh`: creates a save and runs `--benchmark` with the harness.
  * `cmp.py`: prediction vs. measurement report. `ml*.py`: model comparisons.
* `train_pickup_model.py`: trains the belt pickup correction model and writes `scripts/pickup_model.lua`.
  Usage: `python3 train_pickup_model.py <dir with out_ml*/out_vt*.txt> <dir with protos*.lua> <output.lua>`.
* `data/measurements.tar.gz`: raw harness output (training and validation runs).
* `test_control.py`: tests `control.lua` hover logic against a mocked API (needs `pip install lupa`).
* `mockup.py`, `shoot.js`, `mockups/`: UI mockups built from real tooltip fields
  (`npm install playwright @fontsource/titillium-web`, then `python3 mockup.py mockups && node shoot.js tooltip_ru tooltip_en settings`).

The headless server came from the `factoriotools/factorio:2.1.22` image (mirror.gcr.io); the API reference
came from the `typed-factorio@4.7.0` npm package (generated from the 2.1.22 docs).
