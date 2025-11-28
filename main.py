import logging
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
from starlette.responses import JSONResponse

from auth import router as auth_router, load_tokens

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

app = FastAPI()
app.include_router(auth_router)

@app.post("/api/bitrix24")
async def bitrix_robot_post(request: Request):
    logging.info("=== Входящий запрос от робота (POST) ===")
    form = await request.form()
    form = dict(form)

    tokens = load_tokens()
    if not tokens:
        return PlainTextResponse("App not installed", status_code=400)

    access_token = tokens["access_token"]
    domain = tokens["domain"]
    event_token = form.get("event_token")

    # Получаем данные
    last_name = form.get("properties[LAST_NAME]")
    first_name = form.get("properties[NAME]")
    second_name = form.get("properties[SECOND_NAME]", "")  # Пустая строка, если нет
    phone = form.get("properties[PHONE]", "")
    email = form.get("properties[EMAIL]", "")

    if not last_name or not first_name:
        return PlainTextResponse("NAME and LAST_NAME required", status_code=400)

    # 1. Формируем поля для создания контакта
    fields = {
        "NAME": first_name,
        "LAST_NAME": last_name,
        "SECOND_NAME": second_name
    }

    if phone:
        fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "WORK"}]
    if email:
        fields["EMAIL"] = [{"VALUE": email, "VALUE_TYPE": "WORK"}]

    # 2. Создаем контакт в Битрикс24
    url_add = f"https://{domain}/rest/crm.contact.add.json?auth={access_token}"
    response = requests.post(url_add, json={"fields": fields})
    response_data = response.json()
    new_contact_id = response_data.get("result")

    # 3. Отправляем результат обратно в робота
    if event_token and new_contact_id:

        parts = [last_name, first_name, second_name]
        full_name_str = " ".join([part.strip() for part in parts if part and part.strip()])

        bizproc_url = f"https://{domain}/rest/bizproc.event.send.json?auth={access_token}"

        bizproc_payload = {
            "event_token": event_token,
            "return_values": {
                "created_contact_id": new_contact_id,
                # Заполняем поля, описанные в auth.py -> RETURN_PROPERTIES
                "res_name": first_name,
                "res_last_name": last_name,
                "res_second_name": second_name,
                "res_full_name": full_name_str,
                "res_phone": phone,
                "res_email": email
            }
        }

        bp_resp = requests.post(bizproc_url, json=bizproc_payload)
        logging.info(f"Ответ bizproc.event.send: {bp_resp.status_code} {bp_resp.text}")
    else:
        logging.warning("Не удалось отправить результат: нет event_token или contact_id")

    return PlainTextResponse("OK")


@app.get("/api/bitrix24")
async def bitrix_robot_get():
    logging.info("=== Проверка handler URL GET ===")
    return JSONResponse(content={"result": "ok"})
