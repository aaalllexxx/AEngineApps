# AEngineApps v2.0 (OOP Framework)

> AEngineApps — это легковесный, чисто объектно-ориентированный фреймворк для создания webview (десктопных) и web-приложений на Python.
Построен поверх Flask и pywebview. Отличается полным отказом от декораторов в пользу строгой архитектуры классов и понятного API.

---

## 🚀 Быстрый старт (Quick Start)

### Структура проекта
```text
project/
    static/              # картинки, css, js
    templates/           # html шаблоны
    screens/             # файлы с экранами (логикой)
    main.py              # точка входа
    config.json          # конфигурация
```

### 1. `config.json`
```json
{
    "debug": true,
    "view": "web",
    "screen_path": "screens",
    "routers": "auto"
}
```

### 2. `main.py`
```python
from AEngineApps.app import App

app = App("MyApp")
app.load_config("config.json")

if __name__ == "__main__":
    app.run()
```

### 3. `screens/home.py`
```python
from AEngineApps.screen import Screen

class HomeScreen(Screen):
    route = "/"
    methods = ["GET", "POST"]
    
    def run(self):
        if self.request.method == "POST":
            return self.json({"status": "success"})
        return self.render("index.html", title="Главная")
```

---

## 📘 Документация: `App`

Основой класс приложения. Все настройки и запуски происходят через него.

### Инициализация
```python
app = App(app_name="AEngineApp", debug=False)
```

### Методы маршрутизации
| Метод | Описание | Пример |
|---|---|---|
| `add_screen(path, ScreenClass)` | Привязывает класс-экран к URL пути. | `app.add_screen("/", Home)` |
| `add_screens(rules_dict)` | Регистрация нескольких экранов сразу. | `app.add_screens({"/": Home, "/api": Api})` |
| `add_router(path, view_func)` | Привязывает обычную функцию (legacy). | `app.add_router("/old", my_func)` |
| `add_routers(rules_dict)` | Массовая регистрация функций. | `app.add_routers({"/old": my_func})` |

### Middleware и Lifecycle
| Метод | Описание | Пример |
|---|---|---|
| `before_request(func)` | Функция вызывается **до** каждого HTTP запроса. Если вернёт ответ, запрос прерывается. | `app.before_request(check_auth)` |
| `after_request(func)` | Вызывается **после** каждого запроса. Должна вернуть изменённый response. | `app.after_request(add_cors)` |

### События жизненного цикла (Lifecycle)
```python
def check_auth():
    if not is_authorized():
        app.redirect("/login")

# Вызывается ДО каждого запроса
app.before_request(check_auth)

# Функция при старте приложения
app.on_start(db.connect)
```
| Метод | Описание | Пример |
|---|---|---|
| `on_start(func)` | Функция выполнится один раз перед стартом сервера. | `app.on_start(db.connect)` |
| `on_stop(func)` | Функция выполнится при завершении работы приложения. | `app.on_stop(db.close)` |

### Настройки безопасности и ошибок
| Метод | Описание | Пример |
|---|---|---|
| `enable_cors(orig, meth, head)`| Включает CORS. По умолчанию разрешает всё. | `app.enable_cors(origins="*")` |
| `set_error_page(code, ScreenCls)`| Заменяет стандартную страницу ошибки 404/500 на ваш класс Screen. | `app.set_error_page(404, NotFoundScreen)`|

### Управление приложением
| Метод | Описание | Пример |
|---|---|---|
| `load_config(path, encoding)` | Читает JSON-конфигурацию. Настраивает авто-роутинг и папки static/templates. | `app.load_config("config.json")` |
| `run()` | Запускает приложение (в webview или web режиме в зависимости от конфига). | `app.run()` |
| `close()` | Принудительно закрывает окно webview (если оно открыто). | `app.close()` |

---

## 📗 Документация: `Screen`

Базовый класс для каждого контроллера/страницы. В одном `.py` файле может быть **сколько угодно экранов** — авто-роутинг найдет их все.

### Атрибуты класса
| Атрибут | Описание | Пример |
|---|---|---|
| `route` | Обязательный. Указывает `URL` для авто-роутинга. | `route = "/login"` |
| `methods` | Опциональный. Указывает разрешенные HTTP методы. | `methods = ["GET", "POST"]` |

### Основной метод `run`
Вы **обязаны** переопределить метод `run(*args, **kwargs)` во всех наследниках `Screen`.
```python
class PostScreen(Screen):
    route = "/post/<int:id>"
    
    def run(self, id):
        product = db.get(id)
        return self.render("post.html", product=product)
```

### Встроенные помощники (Хелперы)
| Формат Вызова | Описание |
|---|---|
| `self.render("file.html", **ctx)` | Возвращает скомпилированный HTML-шаблон (аналог `render_template`). |
| `self.redirect("/url")` | Перенаправляет пользователя на другой адрес (аналог `redirect`). |
| `self.json(dict_data, status=200)`| Возвращает JSON-ответ (аналог `jsonify`). |
| `self.request` | Свойство. Даёт прямой доступ к `flask.request` (form, args, json, headers). |
| `self.app` | Свойство. Даёт доступ к экземпляру текущего `App` (например, для доступа к `self.app.config`). |
| `self.session` | Свойство. Обертка над `flask.session` (требует SECRET_KEY). |
| `self.client_ip` | Свойство. Безопасное получение IP пользователя (с поддержкой прокси). |
| `self.abort(404)` | Мгновенное прерывание запроса с ошибкой. |
| `self.flash("msg", "type")` | Показ одноразовых сообщений (Flash messages). |
| `self.save_file("avatar", "path")`| Сохранение загруженного файла (возвращает `True/False`). |

---

## � REST API: класс `API` (api.py)

Специальная обертка над `Screen` для максимально быстрого и элегантного создания REST API.
Забудьте про `if request.method == "POST"` и ручной `jsonify`.

### Особенности `API` класса:
1. Автоматически перенаправляет запросы в методы по названию HTTP (`get`, `post`, `put`, `delete`).
2. Любой возвращаемый `dict` или `list` **автоматически превращается в JSON**.
3. Можно возвращать кортеж `(dict, status_code)`.

### Хелперы:
| Формат Вызова | Описание |
|---|---|
| `self.require_keys(["name"])` | Проверяет JSON-запрос. Возвращает `(True, "")` или `(False, 'name')`. |
| `self.get_arg("limit", int, 10)`| Безопасное получение и автокаст Query (?limit=5) параметра. |

```python
# screens/api_screens.py
from AEngineApps.api import API

class UsersAPI(API):
    route = "/api/users"
    methods = ["GET", "POST"]
    
    def get(self):
        # /api/users?limit=5
        limit = self.get_arg("limit", type_func=int, default=10)
        return {"users": ["Alex", "John", "Sarah"][:limit]}
        
    def post(self):
        ok, missing = self.require_keys(["name", "age"])
        if not ok:
             return {"error": f"Missing key: {missing}"}, 400
            
        # Возвращаем dict + HTTP статус (201 Created)
        return {"status": "created"}, 201
```

---

## 🧩 Мультисервисная Архитектура: класс `Service` (service.py)

Легковесный способ разбить монолит на модули (микросервисы).
`Service` — это обертка над Flask Blueprints, полностью интегрированная с `Screen` и `API`.

### Изолированные сервисы
У каждого сервиса может быть свой префикс URL, свои экраны и **свои независимые middleware**!

```python
# services/auth.py
from AEngineApps.service import Service
from AEngineApps.api import API

auth = Service("auth", prefix="/api/auth")

class LoginAPI(API):
    methods = ["POST"]
    def post(self):
        return {"status": "success", "token": "123"}

auth.add_screen("/login", LoginAPI)

# Middleware ТОЛЬКО для экранов Auth-сервиса
@auth.before_request
def check_attempts():
    pass
```

### Подключение сервиса в `main.py`
```python
from AEngineApps.app import App
from services.auth import auth

app = App()
app.register_service(auth)
# Теперь LoginAPI доступен по адресу /api/auth/login
```

---

## 📙 Документация: `GlobalStorage`

Безопасное глобальное хранилище-одиночка (Singleton). Идеально подходит для обмена данными между модулями, избегая циклических импортов (`Circular Import`).

```python
from AEngineApps.global_storage import GlobalStorage
gs = GlobalStorage()
```

| Метод / Синтаксис | Описание | Пример |
|---|---|---|
| `gs.key = value` | Запись данных через атрибут. | `gs.user_id = 42` |
| `gs.key` | Получение данных через атрибут (выдаст `AttributeError` если нет). | `print(gs.user_id)` |
| `gs.get(key, default)`| Безопасное получение с дефолтным значением. | `user = gs.get("user_id", None)` |
| `gs.has(key)` | Проверка существования ключа (возвращает bool). | `if gs.has("user_id"):` |
| `gs.delete(key)` | Удаление ключа. | `gs.delete("user_id")` |
| `gs.clear()` | Полная очистка хранилища. | `gs.clear()` |
| `gs.all()` | Получение всех данных в виде словаря (`dict`). | `config = gs.all()` |

---

## 📕 Документация: `JsonDict`

Удобная обертка над JSON-файлом. Позволяет работать с данными как с объектами Python. Изменения автоматически или ручным вызовом сохраняются на диск.

```python
from AEngineApps.json_dict import JsonDict
data = JsonDict("data.json")
```

| Метод / Синтаксис | Описание | Пример |
|---|---|---|
| `data.key = value` | Обновляет значение и ставит отметку об изменении. | `data.port = 8080` |
| `data.key` | Чтение значения (выдаст `AttributeError` если нет). | `print(data.port)` |
| `data.has(key)` | Возвращает `True`, если ключ есть в JSON. | `if data.has("port"):` |
| `"key" in data` | Аналог `has()`, поддержка оператора `in`. | `if "port" in data:` |
| `data.get(key)` | Безопасное получение (вернёт `None`, если нет). | `port = data.get("port")` |
| `data.update(dict)` | Массовое обновление ключей из словаря. | `data.update({"a": 1, "b": 2})` |
| `data.delete_item(key)`| Удаление ключа из JSON. | `data.delete_item("port")` |
| `data.keys()` | Возвращает список всех ключей. | `for k in data.keys():` |
| `data.values()` | Возвращает список всех значений. | `for v in data.values():` |
| `data.items()` | Возвращает пары `(ключ, значение)`. | `for k, v in data.items():` |
| `data.save()` | Принудительная запись на диск (автовызывается при `load`). | `data.save()` |
| `data.load()` | Принудительная перезагрузка файла с диска (обновляет кэш). | `data.load()` |
| `data.push(dict)` | Заменяет **ВЕСЬ** файл переданным словарём. | `data.push({"new": "data"})` |

*Особенности `JsonDict` v2.0:*
- Не падает при отсутствии файла (`FileNotFoundError` обрабатывается, создается пустой словарь).
- Флаг `ensure_ascii=False` гарантирует корректное отображение русских букв в файле (не в виде `\u0430...`).
- Ленивое сохранение: данные пишутся на диск только если были реально изменены (флаг `_dirty`).
