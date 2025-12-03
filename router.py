from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, PlainTextResponse, JSONResponse
import httpx
import logging

from config import settings
from dependencies import get_repository, get_robot_service, get_http_client
from services.processing import RobotService
from schemas import ContactCreateDTO

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/bitrix/oauth/install")
async def oauth_callback(
        request: Request,
        repo=Depends(get_repository),
        http_client: httpx.AsyncClient = Depends(get_http_client),
        service: RobotService = Depends(get_robot_service)
):
    """
        OAuth 2.0 Callback Endpoint (GET).
    Сюда Битрикс перенаправляет пользователя после успешной авторизации.
    Метод обменивает временный `code` на постоянные `access_token` и `refresh_token`,
    сохраняет их и завершает установку робота.
    """
    code = request.query_params.get("code")
    if not code:
        auth_url = (f"{settings.BITRIX_OAUTH_URL}/oauth/authorize/?client_id={settings.CLIENT_ID}"
                    f"&redirect_uri={settings.HOST_URL}/bitrix/oauth/install&response_type=code")
        return RedirectResponse(url=auth_url)

    token_url = f"{settings.BITRIX_OAUTH_URL}/oauth/token/"
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
        "code": code,
        "redirect_uri": f"{settings.HOST_URL}/bitrix/oauth/install"
    }

    resp = await http_client.post(token_url, data=payload)
    if resp.status_code != 200:
        return JSONResponse({"error": resp.text}, status_code=400)

    token_data = resp.json()
    await repo.save(token_data)

    # ДЕЛЕГИРОВАНИЕ: Роутер просто просит сервис "установи робота"
    if "domain" in token_data:
        await service.install_robot(token_data["domain"], token_data["access_token"])

    return JSONResponse({"status": "installed"})


@router.post("/bitrix/oauth/install")
async def install_app_event(
        request: Request,
        repo=Depends(get_repository),
        service: RobotService = Depends(get_robot_service)
):
    form = await request.form()
    data = dict(form)
    auth_data = {k: v for k, v in data.items() if k.startswith("auth[")}

    access_token = auth_data.get("auth[access_token]")
    domain = auth_data.get("auth[domain]")

    if not access_token:
        return JSONResponse({"error": "No token"}, status_code=400)

    await repo.save({
        "access_token": access_token,
        "refresh_token": auth_data.get("auth[refresh_token]"),
        "domain": domain
    })

    await service.install_robot(domain, access_token)

    return JSONResponse({"status": "installed"})


@router.post("/api/bitrix24")
async def robot_handler(request: Request, service: RobotService = Depends(get_robot_service)):
    """
        Основной обработчик робота (Handler URL).
    Этот эндпоинт вызывает сам Бизнес-процесс Битрикса, когда доходит до шага с роботом.
    Принимает параметры (имя, телефон и т.д.) в формате form-data.
    """
    form = await request.form()
    event_token = form.get("event_token")

    if not event_token:
        return PlainTextResponse("Token missing", status_code=400)

    contact_dto = ContactCreateDTO(
        last_name=form.get("properties[LAST_NAME]", ""),
        first_name=form.get("properties[NAME]", ""),
        second_name=form.get("properties[SECOND_NAME]"),
        phone=form.get("properties[PHONE]"),
        email=form.get("properties[EMAIL]")
    )

    if not contact_dto.last_name:
        return PlainTextResponse("Error: LAST_NAME required", status_code=400)

    try:
        await service.process_robot_request(event_token, contact_dto)
        return PlainTextResponse("OK")
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return PlainTextResponse(f"Error: {str(e)}", status_code=500)


@router.get("/api/bitrix24")
async def robot_check():
    return JSONResponse({"result": "pong"})