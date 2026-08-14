# Как получить Yandex OAuth для приватной таблицы

1. В Yandex OAuth создай приложение типа **Для доступа к API или отладки**.
2. Выбери минимально необходимое право: **чтение Яндекс Диска** (`cloud_api:disk.read`, если это имя отображается в интерфейсе).
3. Получи отладочный/ручной OAuth-токен для своего аккаунта.
4. Никогда не вставляй токен в `index.html`, JavaScript или публичный код.
5. В GitHub сохрани токен только как `YANDEX_TOKEN` в **Settings → Secrets and variables → Actions → Secrets**.
6. Путь к таблице сохрани как Variable `YANDEX_FILE_PATH`, например `/LessonFlow/LessonFlow.xlsx`.
7. Запусти Actions → Sync LessonFlow from Yandex → Run workflow.
8. Когда синхронизация прошла, отключи публичную ссылку на XLSX.

Проект передаёт токен только в HTTP-заголовке `Authorization: OAuth ...` внутри GitHub runner. На GitHub Pages токен не отправляется.
