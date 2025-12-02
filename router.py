from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, PlainTextResponse, JSONResponse
import requests
import logging

from config import settings
from dependencies import get_repository, get_robot_service
from services.processing import RobotService
from services.bitrix_client import BitrixClient
from schemas import ContactCreateDTO

router = APIRouter()
logger = logging.getLogger(__name__)

# Конфигурация робота (можно вынести в config или отдельный файл констант)
ROBOT_CODE = "REST_ROBOT_MY_UNIQUE_V3"
ROBOT_NAME = "Bit24Test"
ROBOT_PROPS = {
    "LAST_NAME": {"Name": "Фамилия", "Type": "string", "Required": True},
    "NAME": {"Name": "Имя", "Type": "string", "Required": True},
    "SECOND_NAME": {"Name": "Отчество", "Type": "string"},
    "PHONE": {"Name": "Телефон", "Type": "string"},
    "EMAIL": {"Name": "Email", "Type": "string"}
}
ROBOT_RETURN_PROPS = {
    "created_contact_id": {"Name": "ID созданного контакта", "Type": "int"},
    "res_name": {"Name": "Имя контакта", "Type": "string"},
    "res_last_name": {"Name": "Фамилия контакта", "Type": "string"},
    "res_second_name": {"Name": "Отчество контакта", "Type": "string"},
    "res_full_name": {"Name": "ФИО (одной строкой)", "Type": "string"},
    "res_phone": {"Name": "Телефон контакта (возврат)", "Type": "string"},
    "res_email": {"Name": "Email контакта (возврат)", "Type": "string"}
}


@router.api_route("/bitrix/oauth/install", methods=["GET", "POST"])
async def install_route(request: Request, repo=Depends(get_repository)):
    """Обработка установки приложения (POST) и OAuth авторизации (GET)"""

    # 1. Установка из маркетплейса (POST запрос от Битрикса)
    if request.method == "POST":
        form = await request.form()
        data = dict(form)
        auth = {k: v for k, v in data.items() if k.startswith("auth[")}

        token_data = {
            "access_token": auth.get("auth[access_token]"),
            "refresh_token": auth.get("auth[refresh_token]"),
            "application_token": auth.get("auth[application_token]"),
            "domain": auth.get("auth[domain]")
        }

        if not token_data["access_token"]:
            return JSONResponse({"error": "No access token"}, status_code=400)

        repo.save(token_data)

        # Регистрируем робота
        client = BitrixClient(token_data["domain"], token_data["access_token"])
        try:
            client.install_robot(
                code=ROBOT_CODE,
                handler_url=f"{settings.HOST_URL}/api/bitrix24",
                name=ROBOT_NAME,
                props=ROBOT_PROPS,
                return_props=ROBOT_RETURN_PROPS
            )
        except Exception as e:
            logger.error(f"Failed to install robot: {e}")

        return {"status": "installed"}

    # 2. Локальная авторизация (GET запрос)
    code = request.query_params.get("code")
    redirect_uri = f"{settings.HOST_URL}/bitrix/oauth/install"

    if not code:
        auth_url = (f"{settings.BITRIX_OAUTH_URL}/oauth/authorize/?client_id={settings.CLIENT_ID}"
                    f"&redirect_uri={redirect_uri}&response_type=code")
        return RedirectResponse(url=auth_url)

    # Обмен кода на токен
    token_url = f"{settings.BITRIX_OAUTH_URL}/oauth/token/"
    try:
        resp = requests.post(token_url, data={
            "grant_type": "authorization_code",
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri
        })

        if resp.status_code != 200:
            return JSONResponse({"error": resp.text}, status_code=400)

        token_data = resp.json()
        # Приводим к единому формату (в ответе oauth нет поля domain, но есть client_endpoint)
        # Обычно domain нужно вытащить из client_endpoint или scope,
        # но для простоты сохраним как есть, если domain уже был известен или извлекаем.
        # В Bitrix OAuth ответе часто нет 'domain' в явном виде, но есть 'client_endpoint'.
        # Упрощение: предполагаем, что domain там есть или мы его знаем.
        # (В install_app оригинальном коде он брался из resp.json(), значит он там есть).

        repo.save(token_data)

        # Регистрируем робота
        if "domain" in token_data:
            # Обратите внимание: иногда 'domain' не приходит в OAuth ответе,
            # тогда надо делать запрос к current user или server info.
            # Оставим логику оригинала.
            client = BitrixClient(token_data["domain"], token_data["access_token"])
            client.install_robot(ROBOT_CODE, f"{settings.HOST_URL}/api/bitrix24", ROBOT_NAME, ROBOT_PROPS,
                                 ROBOT_RETURN_PROPS)

        return {"status": "installed", "tokens": "saved"}

    except Exception as e:
        logger.error(f"OAuth error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/bitrix24")
async def robot_handler(request: Request, service: RobotService = Depends(get_robot_service)):
    """Обработчик действий робота"""
    form = await request.form()

    event_token = form.get("event_token")
    if not event_token:
        # Битрикс может проверять доступность хендлера без токена
        return PlainTextResponse("Event token missing", status_code=400)

    # Маппинг Form -> DTO
    contact_dto = ContactCreateDTO(
        last_name=form.get("properties[LAST_NAME]", ""),
        first_name=form.get("properties[NAME]", ""),
        second_name=form.get("properties[SECOND_NAME]"),
        phone=form.get("properties[PHONE]"),
        email=form.get("properties[EMAIL]")
    )

    if not contact_dto.last_name or not contact_dto.first_name:
        return PlainTextResponse("NAME and LAST_NAME required", status_code=400)

    try:
        service.process_robot_request(event_token, contact_dto)
        return PlainTextResponse("OK")
    except Exception as e:
        logger.error(f"Processing error: {e}")
        # Возвращаем 500, чтобы Битрикс увидел ошибку в логах БП
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)


@router.get("/api/bitrix24")
async def robot_check():
    """Проверка доступности (Ping)"""
    return JSONResponse({"result": "pong"})