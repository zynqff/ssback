import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "sUper_sEcrEt_kEy_fOr_pRojeCt_2024_fAstApi")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 день

    # Админы
    ADMIN_USERNAMES = os.getenv("ADMIN_USERNAMES", "").split(",")
    ADMIN_PASSWORDS = os.getenv("ADMIN_PASSWORDS", "").split(",")

    @property
    def ADMINS_DICT(self):
        return dict(zip(self.ADMIN_USERNAMES, self.ADMIN_PASSWORDS))

settings = Settings()
