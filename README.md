# LessonFlow

A daily lesson dashboard for online teachers.

## Included
- 3×2 dashboard with up to 6 lesson cards
- previous / today / next day navigation
- lesson count, total teaching time and resource count
- automatic service detection from URLs
- Lesson Mode with direct resource buttons
- “Mark done” progress saved in the browser
- light / dark theme
- Yandex workbook → GitHub Actions → JSON automatic sync
- responsive layout

## GitHub Pages
Upload the whole project to a repository and enable:
**Settings → Pages → Build and deployment → Deploy from a branch → main / root**

## Yandex workbook
Use `LessonFlow_Yandex_Template.xlsx`.
It must contain sheets named `LESSONS` and `ACTIVITIES`.
Upload it to Yandex Disk / Yandex Documents, fill it in, and create a public view/download link.
For a public course demo, use aliases instead of sensitive personal data.

## GitHub variable
Go to:
**Settings → Secrets and variables → Actions → Variables → New repository variable**

Name: `YANDEX_PUBLIC_URL`
Value: your public Yandex Disk link.

## Test sync
**Actions → Sync Yandex workbook → Run workflow**

The workflow converts the workbook to `data/lessons.json` and commits it. It also runs every 10 minutes.

## LESSONS columns
`lesson_id`, `date`, `time`, `student`, `level`, `topic`, `focus`, `duration`, `accent`

Recommended date format: `YYYY-MM-DD`.
Accents: `violet`, `cyan`, `lime`, `orange`, `rose`, `blue`.

## ACTIVITIES columns
`lesson_id`, `order`, `activity`, `minutes`, `url`, `note`
