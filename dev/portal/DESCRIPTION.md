# Inserter Throughput Tooltip

Hover any inserter, or a ghost you are about to build, and its tooltip tells you how many items per second
it can move at most, right where it stands.

## What you see

* **Max throughput**: `80/s (4800/min), chest/machine → belt`. The best case for this inserter in its current setup.
  Values that involve taking items from a belt are marked with `≈`. A note appears when a belt is the bottleneck.
* **Upper limit**: `120/s (chest → chest, full hand)`. What the same inserter could do between two chests.
* **Hand stack size**: `16 (5 base + 11 research), belt stacks of 4`. Where the hand size comes from.
* **Cycle**: `12 ticks = 0.2 s (swing 2 × 4 + drop 4)`. Where the time goes.
* **Measured** (optional): items the inserter really moved while you hovered it.

## What is taken into account

* Any inserter, including modded ones and custom pickup/drop vectors
* Quality (faster rotation and extension)
* Hand size research and the inserter's built-in stack bonus
* Manual and circuit-set stack size limits
* Item stack size when the moved item is known (in hand or a single whitelist filter)
* Speed of the input and output belt, output lane capacity
* Stack inserter belt stacking, including belt capacity research
* Stacked items on the input belt and pickup lane filters

## Accuracy

Every rule was measured in Factorio 2.1.22 by building inserters in a headless server and counting moved items
tick by tick, then checked on more than 2,000 random setups:

| Setup | Mean error |
|---|---|
| chest/machine → chest/machine | 0.2% |
| chest/machine → belt | 0.2% |
| belt → chest/machine (≈) | ~2% |
| belt → belt (≈) | ~2% |

Taking items from a belt is the only approximate part: the hand chases items along the belt, so a small model
trained on about 8,000 engine measurements corrects the physics estimate.

Did you know? In 2.1 a fast inserter needs 24 ticks per chest-to-chest cycle, 2.5 items/s per hand item,
not 26 ticks and 2.31/s as in older tables.

## Assumptions

The value is the best case: a fully compressed input belt, a free output lane, chests and machines that always have
items and room. Machine ingredient limits, low power and other inserters taking from the same belt are not
included; turn on "Also show measured throughput" to see the real rate.

## Settings

* Map: **Prepare tooltips for all inserters in advance** (on by default)
* Map: **Show hand stack size, cycle time and upper limit** (on by default)
* Map: **Also show measured throughput** (off by default)
* Per player: **Also show throughput above the hovered inserter**, a text label only you can see (off by default)

## Compatibility

* Factorio 2.1.22 or newer. Space Age and Quality are optional.
* Works with modded inserters, ghosts, multiplayer.
* Tooltips are prepared in the background, 10 inserters per tick and only when something changes
  (an inserter or a belt next to it is built, removed or rotated, or hand size research completes),
  so they show instantly, also in multiplayer.

## Removing the mod from a save

The tooltip lines are stored in the save. Before removing the mod, turn off **Prepare tooltips for all inserters
in advance** in Settings → Mod settings → Map, wait for the chat message saying the lines were removed, then save.
If you forget, nothing breaks: the leftover lines show empty text instead of "Unknown key" errors.

## For modders

```lua
local result = remote.call("inserter-hover-throughput", "analyze", entity) -- inserter or inserter ghost
-- result.rate, result.max_rate (items/s), result.cycle (ticks), result.items_per_swing, result.limiter
```

Source code and the measurement harness: https://github.com/mpodreshetnikov/inserter-throughput-tooltip

---

# Пропускная способность манипуляторов

Наведите курсор на манипулятор (или его призрак), и в подсказке появится, сколько предметов в секунду он может
переносить максимум в своей текущей установке.

**Что показывается:** максимальная пропускная способность (с пометкой, если упирается в конвейер), предел для
переноса «сундук → сундук», размер пачки с разбивкой (база, исследования, ограничения), цикл в тиках с разбивкой.
По желанию: реально измеренная скорость и надпись над манипулятором.

**Что учитывается:** любые манипуляторы, в том числе модовые; качество; исследования размера пачки; ограничение
стопки вручную или по сети; размер стопки предмета; скорость входного и выходного конвейера; укладка стопками у
пакетного манипулятора; стопки на входном конвейере; фильтр полос.

**Точность:** все правила измерены в Factorio 2.1.22 потиково и проверены на 2000+ случайных установках.
Сундуки и машины: ошибка 0,2%. Выгрузка на конвейер: 0,2%. Забор с конвейера: около 2%, помечен «≈».

**Допущения:** показывается лучший случай: входной конвейер полностью сжат, полоса выхода свободна, машины
всегда готовы. Реальную скорость покажет опция «Дополнительно показывать измеренную скорость».

**Совместимость:** Factorio 2.1.22+, Space Age и Quality не обязательны, мультиплеер, призраки, модовые манипуляторы.
Подсказки готовятся заранее в фоне (10 манипуляторов за тик, только при изменениях), поэтому видны сразу, в том числе в мультиплеере.

**Удаление мода из сохранения:** строки подсказок хранятся в сохранении. Перед удалением мода выключите
«Готовить подсказки для всех манипуляторов заранее» (Настройки → Настройки модов → Карта), дождитесь сообщения в чате
и сохраните игру. Если забыть, ничего не сломается: оставшиеся строки будут пустыми, без ошибок «Unknown key».
