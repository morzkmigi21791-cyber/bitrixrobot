import json
import os
from abc import ABC, abstractmethod
from typing import Optional

# Интерфейс
class ITokenRepository(ABC):
    @abstractmethod
    def save(self, data: dict):
        pass

    @abstractmethod
    def load(self) -> Optional[dict]:
        pass

# Реализация для JSON файла
class JsonTokenRepository(ITokenRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def save(self, data: dict):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load(self) -> Optional[dict]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None