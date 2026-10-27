# Порядок работы по лабораторной (Git + Spec Kit + Antigravity)

Приёмка проверяет **историю git**: спецификации раньше реализации, отдельные ветки, слияние через Pull Request.

## 0. Репозиторий
```bash
git init orbita && cd orbita            # новый репозиторий, не Лаб 1/2
# создайте пустой репозиторий на GitHub и подключите:
git remote add origin git@github.com:<you>/orbita.git
git checkout -b main
git commit --allow-empty -m "chore: init repository"
git push -u origin main
```

## 1. Ветка `spec/speckit-artifacts` (VS Code + Copilot)
```bash
git checkout -b spec/speckit-artifacts
```
1. Установите Spec Kit по https://github.com/github/spec-kit и выполните `specify init` с интеграцией **copilot** (точный флаг смотрите в README Spec Kit).
2. В чате Copilot пройдите команды **по актуальной документации** (сейчас это `/speckit.constitution` → `specify` → `plan` → `tasks` → `analyze`; имена могли смениться).
3. Тексты для этих шагов: `docs/SPEC_PROMPTS.md`.
4. Коммитьте **после каждой команды**:
```bash
git add .specify .github specs && git commit -m "spec: constitution (принципы и ограничения)"
git commit -am "spec: feature specification (конвертер + NEO трекер)"
git commit -am "spec: technical plan (Flask + Bootstrap)"
git commit -am "spec: tasks breakdown"
git commit -am "spec: analyze, правки по замечаниям согласованности"
git push -u origin spec/speckit-artifacts
gh pr create --base main --title "Спецификации Spec Kit" --body "Конституция, спецификация, план, задачи, analyze"
```
Смержите PR **на GitHub** (не прямым push).

## 2. Ветка `feat/implementation` (Antigravity)
```bash
git checkout main && git pull && git checkout -b feat/implementation
```
Откройте репозиторий в Antigravity 2.0, дайте агенту `specs/.../tasks.md`. Записывайте в черновик отчёта: какая модель на каком этапе, что сделано верно, где пришлось править руками. Коммиты небольшие: `feat: парсер XML НБМ`, `feat: файловый кэш`, `feat: UI конвертера`, `feat: вкладка NASA`. Затем `gh pr create`, merge через PR.

> Готовая реализация из этого проекта (папки `app/`, `tests/`) может служить **эталоном** для сравнения с тем, что собрал агент. Сдавать её как «собрано агентом» нельзя: пункты 3-5 отчёта должны описывать реальную работу.

## 3. Ветка `test/unit-tests`
```bash
git checkout main && git pull && git checkout -b test/unit-tests
```
Тесты бэкенда и фронтенда, `python run_tests.py` зелёный, команда в README. Коммиты: `test: парсер BNM`, `test: конвертация в обе стороны`, `test: пустой ответ и офлайн`, `test: валидация`. PR → merge.

## 4. Ветка `docs/report`
`REPORT.md`, финальный README. PR → merge. Включите CI (`.github/workflows/ci.yml`) и приложите зелёный прогон.
