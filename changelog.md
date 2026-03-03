# Changelog — AEngineApps v2.0

## [2.0.2] — 2026-03-03
### Новые классы и методы
- **Класс `Service` (`service.py`)** — легковесная мультисервисная архитектура (обертка над Blueprints) для разбиения монолита. Поддерживает свои экраны, свой префикс и свои изолированные middleware. Подключается вручную через `app.register_service()` или **автоматически через `config.json`** (`"services": "auto"`).
- **Класс `API` (`api.py`)** — обёртка над `Screen` для элегантного REST API (авто-роутинг по `get/post`, конвертация в JSON). 
  - Методы: `self.require_keys(keys)`, `self.get_arg("key", type, default)`
- Новые хелперы в **классе `Screen`**:
  - `self.session`, `self.client_ip` (проперти)
  - `self.abort(code)`, `self.flash(msg)`, `self.save_file("field", "path")`

### Документация
- Полностью переписан `readme.md` под новую версию v2.0 (добавлены инструкции по `add_screen`, `add_middleware`, обновлен Quick Start и описание `GlobalStorage`/`JsonDict`)

## [2.0.0] — 2026-03-03

### Архитектура
- Полный переход на ООП — удалены все декораторы из API
- Поддержка нескольких экранов в одном файле (авто-обнаружение через `inspect`)

### App — новые методы
- `add_screen(path, ScreenClass)` — регистрация экрана по маршруту
- `add_screens(dict)` — массовая регистрация
- `before_request(func)` — middleware до запроса (вместо add_middleware)
- `after_request(func)` — middleware после запроса (вместо add_after_middleware)
- `set_error_page(code, ScreenClass)` — страницы ошибок через Screen-классы
- `on_start(func)` / `on_stop(func)` — lifecycle хуки (без декораторов)
- `enable_cors()` — включение CORS одной строкой
- Автоконфигурация `static_folder` и `template_folder` из config.json
- Встроенные HTML-страницы 404/500 по умолчанию
- Type hints на все методы

### Screen — хелперы
- `self.render(template, **context)` — рендер шаблона
- `self.redirect(url)` — редирект
- `self.json(data, status)` — JSON-ответ
- `self.request` — доступ к текущему запросу
- `self.app` — ссылка на экземпляр App
- Атрибуты класса: `route`, `methods`

### GlobalStorage
- `get(key, default)` — безопасное получение
- `has(key)` — проверка наличия
- `delete(key)` — удаление ключа
- `clear()` — очистка
- `all()` — все данные как dict
- Безопасный `__getattr__` с `AttributeError` вместо `KeyError`

### JsonDict
- `has(key)`, `values()`, `items()`, `update(dict)`
- `save()` — принудительное сохранение
- `ensure_ascii=False` — корректное сохранение русского текста
- `__contains__` — оператор `in`
- Безопасный `load()` — не падает при `FileNotFoundError`

### Исправления
- Устранено затенение переменной `value` в `config.setter`
- Устранена неинициализированная переменная `prefix`
- Фильтрация non-.py файлов в авто-роутинге
