"""
AEngineApps.api — модуль для элегантного создания REST API.
"""

from AEngineApps.screen import Screen


class API(Screen):
    """
    Базовый класс для создания REST API.
    Автоматически маршрутизирует HTTP-запросы в соответствующие методы (get, post, put, delete).
    Автоматически конвертирует словари (dict) и списки (list) в JSON-ответы.
    
    Пример:
        class UserAPI(API):
            route = "/api/user"
            methods = ["GET", "POST"]
            
            def get(self):
                return {"name": "Alex"}  # Авто-конвертация в JSON
                
            def post(self):
                data = self.request.json
                return {"status": "created"}, 201  # JSON + HTTP 201
    """
    
    def run(self, *args, **kwargs):
        # Получаем HTTP метод в нижнем регистре (get, post, put, delete и т.д.)
        method = self.request.method.lower()
        
        # Ищем соответствующий метод в классе
        if hasattr(self, method):
            handler = getattr(self, method)
            result = handler(*args, **kwargs)
            
            # Автоматическая конвертация результата в JSON
            if isinstance(result, tuple):
                data, status = result
                if isinstance(data, (dict, list)):
                    return self.json(data, status)
                return result
            elif isinstance(result, (dict, list)):
                return self.json(result)
            
            return result
        else:
            # Если метода нет — возвращаем 405 Method Not Allowed
            return self.json({"error": "Method Not Allowed"}, 405)

    # ─── API Хелперы ──────────────────────────────────────────

    def require_keys(self, required_keys: list[str]) -> tuple[bool, str]:
        """Удобная проверка наличия обязательных ключей в JSON запросе.
        Возвращает кортеж: (статус, отсутствующий_ключ).
        
        Пример:
            ok, missing = self.require_keys(["username", "password"])
            if not ok:
                return {"error": f"Missing key: {missing}"}, 400
        """
        data = self.request.json
        if not isinstance(data, dict):
            return False, "JSON body"
            
        for key in required_keys:
            if key not in data:
                return False, key
        return True, ""

    def get_arg(self, key: str, type_func=str, default=None):
        """Безопасное получение и типизация параметра запроса (?key=value).
        
        Пример:
            limit = self.get_arg("limit", type_func=int, default=10)
        """
        val = self.request.args.get(key)
        if val is None:
            return default
        try:
            return type_func(val)
        except (ValueError, TypeError):
            return default
