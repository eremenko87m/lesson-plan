# LessonFlow FINAL — НАСТРОЙКА

## Что уже сделано
- Проект читает ТОЛЬКО лист `PLAN`.
- `GROUPS` и `MY BASE` никогда не попадают в `data/lessons.json`.
- Текущая публичная ссылка уже встроена в `scripts/sync_yandex.py` как резерв для теста.
- Картинки, вставленные через Ctrl+V поверх `IMAGE_1` / `IMAGE_2`, извлекаются из XLSX автоматически.
- Ссылки, картинки и аудио могут быть в одной строке активности одновременно.
- GitHub Actions запускает синхронизацию каждые 10 минут и вручную.
- Если таблица не изменилась, Action НЕ делает новый commit.

## 1. Загрузка в GitHub
Создай репозиторий, например `lesson-flow`, и загрузи СОДЕРЖИМОЕ этой папки в корень.

GitHub → Settings → Pages → Build and deployment → Deploy from a branch → `main` / `(root)`.

## 2. Первый тест — пока таблица публичная
Ничего в GitHub Secrets добавлять не нужно.

GitHub → Actions → `Sync LessonFlow from Yandex` → `Run workflow`.

Если лист называется `PLAN` и колонки совпадают со структурой, появится commit `Sync LessonFlow from PLAN`.

## 3. Финальный безопасный режим — приватная таблица
Когда тест пройдёт, переведи файл в приватный режим и используй Yandex Disk REST API.

### В GitHub нужны две настройки
**Secret**: `YANDEX_TOKEN` — OAuth-токен Яндекса с правом чтения Диска.

**Variable**: `YANDEX_FILE_PATH` — путь к XLSX на твоём Яндекс Диске, например:
`/LessonFlow/LessonFlow.xlsx`

После этого скрипт автоматически выбирает private API вместо публичной ссылки.

GitHub: Settings → Secrets and variables → Actions.
- Secrets → New repository secret → `YANDEX_TOKEN`
- Variables → New repository variable → `YANDEX_FILE_PATH`

После успешного private sync публичный доступ к таблице можно отключить.

## 4. Как заполнять PLAN
Точные колонки:
`DATE | TIME | STUDENT | LEVEL | TOPIC | FOCUS | LESSON_MIN | ACTIVITY | MIN | LINK | IMAGE_1 | IMAGE_2 | AUDIO | AUDIO_LABEL | NOTE`

Первая строка урока содержит дату/время/ученика/уровень/тему. Следующие строки этого урока могут оставлять первые 7 колонок пустыми.

### Картинка
Win+Shift+S → Ctrl+V в Яндекс Таблице → расположи ВЕРХНИЙ ЛЕВЫЙ УГОЛ картинки над нужной ячейкой `IMAGE_1` или `IMAGE_2`.

### Аудио
В `AUDIO` можно указать:
- публичную ссылку Яндекс Диска на mp3/m4a/ogg/wav;
- прямую https-ссылку на аудио;
- в private API режиме путь `disk:/LessonFlow/audio/track.mp3`.

В `AUDIO_LABEL` — например `Track 2.14`.

## 5. Важное про личные листы
Код находит лист строго по имени `PLAN` и не читает остальные листы. Но пока ВЕСЬ XLSX опубликован публичной ссылкой, человек с этой ссылкой потенциально может скачать всю книгу. Поэтому для реальных `GROUPS` и `MY BASE` переходи на private API.
