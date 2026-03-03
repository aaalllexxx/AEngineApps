"""
JsonDict — JSON-файл как Python-объект с автосохранением.
"""

import json
from typing import Any, Optional


class JsonDict:
    """Класс для работы с JSON как с объектом.
    
    При изменении атрибутов значения сохраняются в файл.
    
    Пример:
        data = JsonDict("config.json")
        data.host = "0.0.0.0"       # автоматически сохраняется
        print(data.port)             # читает из файла
        data.save()                  # принудительное сохранение
    """

    def __init__(self, path: str, encoding: str = "utf-8"):
        self.path: str = path
        self.encoding: str = encoding
        self._dirty: bool = False
        self.dictionary: dict = self.load()

    def __getitem__(self, item: str) -> Any:
        return self.dictionary.get(item)

    def __setitem__(self, key: str, value: Any) -> None:
        self.__setattr__(key, value)

    def __setattr__(self, key: str, value: Any) -> None:
        if "dictionary" in self.__dict__:
            if key not in ("dictionary", "path", "encoding", "_dirty"):
                self.dictionary[key] = value
                self._dirty = True
                self._auto_save()
        self.__dict__[key] = value
    
    def _auto_save(self) -> None:
        """Сохраняет изменения в файл."""
        if self._dirty:
            self.push(self.dictionary)
            self._dirty = False
    
    def keys(self) -> list[str]:
        """Возвращает список ключей."""
        return list(self.dictionary.keys())

    def values(self) -> list:
        """Возвращает список значений."""
        return list(self.dictionary.values())

    def items(self) -> list[tuple[str, Any]]:
        """Возвращает пары ключ-значение."""
        return list(self.dictionary.items())

    def has(self, key: str) -> bool:
        """Проверяет наличие ключа."""
        return key in self.dictionary

    def load(self) -> dict:
        """Загружает данные из файла."""
        try:
            with open(self.path, "r", encoding=self.encoding) as file:
                content = file.read()
                if not content:
                    content = "{}"
                dictionary = json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            dictionary = {}

        for k, v in dictionary.items():
            self.__dict__[k] = v

        return dictionary

    def save(self) -> None:
        """Принудительное сохранение в файл."""
        self.push(self.dictionary)

    def push(self, data: dict) -> None:
        """Записывает данные в файл."""
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        with open(self.path, "w", encoding=self.encoding) as file:
            file.write(serialized)

    def delete_item(self, key: str) -> None:
        """Удаляет ключ из словаря и файла."""
        if key in self.dictionary:
            del self.dictionary[key]
            if key in self.__dict__:
                del self.__dict__[key]
            self.push(self.dictionary)

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение по ключу с fallback."""
        return self.dictionary.get(key, default)

    def update(self, data: dict) -> None:
        """Обновляет несколько значений и сохраняет."""
        self.dictionary.update(data)
        for k, v in data.items():
            self.__dict__[k] = v
        self.push(self.dictionary)

    def __contains__(self, key: str) -> bool:
        return key in self.dictionary

    def __repr__(self) -> str:
        return json.dumps(self.dictionary, indent=2, ensure_ascii=False)