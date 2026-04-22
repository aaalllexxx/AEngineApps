"""
AEngineApps - OOP framework for building webview/web apps.
Built on top of Flask + pywebview without decorator-heavy APIs.
"""

import inspect
import os
import socket
import sys
from collections.abc import Iterable
from importlib import import_module
from typing import Any, Callable, Optional

import webview
from flask import Flask, make_response

from AEngineApps.json_dict import JsonDict
from AEngineApps.screen import Screen


class App:
    """Main AEngine application class."""

    def __init__(self, app_name: str = __name__, debug: bool = False):
        self.app_name: str = app_name
        self.project_root: str = os.path.dirname(os.path.dirname(__file__)) + os.sep
        self.flask: Flask = Flask(
            self.app_name,
            static_folder=os.path.join(self.project_root, "static"),
            template_folder=os.path.join(self.project_root, "templates"),
        )
        self.flask.debug = debug
        self.flask.root_path = self.project_root
        self.__config: dict = {}
        self._startup_hooks: list[Callable] = []
        self._shutdown_hooks: list[Callable] = []
        self._error_pages: dict[int, Any] = {}
        self.window = None

        # Suppress duplicate logs in clustered worker processes.
        if os.environ.get("AENGINE_CLUSTER_PORT"):
            self._original_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            self._original_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

    def add_screen(self, path: str, screen_cls: type, **options) -> None:
        """Register a screen class under a route."""
        instance = screen_cls()
        instance._app = self
        instance.__name__ = path.replace("/", "_") or "_root"

        if "methods" not in options and hasattr(screen_cls, "methods"):
            options["methods"] = screen_cls.methods

        self.flask.add_url_rule(path, view_func=instance, **options)

    def add_screens(self, rules: dict[str, type]) -> None:
        for route, screen_cls in rules.items():
            self.add_screen(route, screen_cls)

    def add_router(self, path: str, view_func: Callable, **options) -> None:
        self.flask.add_url_rule(path, view_func=view_func, **options)

    def add_routers(self, rules: dict[str, Callable]) -> None:
        for route, func in rules.items():
            self.add_router(route, func)

    def register_service(self, service: Any) -> None:
        """Attach a Service instance to the app."""
        for screen in service._screens:
            screen._app = self

        self.flask.register_blueprint(service.blueprint)

    def before_request(self, func: Callable) -> None:
        self.flask.before_request(func)

    def after_request(self, func: Callable) -> None:
        self.flask.after_request(func)

    def set_error_page(self, code: int, screen_cls: type) -> None:
        instance = screen_cls()
        instance._app = self
        self.flask.register_error_handler(code, instance)

    def _register_default_error_handlers(self) -> None:
        @self.flask.errorhandler(404)
        def _default_404(e):
            return make_response(
                "<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                "<h1>404</h1><p>Страница не найдена</p>"
                "<a href='/'>На главную</a></body></html>",
                404,
            )

        @self.flask.errorhandler(500)
        def _default_500(e):
            return make_response(
                "<html><body style='font-family:sans-serif;text-align:center;padding:60px'>"
                "<h1>500</h1><p>Внутренняя ошибка сервера</p></body></html>",
                500,
            )

    def on_start(self, func: Callable) -> None:
        self._startup_hooks.append(func)

    def on_stop(self, func: Callable) -> None:
        self._shutdown_hooks.append(func)

    def _run_hooks(self, hooks: list[Callable]) -> None:
        for hook in hooks:
            try:
                hook()
            except Exception as e:
                print(f"[App] Ошибка в хуке {hook.__name__}: {e}")

    def load_config(self, path: str, encoding: str = "utf-8") -> None:
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
            if value.get("static_folder"):
                self.flask.static_folder = os.path.join(self.project_root, value["static_folder"])
            if value.get("template_folder"):
                self.flask.template_folder = os.path.join(self.project_root, value["template_folder"])

            if value.get("routers") and value.get("routers") != "auto":
                if value.get("screen_path"):
                    prefix = value["screen_path"].replace("/", ".").replace("\\", ".") + "."
                for route, func_name in value["routers"].items():
                    try:
                        cls = getattr(import_module(prefix + func_name), func_name)
                        self.add_screen(route, cls)
                    except (ImportError, AttributeError) as e:
                        print(f"[App] Ошибка загрузки экрана '{func_name}': {e}")

            if value.get("routers") == "auto":
                self._auto_discover_screens(value.get("screen_path", "screens"))

            if value.get("root_path"):
                self.flask.root_path = value["root_path"]

            services_path = value.get("services_path", "services")
            services = value.get("services")
            if services == "auto":
                self._auto_discover_services(services_path)
            elif services:
                self._load_services(services, services_path)

            for prop, val in value.items():
                self.__config[prop] = val

        elif isinstance(value, JsonDict):
            self.config = value.dictionary

    def _normalize_import_prefix(self, base_path: str) -> str:
        normalized = base_path.replace("/", ".").replace("\\", ".").strip(".")
        return f"{normalized}." if normalized else ""

    def _iter_service_modules(self, services_dir: str, services_path: str) -> Iterable[str]:
        prefix = self._normalize_import_prefix(services_path)

        for root, dirs, files in os.walk(services_dir):
            dirs[:] = [directory for directory in dirs if not directory.startswith("__")]

            relative_root = os.path.relpath(root, services_dir)
            package_prefix = ""
            if relative_root != ".":
                package_prefix = relative_root.replace("/", ".").replace("\\", ".") + "."

            for filename in files:
                if filename.startswith("__") or not filename.endswith(".py"):
                    continue

                yield prefix + package_prefix + filename[:-3]

    def _get_service_instances(self, module: Any) -> list[Any]:
        from AEngineApps.service import Service

        return [obj for _, obj in inspect.getmembers(module) if isinstance(obj, Service)]

    def _register_service_instance(self, service: Any, *, auto: bool = False) -> None:
        try:
            self.register_service(service)
            status = "автоматически " if auto else ""
            print(f"[App] Сервис '{service.name}' (префикс {service.prefix}) {status}зарегистрирован.")
        except Exception as e:
            print(f"[App] Ошибка регистрации сервиса '{service.name}': {e}")

    def _load_services(self, services: Any, services_path: str) -> None:
        """Load services from config.

        Supported shapes:
        - ["auth", "billing"]
        - {"auth": "auth_service", "billing": "billing_service"}
        """
        prefix = self._normalize_import_prefix(services_path)

        if isinstance(services, (list, tuple, set)):
            for service_module in services:
                if not isinstance(service_module, str) or not service_module.strip():
                    continue

                module_name = service_module if "." in service_module else prefix + service_module
                try:
                    module = import_module(module_name)
                except ImportError as e:
                    print(f"[App] Ошибка импорта сервиса '{module_name}': {e}")
                    continue

                services_in_module = self._get_service_instances(module)
                if not services_in_module:
                    print(f"[App] В модуле '{module_name}' не найдено экземпляров Service.")
                    continue

                for service in services_in_module:
                    self._register_service_instance(service)
            return

        if isinstance(services, dict):
            for service_module, service_object in services.items():
                if not isinstance(service_module, str) or not service_module.strip():
                    continue

                module_name = service_module if "." in service_module else prefix + service_module
                try:
                    module = import_module(module_name)
                except ImportError as e:
                    print(f"[App] Ошибка импорта сервиса '{module_name}': {e}")
                    continue

                if isinstance(service_object, str) and service_object.strip():
                    service = getattr(module, service_object, None)
                    if service is None:
                        print(f"[App] В модуле '{module_name}' не найден объект '{service_object}'.")
                        continue
                    self._register_service_instance(service)
                else:
                    services_in_module = self._get_service_instances(module)
                    if not services_in_module:
                        print(f"[App] В модуле '{module_name}' не найдено экземпляров Service.")
                        continue
                    for service in services_in_module:
                        self._register_service_instance(service)
            return

        print("[App] Параметр 'services' должен быть 'auto', списком или dict.")

    def _auto_discover_services(self, services_path: str) -> None:
        services_dir = os.path.join(self.project_root, services_path)

        if not os.path.isdir(services_dir):
            print(f"[App] Директория сервисов не найдена: {services_dir}")
            return

        for module_name in self._iter_service_modules(services_dir, services_path):
            try:
                module = import_module(module_name)
            except ImportError as e:
                print(f"[App] Ошибка импорта сервиса '{module_name}': {e}")
                continue

            for service in self._get_service_instances(module):
                self._register_service_instance(service, auto=True)

    def _auto_discover_screens(self, screen_path: str) -> None:
        screen_dir = os.path.join(self.project_root, screen_path)
        if not os.path.isdir(screen_dir):
            print(f"[App] Директория экранов не найдена: {screen_dir}")
            return

        prefix = screen_path.replace("/", ".").replace("\\", ".") + "."

        for filename in os.listdir(screen_dir):
            if filename.startswith("__") or not filename.endswith(".py"):
                continue

            mod_name = filename[:-3]
            try:
                module = import_module(prefix + mod_name)
            except ImportError as e:
                print(f"[App] Ошибка импорта '{mod_name}': {e}")
                continue

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

    def run(self) -> None:
        if getattr(self, "_original_stdout", None) and sys.stdout != getattr(self, "_original_stdout"):
            sys.stdout.close()
            sys.stdout = self._original_stdout
        if getattr(self, "_original_stderr", None) and sys.stderr != getattr(self, "_original_stderr"):
            sys.stderr.close()
            sys.stderr = self._original_stderr

        host: Optional[str] = self.config.get("host")
        port: Optional[int] = self.config.get("port")
        if not host:
            print("[App] Ошибка: не указан host в конфигурации.")
            return
        if not port:
            print("[App] Ошибка: не указан port в конфигурации.")
            return

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
        role = os.environ.get("AENGINE_CLUSTER_ROLE")
        is_slave = role == "slave"

        if is_slave:
            import logging

            logging.getLogger("werkzeug").disabled = True
            cli = sys.modules.get("flask.cli")
            if cli:
                cli.show_server_banner = lambda *args, **kwargs: None
        else:
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
            if not is_slave:
                print(f"[App] Ошибка запуска сервера: {e}")
                print(f"[App] Возможно, порт {port} уже занят.")

    def close(self) -> None:
        if self.window:
            self.window.destroy()
