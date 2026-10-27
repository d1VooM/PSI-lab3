# Орбита: конвертер валют НБМ + трекер астероидов NASA

Веб-приложение на Python (Flask) с интерфейсом на Bootstrap 5.
Две вкладки: **конвертер валют** (источник: XML Национального банка Молдовы) и **трекер околоземных астероидов** (NASA NeoWs).

## Запуск
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                                       # http://127.0.0.1:5000
```
Для NASA используется `DEMO_KEY` (лимит ~30 запросов/час). Свой ключ с https://api.nasa.gov: `export NASA_API_KEY=...`

## Тесты (одна команда)
```bash
python run_tests.py
```
Запускает pytest (бэкенд: разбор ответов, расчёт в обе стороны, пустой/битый ответ, валидация, кэш, API) и `node --test` (фронтенд-логика: валидация, кнопка, шкала расстояний, экранирование). Нужен Node.js 18+; без него фронтенд-тесты пропускаются с сообщением.

## Как выполнены требования
| Требование | Где |
|---|---|
| Нет сети: не падает, берёт кэш с датой | `services/rates.py::_from_cache`, `services/neo.py::_fallback`, 503 только если кэша нет |
| Выходные/праздники | `services/rates.py` идёт назад до 7 дней; NASA: пустой день → последний кэш |
| Некорректный ввод | `app/validation.py` (бэк) и `static/js/logic.js` (фронт), правила совпадают |
| Одинаковые валюты | `convert()` возвращает сумму, курс 1:1 |
| Кэш переживает перезапуск | `data/cache.json` (атомарная запись), тест `test_offline_uses_cache_that_survives_restart` |
| Дата курса и источник | карточка «Источник / Дата курса», для NASA ещё метка времени ответа |
| Кнопка неактивна до заполнения | `canConvert()` в `logic.js` |

## Структура (подробнее про SOLID: `docs/ARCHITECTURE.md`)
```
app/ports.py        абстракции: KeyValueStore, RatesProvider, AsteroidProvider
app/providers/      bnm.py, nasa.py (сеть + разбор)
app/services/       rates.py, neo.py (сценарии: откат по датам, кэш)
app/converter.py    чистый расчёт; messages.py тексты; cache.py хранилища
app/__init__.py     composition root (внедрение зависимостей)
app/routes.py       Flask routes
app/static/     css/app.css, js/logic.js (чистая логика), js/app.js (DOM)
tests/          pytest (в т.ч. test_solid.py) + tests/frontend/*.test.js
specs/          сюда Spec Kit положит спецификации (см. docs/WORKFLOW.md)
docs/           WORKFLOW.md: порядок работы с Git, Spec Kit, Antigravity
REPORT.md       отчёт (заполняется по факту)
```
