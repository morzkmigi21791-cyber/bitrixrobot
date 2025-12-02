from functools import lru_cache
from fastapi import Depends
from config import settings
from repositories.token_store import JsonTokenRepository, ITokenRepository
from services.processing import RobotService

@lru_cache()
def get_repository() -> ITokenRepository:
    return JsonTokenRepository(settings.TOKENS_FILE)

def get_robot_service(repo: ITokenRepository = Depends(get_repository)) -> RobotService:
    return RobotService(repo)