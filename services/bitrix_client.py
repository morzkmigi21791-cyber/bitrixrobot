import httpx
import logging
from typing import Dict, Any, Optional
from schemas import RobotConfig

logger = logging.getLogger(__name__)

class BitrixClient:
    """
    Низкоуровневый HTTP-клиент для работы с REST API Bitrix24.
    Отвечает только за отправку запросов и обработку сетевых ошибок
    """
    def __init__(self, client: httpx.AsyncClient, domain: str, access_token: str):
        self.client = client
        self.base_url = f"https://{domain}/rest"
        # httpx передает params немного иначе, но логика та же
        self.auth_params = {"auth": access_token}

    async def _post(self, method: str, json_data: dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}.json"
        try:
            resp = await self.client.post(url, params=self.auth_params, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Bitrix API Error [{method}]: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network Error [{method}]: {e}")
            raise

    async def install_robot(self, config: RobotConfig):
        try:
            await self._post("bizproc.robot.delete", {"CODE": config.code})
        except Exception:
            pass

        payload = {
            "CODE": config.code,
            "HANDLER": config.handler_url,
            "AUTH_USER_ID": 1,
            "USE_SUBSCRIPTION": "Y",
            "NAME": config.name,
            "PROPERTIES": {k: v.model_dump(exclude_none=True) for k, v in config.properties.items()},
            "RETURN_PROPERTIES": {k: v.model_dump(exclude_none=True) for k, v in config.return_properties.items()},
            "FILTER": {"INCLUDE": [["crm", "CCrmDocumentDeal"]]}
        }
        return await self._post("bizproc.robot.add", payload)

    async def add_contact(self, fields: dict) -> Optional[int]:
        result = await self._post("crm.contact.add", {"fields": fields})
        return result.get("result")

    async def send_robot_result(self, event_token: str, return_values: dict):
        payload = {
            "event_token": event_token,
            "return_values": return_values
        }
        await self._post("bizproc.event.send", payload)