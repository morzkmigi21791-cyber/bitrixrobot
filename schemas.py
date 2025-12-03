from pydantic import BaseModel
from typing import Optional, Dict

class ContactCreateDTO(BaseModel):
    """
    Модель данных (DTO) для создания контакта.
    Валидирует входящие данные от робота перед отправкой в CRM.
    """
    last_name: str
    first_name: str
    second_name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

class TokenData(BaseModel):
    """
    Структура данных для хранения токенов авторизации OAuth.
    """
    access_token: str
    refresh_token: str
    application_token: Optional[str] = None
    domain: str

class RobotProperty(BaseModel):
    Name: str
    Type: str = "string"
    Required: bool = False

class RobotConfig(BaseModel):
    """
    Конфигурация робота для регистрации в Bitrix24.
    Описывает код, название, входные и выходные параметры.
    """
    code: str
    name: str
    handler_url: str
    properties: Dict[str, RobotProperty]
    return_properties: Dict[str, RobotProperty]