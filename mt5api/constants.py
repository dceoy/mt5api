"""Application-wide constants."""

from importlib.metadata import version

API_TITLE = "MT5 REST API"
API_DESCRIPTION = (
    "REST API for MetaTrader 5 data access and non-executing terminal utilities. "
    "Provides market data, account information, trading history, calculations, "
    "and safe operational endpoints via HTTP."
)
API_VERSION = version("mt5api")
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"
API_OPENAPI_URL = "/openapi.json"
API_APP_IMPORT = "mt5api.main:app"
API_KEY_HEADER_NAME = "X-API-Key"
API_KEY_SECURITY_SCHEME_NAME = "APIKeyHeader"
MT5_RUNTIME_STATE_KEY = "mt5_runtime"

ENV_MT5API_HOST = "MT5API_HOST"
ENV_MT5API_PORT = "MT5API_PORT"
ENV_MT5API_LOG_LEVEL = "MT5API_LOG_LEVEL"
ENV_MT5API_ROUTER_PREFIX = "MT5API_ROUTER_PREFIX"
ENV_MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS = "MT5API_MAX_MARKET_BOOK_SUBSCRIPTIONS"
ENV_MT5API_SECRET_KEY = "MT5API_SECRET_KEY"  # noqa: S105

DEFAULT_API_HOST = "0.0.0.0"  # noqa: S104
DEFAULT_API_PORT = 8000
DEFAULT_API_LOG_LEVEL = "INFO"
DEFAULT_API_ROUTER_PREFIX = ""
DEFAULT_MAX_MARKET_BOOK_SUBSCRIPTIONS = 100
MAX_API_PORT = 65535
