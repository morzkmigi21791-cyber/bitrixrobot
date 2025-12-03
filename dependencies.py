import httpx
from typing import AsyncGenerator
from fastapi import Depends
from config import settings
from repositories.token_store import JsonTokenRepository, ITokenRepository
from services.processing import RobotService

def get_repository() -> ITokenRepository:
    return JsonTokenRepository(settings.TOKENS_FILE)

# HTTP Client (Resource Management)
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        yield client

# Сервис
async def get_robot_service(
    repo: ITokenRepository = Depends(get_repository),
    http_client: httpx.AsyncClient = Depends(get_http_client)
) -> RobotService:
    return RobotService(repo, http_client)