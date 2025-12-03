import logging
import httpx
from .bitrix_client import BitrixClient
from repositories.token_store import ITokenRepository
from schemas import ContactCreateDTO
from constants import DEFAULT_ROBOT_CONFIG
from config import settings

logger = logging.getLogger(__name__)


class RobotService:
    """
    Сервис бизнес-логики.
    Оркестрирует работу между хранилищем токенов, HTTP-клиентом и данными.
    """
    def __init__(self, repo: ITokenRepository, http_client: httpx.AsyncClient):
        self.repo = repo
        self.http_client = http_client

    async def install_robot(self, domain: str, access_token: str):
        """
                Сценарий установки робота на портал
        1. Создает клиента с переданными кредами.
        2. Формирует конфигурацию робота (проставляя актуальный URL обработчика).
        3. Отправляет запрос на регистрацию.
        """
        client = BitrixClient(self.http_client, domain, access_token)

        config = DEFAULT_ROBOT_CONFIG.model_copy()
        config.handler_url = f"{settings.HOST_URL}/api/bitrix24"

        try:
            await client.install_robot(config)
            logger.info(f"Robot {config.code} installed successfully on {domain}")
        except Exception as e:
            logger.error(f"Failed to install robot on {domain}: {e}")
            raise

    async def process_robot_request(self, event_token: str, data: ContactCreateDTO):
        """
            Основной сценарий выполнения робота
        Args:
            event_token (str): Токен события, пришедший от Битрикса (нужен для ответа).
            data (ContactCreateDTO): Валидированные данные контакта.

        Steps:
            1. Загружает токены из репозитория.
            2. Формирует поля для CRM.
        3. Создает контакт.
        4. Возвращает ID и сформированные данные обратно в процесс.
        """
        tokens = await self.repo.load()
        if not tokens or "domain" not in tokens:
            raise ValueError("Tokens missing or corrupted")

        client = BitrixClient(self.http_client, tokens["domain"], tokens["access_token"])

        logger.info(f"Processing request for: {data.first_name} {data.last_name}")

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

        contact_id = await client.add_contact(crm_fields)

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

        await client.send_robot_result(event_token, return_values)