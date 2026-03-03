"""
AEngineApps — OOP-фреймворк для создания webview/web приложений.
Построен на Flask + pywebview. Без декораторов — чистый ООП.
"""

import os
import sys
import socket
import inspect
from typing import Callable, Any, Optional
from flask import Flask, make_response
from AEngineApps.json_dict import JsonDict
from AEngineApps.screen import Screen
from importlib import import_module
import webview


class App:
    """Основной класс приложения AEngine.
    
    Пример:
        app = App("MyApp")
        app.load_config("config.json")
        app.run()
    """

    def __init__(self, app_name: str = __name__, debug: bool = False):
        self.app_name: str = app_name
        self.project_root: str = os.path.dirname(os.path.dirname(__file__)) + os.sep
        self.flask: Flask = Flask(
            self.app_name,
            static_folder=os.path.join(self.project_root, "static"),
            template_folder=os.path.join(self.project_root, "templates")
        )
        self.flask.debug = debug
        self.flask.root_path = self.project_root
        self.__config: dict = {}
        self.window = None
        self._startup_hooks: list[Callable] = []
        self._shutdown_hooks: list[Callable] = []
        self._error_pages: dict[int, Any] = {}
    
    # ─── Роутинг ──────────────────────────────────────────────

    def add_screen(self, path: str, screen_cls: type, **options) -> None:
        """Добавляет экран по маршруту.
        
        Пример:
            app.add_screen("/", HomeScreen)
            app.add_screen("/profile", ProfileScreen, methods=["GET", "POST"])
        """
        instance = screen_cls()
        instance._app = self
        instance.__name__ = path.replace("/", "_") or "_root"
        
        # Берём methods из класса, если не переданы явно
        if "methods" not in options and hasattr(screen_cls, "methods"):
            options["methods"] = screen_cls.methods
        
        self.flask.add_url_rule(path, view_func=instance, **options)

    def add_screens(self, rules: dict[str, type]) -> None:
        """Добавляет несколько экранов из словаря {путь: ScreenClass}.
        
        Пример:
            app.add_screens({
                "/": HomeScreen,
                "/about": AboutScreen,
                "/api/data": DataScreen
            })
        """
        for route, screen_cls in rules.items():
            self.add_screen(route, screen_cls)

    def add_router(self, path: str, view_func: Callable, **options) -> None:
        """Добавляет маршрут с функцией (совместимость)."""
        self.flask.add_url_rule(path, view_func=view_func, **options)
        
    def add_routers(self, rules: dict[str, Callable]) -> None:
        """Добавляет несколько маршрутов из словаря (совместимость)."""
        for route, func in rules.items():
            self.add_router(route, func)

    # ─── Middleware ────────────────────────────────────────────

    def add_middleware(self, func: Callable) -> None:
        """Добавляет middleware, вызываемый ДО каждого запроса.
        
        Если middleware возвращает Response — запрос прерывается.
        
        Пример:
            def check_auth():
                if not session.get("user"):
                    return redirect("/login")
            
            app.add_middleware(check_auth)
        """
        self.flask.before_request(func)

    def add_after_middleware(self, func: Callable) -> None:
        """Добавляет middleware, вызываемый ПОСЛЕ каждого запроса.
        
        Middleware принимает response и должен вернуть response.
        
        Пример:
            def add_headers(response):
                response.headers["X-App"] = "AEngine"
                return response
            
            app.add_after_middleware(add_headers)
        """
        self.flask.after_request(func)

    # ─── CORS ─────────────────────────────────────────────────

    def enable_cors(self, origins: str = "*", methods: str = "GET,POST,PUT,DELETE,OPTIONS",
                    headers: str = "Content-Type,Authorization") -> None:
        """Включает CORS для API-режима.
        
        Пример:
            app.enable_cors()
            app.enable_cors(origins="https://mysite.com")
        """
        @self.flask.after_request
        def cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = origins
            response.headers["Access-Control-Allow-Methods"] = methods
            response.headers["Access-Control-Allow-Headers"] = headers
            return response

    # ─── Страницы ошибок ──────────────────────────────────────

    def set_error_page(self, code: int, screen_cls: type) -> None:
        """Устанавливает экран для страницы ошибки.
        
        Пример:
            class NotFoundPage(Screen):
                def run(self, error=None):
                    return self.render("404.html"), 404
            
            app.set_error_page(404, NotFoundPage)
        """
        instance = screen_cls()
        instance._app = self
        self.flask.register_error_handler(code, instance)

    def _register_default_error_handlers(self) -> None:
        """Стандартные страницы ошибок (если не заданы пользователем)."""
        @self.flask.errorhandler(404)
        def _default_404(e):
            return make_response(
                "<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                "<h1>404</h1><p>Страница не найдена</p>"
                "<a href='/'>На главную</a></body></html>", 404
            )

        @self.flask.errorhandler(500)
        def _default_500(e):
            return make_response(
                "<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                "<h1>500</h1><p>Внутренняя ошибка сервера</p></body></html>", 500
            )

    # ─── Lifecycle ────────────────────────────────────────────

    def on_start(self, func: Callable) -> None:
        """Регистрирует функцию, вызываемую при запуске.
        
        Пример:
            def connect_db():
                db.connect()
            
            app.on_start(connect_db)
        """
        self._startup_hooks.append(func)

    def on_stop(self, func: Callable) -> None:
        """Регистрирует функцию, вызываемую при завершении.
        
        Пример:
            def disconnect_db():
                db.close()
            
            app.on_stop(disconnect_db)
        """
        self._shutdown_hooks.append(func)

    def _run_hooks(self, hooks: list[Callable]) -> None:
        for hook in hooks:
            try:
                hook()
            except Exception as e:
                print(f"[App] Ошибка в хуке {hook.__name__}: {e}")

    # ─── Конфигурация ─────────────────────────────────────────

    def load_config(self, path: str, encoding: str = "utf-8") -> None:
        """Загрузка конфигурации из JSON файла."""
        if not os.path.exists(path):
            print(f"[App] Ошибка: файл конфигурации не найден: {path}")
            return
        try:
            self.config = JsonDict(path, encoding)
        except Exception as e:
            print(f"[App] Ошибка при загрузке конфигурации: {e}")
    
    @property
    def config(self) -> dict:
        return self.__config
    
    @config.setter
    def config(self, value):
        prefix = ""
        if isinstance(value, dict):
            # Настройка папок из конфига
            if value.get("static_folder"):
                self.flask.static_folder = os.path.join(self.project_root, value["static_folder"])
            if value.get("template_folder"):
                self.flask.template_folder = os.path.join(self.project_root, value["template_folder"])
            
            # Ручные роуты: {"route": "ClassName"}
            if value.get("routers") and value.get("routers") != "auto":
                if value.get("screen_path"):
                    prefix = value["screen_path"].replace("/", ".") + "."
                for route, func_name in value["routers"].items():
                    try:
                        cls = getattr(import_module(prefix + func_name), func_name)
                        self.add_screen(route, cls)
                    except (ImportError, AttributeError) as e:
                        print(f"[App] Ошибка загрузки экрана '{func_name}': {e}")

            # Авто-роутинг: сканирует ВСЕ Screen-классы во всех файлах
            if value.get("routers") == "auto":
                self._auto_discover_screens(value.get("screen_path", "screens"))

            if value.get("root_path"):
                self.flask.root_path = value["root_path"]
            for prop, val in value.items():       
                self.__config[prop] = val
        
        elif isinstance(value, JsonDict):
            self.config = value.dictionary

    def _auto_discover_screens(self, screen_path: str) -> None:
        """Автообнаружение ВСЕХ Screen-классов во всех файлах screen_path.
        
        Поддерживает несколько экранов в одном файле.
        Каждый экран должен наследоваться от Screen и иметь атрибут route.
        """
        screen_dir = os.path.join(self.project_root, screen_path)
        if not os.path.isdir(screen_dir):
            print(f"[App] Директория экранов не найдена: {screen_dir}")
            return
        
        prefix = screen_path.replace("/", ".").replace("\\", ".") + "."
        
        for filename in os.listdir(screen_dir):
            if filename.startswith("__") or not filename.endswith(".py"):
                continue
            
            mod_name = filename.replace(".py", "")
            try:
                module = import_module(prefix + mod_name)
            except ImportError as e:
                print(f"[App] Ошибка импорта '{mod_name}': {e}")
                continue
            
            # Ищем ВСЕ классы-наследники Screen в модуле
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if not issubclass(cls, Screen) or cls is Screen:
                    continue
                if not hasattr(cls, "route"):
                    continue
                
                try:
                    routes = cls.route if isinstance(cls.route, list) else [cls.route]
                    for route in routes:
                        self.add_screen(route, cls)
                except Exception as e:
                    print(f"[App] Ошибка регистрации экрана '{name}': {e}")
    
    # ─── Запуск ───────────────────────────────────────────────

    def run(self) -> None:
        """Запуск приложения."""
        host: Optional[str] = self.config.get("host")
        port: Optional[int] = self.config.get("port")
        if not host:
            print("[App] Ошибка: не указан host в конфигурации.")
            return
        if not port:
            print("[App] Ошибка: не указан port в конфигурации.")
            return
        
        # Дефолтные страницы ошибок (если пользователь не задал свои)
        self._register_default_error_handlers()
        
        self._run_hooks(self._startup_hooks)
        
        try:
            if self.config.get("view") != "web":
                try:
                    self.window = webview.create_window(self.app_name, self.flask)
                    webview.start(debug=self.config.get("debug") or False)
                except Exception as e:
                    print(f"[App] Ошибка webview: {e}")
                    print("[App] Попытка запуска в режиме web...")
                    self._run_web(host, port)
            else:
                self._run_web(host, port)
        finally:
            self._run_hooks(self._shutdown_hooks)
    
    def _run_web(self, host: str, port: int) -> None:
        """Запуск в web-режиме."""
        if host == "0.0.0.0":
            try:
                addrs = set()
                for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                    addrs.add(info[4][0])
                for addr in addrs:
                    print(f"Running '{self.app_name}' on http://{addr}:{port}")
            except socket.gaierror:
                print(f"Running '{self.app_name}' on http://0.0.0.0:{port}")
        else:
            print(f"Running '{self.app_name}' on http://{host}:{port}")
        try:
            self.flask.run(host, port, debug=self.config.get("debug") or False)
        except OSError as e:
            print(f"[App] Ошибка запуска сервера: {e}")
            print(f"[App] Возможно, порт {port} уже занят.")

    def close(self) -> None:
        """Закрывает окно webview."""
        if self.window:
            self.window.destroy()