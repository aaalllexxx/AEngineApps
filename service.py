"""
AEngineApps.service — поддержка мультисервисной/модульной архитектуры.
"""
from typing import Callable, Any
from flask import Blueprint


class Service:
    """
    Легковесный класс для разбиения монолита на логические модули / сервисы.
    Является объектно-ориентированной оберткой над Flask Blueprint.
    
    Пример:
        # Модуль авторизации (services/auth.py)
        from AEngineApps.service import Service
        
        auth_service = Service("auth", prefix="/auth")
        auth_service.add_screen("/login", LoginAPI)
        
        # Регистрация в main.py
        app.register_service(auth_service)
    """
    
    def __init__(self, name: str, prefix: str = ""):
        self.name = name
        self.prefix = prefix
        self.blueprint = Blueprint(name, name, url_prefix=prefix)
        self._screens = []

    def add_screen(self, path: str, screen_cls: type, **options) -> None:
        """Регистрация экрана внутри сервиса с учетом префикса сервиса."""
        instance = screen_cls()
        
        # Гарантируем уникальное имя функции-обработчика для Flask
        name_str = path.replace("/", "_") or "root"
        instance.__name__ = f"{self.name}_{name_str}"
        
        if "methods" not in options and hasattr(screen_cls, "methods"):
            options["methods"] = screen_cls.methods
            
        self.blueprint.add_url_rule(path, view_func=instance, **options)
        self._screens.append(instance)

    def before_request(self, func: Callable) -> None:
        """Middleware, работающее ТОЛЬКО для экранов этого сервиса."""
        self.blueprint.before_request(func)

    def after_request(self, func: Callable) -> None:
        """Middleware, вызываемое ТОЛЬКО после запросов к экранам этого сервиса."""
        self.blueprint.after_request(func)
