import json
import os
import aiofiles
from abc import ABC, abstractmethod
from typing import Optional

class ITokenRepository(ABC):
    """
    Интерфейс (контракт) для хранилища токенов.
    Позволяет подменять реализацию (файл -> база данных) без изменения бизнес-логики.
    """
    @abstractmethod
    async def save(self, data: dict):
        pass

    @abstractmethod
    async def load(self) -> Optional[dict]:
        pass

class JsonTokenRepository(ITokenRepository):
    def __init__(self, file_path: str):
        self.file_path = file_path

    async def save(self, data: dict):
        async with aiofiles.open(self.file_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))

    async def load(self) -> Optional[dict]:
        if not os.path.exists(self.file_path):
            return None
        try:
            async with aiofiles.open(self.file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return None