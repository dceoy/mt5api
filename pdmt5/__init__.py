"""pdmt5: Pandas-based data handler for MetaTrader 5."""

from importlib.metadata import version

from .dataframe import Mt5Config, Mt5DataClient
from .mt5 import Mt5Client, Mt5RuntimeError
from .trading import Mt5TradingClient, Mt5TradingError

__version__ = version(__package__) if __package__ else None

__all__ = [
    "Mt5Client",
    "Mt5Config",
    "Mt5DataClient",
    "Mt5RuntimeError",
    "Mt5TradingClient",
    "Mt5TradingError",
]

try:
    from .api.main import app as api_app
except (ImportError, RuntimeError):
    api_app = None
else:
    __all__ += ["api_app"]
