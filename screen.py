"""
Screen — базовый класс экрана AEngineApps.
Все экраны приложения наследуются от этого класса.
"""

from typing import Any, Optional
from flask import render_template, redirect as flask_redirect, jsonify, request, url_for, session, flash, abort
import os


class Screen:
    """Базовый класс экрана.
    
    Атрибуты класса:
        route: str | list[str] — маршрут(ы) экрана (для авто-роутинга)
        methods: list[str] — HTTP-методы (по умолчанию ["GET"])
    
    Пример:
        class HomeScreen(Screen):
            route = "/"
            methods = ["GET"]
            
            def run(self):
                return self.render("index.html", title="Главная")
    """
    
    route: str = "/"
    methods: list[str] = ["GET"]
    _app = None  # ссылка на App, устанавливается автоматически

    def __init__(self) -> None:
        self.__name__: str = self.__class__.__name__

    def run(self, *args, **kwargs) -> Any:
        """Основной метод экрана. Должен быть переопределён."""
        raise NotImplementedError(
            f"Метод 'run' экрана '{self.__name__}' не реализован"
        )

    def __call__(self, *args, **kwargs) -> Any:
        return self.run(*args, **kwargs)

    # ─── Хелперы ──────────────────────────────────────────────

    def render(self, template: str, **context) -> str:
        """Рендерит HTML-шаблон.
        
        Пример:
            return self.render("home.html", title="Главная", items=items)
        """
        return render_template(template, **context)

    def redirect(self, url: str, code: int = 302):
        """Перенаправляет на другой URL.
        
        Пример:
            return self.redirect("/login")
        """
        return flask_redirect(url, code)

    def json(self, data: Any, status: int = 200):
        """Возвращает JSON-ответ.
        
        Пример:
            return self.json({"status": "ok", "users": users})
        """
        response = jsonify(data)
        response.status_code = status
        return response

    @property
    def request(self):
        """Доступ к текущему запросу Flask.
        
        Пример:
            name = self.request.args.get("name")
            data = self.request.json
        """
        return request

    @property
    def app(self):
        """Ссылка на экземпляр App (устанавливается автоматически)."""
        return self._app

    @property
    def session(self):
        """Доступ к сессии (работает как dict).
        
        Требует заданного SECRET_KEY в конфигурации Flask.
        """
        return session
        
    def abort(self, code: int, *args, **kwargs):
        """Мгновенно прерывает запрос с кодом ошибки.
        
        Пример:
            self.abort(404)
        """
        abort(code, *args, **kwargs)

    def flash(self, message: str, category: str = "message"):
        """Показывает флеш-сообщение пользователю (Flash messages).
        
        Пример:
            self.flash("Успешно сохранено!", "success")
        """
        flash(message, category)

    @property
    def client_ip(self) -> str:
        """Безопасное получение IP-адреса пользователя (через прокси или напрямую)."""
        forwarded = self.request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.request.remote_addr or "127.0.0.1"

    def save_file(self, field_name: str, save_path: str) -> bool:
        """Удобное сохранение загруженного через POST-форму файла.
        
        Пример:
            if self.save_file("avatar", "static/avatars/user_1.png"):
                print("Успешно загружено")
        """
        file = self.request.files.get(field_name)
        if file and file.filename != "":
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            return True
        return False