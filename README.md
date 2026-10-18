# Inserter Throughput Tooltip

Factorio 2.1 (Space Age optional). Hover any inserter, or an inserter ghost, and its tooltip shows how many
items per second it can move at most in its current setup.

## What the tooltip shows

| Line | Example | Meaning |
|---|---|---|
| Max throughput | `≈23.7/s (1420/min), belt → chest/machine` | Best case for this inserter where it stands. `≈` marks values that involve taking items from a belt. A note is added when a belt is the bottleneck. |
| Upper limit | `51.4/s (3086/min) (chest → chest, full hand)` | The same inserter moving chest to chest with a full hand. Hidden when equal to the first line. |
| Hand stack size | `16 (5 base + 11 research), belt stacks of 4` | Hand size with its sources, circuit or manual limits, item stack size caps, stack inserter belt stacking. |
| Cycle | `30.4 ticks = 0.51 s (swing 2 × 7 + pickup 16.4)` | Where the time goes. |
| Measured (opt-in) | `25.8/s over 10 s` | Items the inserter really moved while you hovered it. |

What is taken into account: inserter prototype (any mod), quality, hand size research (inserter and bulk
capacity bonuses), the prototype's own stack bonus, manual and circuit stack size limits, item stack size
(when the moved item is known from the hand or a single whitelist filter), custom pickup/drop vectors,
belt speed at both ends, stack inserter belt stacking (with belt capacity research) and "grab less to match
belt stack", stacked items on the input belt, lane pickup filters.

Assumptions for the "max" value: the input belt is fully compressed, the output belt lane is free, chests
and machines always have items / room. Machine ingredient limits and low power are not modelled; enable the
measured line to see the real rate.

## Settings

* Map: **Show hand stack size, cycle time and upper limit** (on by default).
* Map: **Also show measured throughput** (off by default).
* Per player: **Also show throughput above the hovered inserter**: a text label only you can see.

## How it is calculated

All rules were measured on Factorio 2.1.22 by building inserters in a headless server and counting
items tick by tick:

* A half swing takes `max(ceil(angle / rotation_speed) − 1, ceil(|r_drop − r_pickup| / extension_speed) − 1)`
  ticks (angle in revolutions). A fast inserter moves chest to chest in 24 ticks, i.e. 2.5 items/s per hand item.
* Taking from / putting into chests and machines adds no time.
* Dropping `k` stacks on a belt adds `max(k − 1, floor((k − 2) · 0.25 / belt_speed))` ticks; a lane takes at
  most `belt_speed / 0.25` stacks per tick.
* Taking `k` stacks from a compressed belt: physics estimate `2 · half_swing + (k − 1) · max(1, 0.2 / extension_speed)`
  corrected by a small gradient boosted tree model (150 trees) trained on ~8000 engine measurements of
  random and vanilla inserters, because the hand chases items along the belt.

Accuracy against the engine (2,300+ random setups not used for training):

| Setup | Mean error | Max error |
|---|---|---|
| chest/machine → chest/machine | 0.2% | 1.1% |
| chest → belt | 0.2% | 1.6% |
| belt → chest (≈) | 1.9% | 10–18% (rare) |
| belt → belt (≈) | 2.0% | 8–14% (rare) |

Errors up to ~1.5% are the measurement window itself (a whole number of cycles).

## Remote interface

```lua
local result = remote.call("inserter-throughput", "analyze", entity) -- entity: inserter or inserter ghost
-- result.rate, result.max_rate (items/s), result.cycle (ticks), result.items_per_swing, result.limiter, ...
```

---

# Пропускная способность манипуляторов

Наведите курсор на любой манипулятор (или его призрак), и в подсказке появится, сколько предметов в секунду
он может переносить максимум в текущей установке. Учитываются качество, исследования размера пачки,
ограничения стопки (вручную или по сети), размер стопки предмета, скорости конвейеров с обеих сторон,
укладка стопками у пакетного манипулятора, стопки на входном конвейере, фильтр полос, нестандартные векторы
модовых манипуляторов. Значения с конвейера помечены «≈»: средняя ошибка около 2%, остальное совпадает с игрой.

Настройки: «Показывать размер пачки, цикл и предел» (карта, вкл.), «Дополнительно показывать измеренную
скорость» (карта, выкл.), «Дублировать скорость надписью над манипулятором» (для игрока, выкл.).

---

## Development

* `./build.sh` builds `dist/inserter-throughput-tooltip_<version>.zip` for the Mod Portal (mod files only).
* `dev/` holds the headless test harness, the measurements, the model training script and tests; see `dev/README.md`.
