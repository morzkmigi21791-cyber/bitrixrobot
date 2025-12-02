import logging
from .bitrix_client import BitrixClient
from repositories.token_store import ITokenRepository
from schemas import ContactCreateDTO

logger = logging.getLogger(__name__)

class RobotService:
    def __init__(self, repo: ITokenRepository):
        self.repo = repo

    def _get_client(self) -> BitrixClient:
        tokens = self.repo.load()
        if not tokens or "domain" not in tokens or "access_token" not in tokens:
            raise ValueError("Application not installed or tokens corrupted")
        return BitrixClient(tokens["domain"], tokens["access_token"])

    def process_robot_request(self, event_token: str, data: ContactCreateDTO):
        client = self._get_client()
        logger.info(f"Processing robot request for: {data.first_name} {data.last_name}")

        # 1. Формируем поля для CRM
        crm_fields = {
            "NAME": data.first_name,
            "LAST_NAME": data.last_name,
            "SECOND_NAME": data.second_name,
            "TYPE_ID": "CLIENT"
        }
        if data.phone:
            crm_fields["PHONE"] = [{"VALUE": data.phone, "VALUE_TYPE": "WORK"}]
        if data.email:
            crm_fields["EMAIL"] = [{"VALUE": data.email, "VALUE_TYPE": "WORK"}]

        # 2. Создаем контакт
        contact_id = client.add_contact(crm_fields)
        logger.info(f"Contact created ID: {contact_id}")

        # 3. Формируем ответ для робота
        full_name_parts = [data.last_name, data.first_name, data.second_name]
        full_name = " ".join([p for p in full_name_parts if p]).strip()

        return_values = {
            "created_contact_id": contact_id,
            "res_name": data.first_name,
            "res_last_name": data.last_name,
            "res_second_name": data.second_name,
            "res_full_name": full_name,
            "res_phone": data.phone,
            "res_email": data.email
        }

        # 4. Отправляем в бизнес-процесс
        client.send_robot_result(event_token, return_values)