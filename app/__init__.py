"""Composition root: единственное место, где выбираются конкретные реализации (D)."""
import os
from pathlib import Path

from flask import Flask

from .cache import JsonCache
from .messages import Messages
from .providers.bnm import BnmProvider
from .providers.nasa import NasaNeoProvider
from .routes import bp
from .services.neo import NeoService
from .services.rates import RatesService


def create_app(config=None, rates_service=None, neo_service=None):
    app = Flask(__name__)
    app.config.update(
        CACHE_PATH=str(Path(__file__).resolve().parent.parent / "data" / "cache.json"),
        NASA_API_KEY=os.environ.get("NASA_API_KEY", "DEMO_KEY"),
    )
    if config:
        app.config.update(config)
    store, messages = JsonCache(app.config["CACHE_PATH"]), Messages()
    app.extensions["rates"] = rates_service or RatesService(BnmProvider(), store, messages)
    app.extensions["neo"] = neo_service or NeoService(
        NasaNeoProvider(api_key=app.config["NASA_API_KEY"]), store, messages)
    app.register_blueprint(bp)
    return app
