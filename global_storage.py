"""
GlobalStorage — потокобезопасный singleton для глобального состояния.
"""

from typing import Any


class GlobalStorage:
    """Глобальное хранилище (singleton).
    
    Все экземпляры разделяют одно состояние.
    
    Пример:
        # file1.py
        gs = GlobalStorage()
        gs.user = "admin"
        
        # file2.py
        gs = GlobalStorage()
        print(gs.user)  # "admin"
    """
    _instance = None
    _data: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalStorage, cls).__new__(cls)
        return cls._instance

    def __setattr__(self, key: str, value: Any) -> None:
        GlobalStorage._data[key] = value

    def __getattr__(self, item: str) -> Any:
        try:
            return GlobalStorage._data[item]
        except KeyError:
            raise AttributeError(f"GlobalStorage не содержит '{item}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение по ключу с fallback."""
        return GlobalStorage._data.get(key, default)

    def has(self, key: str) -> bool:
        """Проверяет наличие ключа."""
        return key in GlobalStorage._data

    def delete(self, key: str) -> None:
        """Удаляет ключ из хранилища."""
        GlobalStorage._data.pop(key, None)

    def clear(self) -> None:
        """Очищает хранилище."""
        GlobalStorage._data.clear()

    def all(self) -> dict:
        """Возвращает все данные."""
        return dict(GlobalStorage._data)

    def __repr__(self) -> str:
        return f"GlobalStorage({GlobalStorage._data})"