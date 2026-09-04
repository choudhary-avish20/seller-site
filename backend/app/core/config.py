import os
import sys

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, populated from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    PROJECT_NAME: str = "WolkaGo API"
    API_V1_PREFIX: str = "/api/v1"
    ENV: str = "development"
    DEBUG: bool = True

    # Database
    # Local dev default: SQLite (no extra setup needed).
    # Production: set DATABASE_URL to your Neon connection string, e.g.:
    #   postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require
    DATABASE_URL: str = "sqlite:///./wholesale.db"

    # Auth
    SECRET_KEY: str = "change-me-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS - allow all dev origins (vanilla at 8000/vanilla, 3001, etc.)
    # For production, restrict to specific domains via .env; never include "null".
    # Accepts a JSON array OR a comma-separated string, e.g.:
    #   CORS_ORIGINS=["https://example.com"]
    #   CORS_ORIGINS=https://example.com,https://other.com
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8000",
        "http://localhost:8002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:5173",
        # "null" intentionally omitted — it allows file:// origins which is a security risk
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        """Accept a JSON array string or a comma-separated string in addition to a plain list."""
        if not isinstance(v, str):
            return v
        v = v.strip()
        if v.startswith("["):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                # A malformed value here must never crash the whole app with a bare
                # traceback — fail with a message that says exactly what to fix.
                raise ValueError(
                    f"CORS_ORIGINS is not valid JSON: {v!r} ({e}). "
                    'Use a JSON array like ["https://example.com"] or a comma-separated '
                    "list like https://example.com,https://other.com"
                ) from e
        # comma-separated: "https://a.com, https://b.com"
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # Wholesale business settings
    REQUIRE_LOGIN_TO_SEE_PRICES: bool = False  # if True, guests cannot see net/gross prices
    REQUIRE_BUYER_APPROVAL: bool = False  # if True, buyers need admin approval before buying
    ALLOW_CASH_ON_DELIVERY_ONLY: bool = True

    # Email settings
    MAIL_USERNAME: str = ""  # SMTP username - if empty, use console backend for dev
    MAIL_PASSWORD: str = ""  # SMTP password
    MAIL_FROM: str = "noreply@wolkago.pl"  # From email address
    MAIL_FROM_NAME: str = "WolkaGo"  # From name
    MAIL_SERVER: str = "smtp.gmail.com"  # SMTP server
    MAIL_PORT: int = 587  # SMTP port
    MAIL_TLS: bool = True  # Use TLS
    MAIL_SSL: bool = False  # Use SSL (alternative to TLS)
    
    # Backend URL — used to build the verification link in emails.
    # In production set this to your backend service URL, e.g.:
    #   BACKEND_BASE_URL=https://seller-site-2.onrender.com
    # The verification link goes to /api/v1/auth/verify-email?token=... on the
    # backend, which consumes the token and then redirects the browser to the
    # frontend result page using FRONTEND_BASE_URL below.
    BACKEND_BASE_URL: str = "http://localhost:8000"

    # Frontend URL — used by the backend's /auth/verify-email redirect target.
    # Set to your frontend service URL in production, e.g.:
    #   FRONTEND_BASE_URL=https://seller-site-frontend.onrender.com
    FRONTEND_BASE_URL: str = "http://localhost:8000"

    # Cloudflare R2 image storage
    # Leave all R2 vars empty in local dev — uploads will fall back to local disk.
    # In production, set all five vars in Render's environment dashboard.
    # Get these from: Cloudflare dashboard → R2 → your bucket → Manage R2 API Tokens
    R2_ACCOUNT_ID: str = ""         # Cloudflare Account ID (found on R2 overview page)
    R2_ACCESS_KEY_ID: str = ""      # R2 API token Access Key ID
    R2_SECRET_ACCESS_KEY: str = ""  # R2 API token Secret Access Key
    R2_BUCKET_NAME: str = ""        # e.g. "seller-site-uploads"
    R2_PUBLIC_URL: str = ""         # Public bucket URL, e.g. "https://pub-xxx.r2.dev"
                                    # or your custom domain "https://cdn.yourdomain.com"

    @property
    def r2_configured(self) -> bool:
        """True when all five R2 vars are set — switches uploads from local disk to R2."""
        return all([
            self.R2_ACCOUNT_ID,
            self.R2_ACCESS_KEY_ID,
            self.R2_SECRET_ACCESS_KEY,
            self.R2_BUCKET_NAME,
            self.R2_PUBLIC_URL,
        ])


settings = Settings()

# Logs exactly what this process actually received for the handful of vars that
# most often go wrong on a new deploy — the raw string the OS/platform handed us
# (proving whether it was delivered at all) next to what Settings() resolved it
# to (proving it parsed the way you expect). Written to stderr with an explicit
# flush, same stream as the RuntimeError traceback below, so the two can never
# get reordered relative to each other in a log viewer that merges both streams.
# Never logs SECRET_KEY or MAIL_PASSWORD themselves, only whether each was left
# as its insecure default. Always logged, not just on failure, so a healthy
# deploy's log is equally checkable.
def _log_config_source(name: str, resolved) -> None:
    print(f"[config] {name}: raw_env_var={os.environ.get(name)!r} resolved={resolved!r}", file=sys.stderr, flush=True)

for _name, _resolved in [
    ("ENV", settings.ENV),
    ("DEBUG", settings.DEBUG),
    ("DATABASE_URL", settings.DATABASE_URL),
    ("CORS_ORIGINS", settings.CORS_ORIGINS),
    ("BACKEND_BASE_URL", settings.BACKEND_BASE_URL),
    ("FRONTEND_BASE_URL", settings.FRONTEND_BASE_URL),
]:
    _log_config_source(_name, _resolved)
print(
    f"[config] SECRET_KEY: raw_env_var_present={'SECRET_KEY' in os.environ!r} "
    f"is_still_placeholder={settings.SECRET_KEY == 'change-me-in-prod'!r}",
    file=sys.stderr, flush=True,
)

if settings.ENV == "production":
    # These checks close the gap where the app silently boots in an insecure state
    # if an operator forgets to override the dev defaults for a real deploy. All
    # problems are collected and reported together — so a misconfigured deploy
    # doesn't take multiple redeploy attempts to reveal each issue one at a time.
    _problems = []
    if settings.SECRET_KEY == "change-me-in-prod":
        _problems.append(
            "SECRET_KEY is still the default placeholder. Set a real SECRET_KEY "
            "environment variable (a long random string)."
        )
    if settings.DEBUG:
        _problems.append("DEBUG=true is set. Set DEBUG=false in production.")
    if _problems:
        raise RuntimeError(
            "Refusing to start with ENV=production due to " + str(len(_problems)) +
            " misconfiguration(s):\n- " + "\n- ".join(_problems)
        )
