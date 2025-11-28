from fastapi import APIRouter, Request
import requests
import logging
import json
import os
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
HOST_URL = os.getenv("HOST_URL")
REDIRECT_URI = f"{HOST_URL}/bitrix/oauth/install"
TOKENS_FILE = "tokens.json"


def save_tokens(data: dict):
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def create_robot(domain, access_token, robot_name="Bit24Test", document_type="CCrmDocumentDeal"):

    code = "REST_ROBOT_MY_UNIQUE_V3"

    # Удаляем старого (на всякий случай)
    requests.post(
        f"https://{domain}/rest/bizproc.robot.delete.json?auth={access_token}",
        json={"CODE": code}
    )

    # Правильный адрес обработчика (БЕЗ button_handler)
    handler_url = f"{HOST_URL}/api/bitrix24"

    payload = {
        "CODE": code,
        "HANDLER": handler_url,
        "AUTH_USER_ID": 1,
        "USE_SUBSCRIPTION": "Y",
        "NAME": robot_name,
        # Входящие параметры
        "PROPERTIES": {
            "LAST_NAME": {"Name": "Фамилия", "Type": "string", "Required": True},
            "NAME": {"Name": "Имя", "Type": "string", "Required": True},
            "SECOND_NAME": {"Name": "Отчество", "Type": "string"},
            "PHONE": {"Name": "Телефон", "Type": "string"},
            "EMAIL": {"Name": "Email", "Type": "string"}
        },
        "RETURN_PROPERTIES": {
            "created_contact_id": {"Name": "ID созданного контакта", "Type": "int"},
            "res_name": {"Name": "Имя контакта", "Type": "string"},
            "res_last_name": {"Name": "Фамилия контакта", "Type": "string"},
            "res_second_name": {"Name": "Отчество контакта", "Type": "string"},
            "res_full_name": {"Name": "ФИО (одной строкой)", "Type": "string"},
            "res_phone": {"Name": "Телефон контакта (возврат)", "Type": "string"},
            "res_email": {"Name": "Email контакта (возврат)", "Type": "string"}
        },

        "FILTER": {
            "INCLUDE": [
                ["crm", document_type]
            ]
        }
    }

    url = f"https://{domain}/rest/bizproc.robot.add.json?auth={access_token}"
    resp = requests.post(url, json=payload)
    logging.info(f"Робот зарегистрирован (V3): {resp.status_code} {resp.text}")
    return resp.json()


@router.api_route("/bitrix/oauth/install", methods=["GET", "POST"])
async def install_app(request: Request):
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
        save_tokens(token_data)
        create_robot(token_data["domain"], token_data["access_token"])
        return {"status": "installed"}

    code = request.query_params.get("code")
    if not code:
        auth_url = (f"https://oauth.bitrix.info/oauth/authorize/?client_id={CLIENT_ID}"
                    f"&redirect_uri={REDIRECT_URI}&response_type=code")
        return RedirectResponse(url=auth_url)

    token_url = "https://oauth.bitrix.info/oauth/token/"
    resp = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "code": code, "redirect_uri": REDIRECT_URI
    })

    if resp.status_code != 200:
        return {"error": resp.text}

    token_data = resp.json()
    save_tokens(token_data)
    create_robot(token_data["domain"], token_data["access_token"])
    return {"status": "installed", "token": token_data}