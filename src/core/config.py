import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Carrega variáveis de ambiente de .env se existir
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    PROJECT_NAME: str = "Inteligência Financeira Pessoal"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/financial.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-local-financial-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

settings = Settings()
