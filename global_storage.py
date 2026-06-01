"""
GlobalStorage — потокобезопасный singleton для глобального состояния.
"""

import threading
from typing import Any


class GlobalStorage:
    """Глобальное хранилище (singleton).
    
    Все экземпляры разделяют одно состояние.
    Все операции чтения/записи защищены блокировкой (threading.RLock).
    
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
    _lock: threading.RLock = threading.RLock()

    def __new__(cls) -> "GlobalStorage":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GlobalStorage, cls).__new__(cls)
            return cls._instance

    def __setattr__(self, key: str, value: Any) -> None:
        with GlobalStorage._lock:
            GlobalStorage._data[key] = value

    def __getattr__(self, item: str) -> Any:
        with GlobalStorage._lock:
            try:
                return GlobalStorage._data[item]
            except KeyError:
                raise AttributeError(f"GlobalStorage не содержит '{item}'")

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение по ключу с fallback."""
        with GlobalStorage._lock:
            return GlobalStorage._data.get(key, default)

    def has(self, key: str) -> bool:
        """Проверяет наличие ключа."""
        with GlobalStorage._lock:
            return key in GlobalStorage._data

    def delete(self, key: str) -> None:
        """Удаляет ключ из хранилища."""
        with GlobalStorage._lock:
            GlobalStorage._data.pop(key, None)

    def clear(self) -> None:
        """Очищает хранилище."""
        with GlobalStorage._lock:
            GlobalStorage._data.clear()

    def all(self) -> dict:
        """Возвращает копию всех данных."""
        with GlobalStorage._lock:
            return dict(GlobalStorage._data)

    def __repr__(self) -> str:
        with GlobalStorage._lock:
            return f"GlobalStorage({GlobalStorage._data})"
