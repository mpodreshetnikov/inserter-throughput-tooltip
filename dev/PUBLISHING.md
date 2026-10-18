# Публикация на Factorio Mod Portal

У Factorio нет Steam Workshop: все моды, в том числе для Steam-версии, ставятся с mods.factorio.com
(через сайт или через «Моды → Установить» в самой игре).

## Сборка

`./build.sh` в корне репозитория собирает `dist/inserter-hover-throughput_<version>.zip` (только файлы мода, без `dev/`).

## Перед загрузкой

1. В `info.json` поле `author` сейчас `mpodreshetnikov`. Если ваш логин на factorio.com другой, поправьте.
2. Имя мода `inserter-hover-throughput` (первое, `inserter-throughput-tooltip`, оказалось занято). Если портал
   снова скажет, что имя занято, поменяйте `name` в `info.json` и ключ в `[mod-name]`/`[mod-description]` обоих
   `locale.cfg`; `build.sh` сам назовёт папку и zip `<name>_<version>`.
3. Желательно сделать 1–2 настоящих скриншота подсказки в игре для галереи (макеты в `dev/mockups/` — не скриншоты).

## Через сайт (проще всего)

1. Войдите на https://mods.factorio.com и нажмите «Upload new mod» (https://mods.factorio.com/create).
2. Загрузите `dist/inserter-hover-throughput_1.0.0.zip` (после `./build.sh`).
3. На странице мода заполните:
   * Category: **Utilities**; Tags: **Logistics** (по желанию **Circuit network**).
   * License: MIT (как в `LICENSE`).
   * Description: вставьте `dev/portal/DESCRIPTION.md` (английская и русская части).
   * Иконка мода берётся из `thumbnail.png` в zip; крупные варианты для страницы — `dev/portal/icon-*-512.png`.
   * Gallery: скриншоты из игры.

## Через API (для будущих обновлений)

1. На https://factorio.com/profile создайте API key с правом «ModPortal: Upload Mods».
2. Новая версия существующего мода:

   ```sh
   KEY=...   # не храните ключ в репозитории
   URL=$(curl -s -H "Authorization: Bearer $KEY" -F mod=inserter-hover-throughput \
         https://mods.factorio.com/api/v2/mods/releases/init_upload | jq -r .upload_url)
   curl -s -F file=@dist/inserter-hover-throughput_1.0.1.zip "$URL"
   ```

   Первую публикацию нового мода через API делают через `.../api/v2/mods/init_publish` так же; проще первый раз
   загрузить через сайт.

Перед каждым релизом поднимайте `version` в `info.json`, добавляйте секцию в `changelog.txt` и называйте zip
`inserter-hover-throughput_<version>.zip`.
