# Архитектура и SOLID

```
routes (Flask, HTTP) ─▶ services (сценарии) ─▶ ports (Protocol) ◀─ providers / cache (реализации)
                              │
                       converter, validation, messages (чистая логика)
create_app() = composition root: единственное место, где выбираются реализации
```

| Принцип | Где в коде | Чем доказано |
|---|---|---|
| **S** Single Responsibility | `converter.py` только расчёт; `providers/*` только сеть+разбор; `services/*` только сценарий; `messages.py` только тексты; `cache.py` только хранение; `validation.py` только ввод | у каждого модуля одна причина для изменений |
| **O** Open/Closed | новый источник курсов = новый класс с `fetch_rates()`, `RatesService` не правится; новые тексты/язык = наследник `Messages` | `test_new_provider_needs_no_service_change`, `test_messages_are_replaceable` |
| **L** Liskov | `JsonCache` и `MemoryCache` взаимозаменяемы; `EnglishMessages` подставляется вместо `Messages` | `test_store_contract` (один контракт на обе реализации) |
| **I** Interface Segregation | `app/ports.py`: `KeyValueStore` (2 метода), `RatesProvider`, `AsteroidProvider` раздельные; BNM-провайдер не обязан уметь астероиды | `test_ports_are_small_and_satisfied` |
| **D** Dependency Inversion | сервисы принимают порты в конструкторе; HTTP, часы (`today`) и хранилище внедряются; `create_app(rates_service=..., neo_service=...)` | `test_service_depends_on_abstractions_only`, `test_create_app_accepts_injected_services` |
