import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BitrixClient:
    def __init__(self, domain: str, access_token: str):
        self.base_url = f"https://{domain}/rest"
        self.auth_params = {"auth": access_token}

    def _post(self, method: str, json_data: dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}.json"
        try:
            # auth передаем в params, данные в json
            resp = requests.post(url, params=self.auth_params, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Bitrix API error [{method}]: {e}")
            if e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            raise

    def install_robot(self, code: str, handler_url: str, name: str, props: dict, return_props: dict):
        # 1. Удаляем старого (best effort, не падаем если нет)
        try:
            self._post("bizproc.robot.delete", {"CODE": code})
        except Exception:
            pass

        # 2. Регистрируем нового
        payload = {
            "CODE": code,
            "HANDLER": handler_url,
            "AUTH_USER_ID": 1,
            "USE_SUBSCRIPTION": "Y",
            "NAME": name,
            "PROPERTIES": props,
            "RETURN_PROPERTIES": return_props,
            "FILTER": {"INCLUDE": [["crm", "CCrmDocumentDeal"]]}
        }
        return self._post("bizproc.robot.add", payload)

    def add_contact(self, fields: dict) -> Optional[int]:
        result = self._post("crm.contact.add", {"fields": fields})
        return result.get("result")

    def send_robot_result(self, event_token: str, return_values: dict):
        payload = {
            "event_token": event_token,
            "return_values": return_values
        }
        self._post("bizproc.event.send", payload)