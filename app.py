import dash
import dash_bootstrap_components as dbc
from flask import Flask
from flask_caching import Cache
import os

# https://www.bootstrapcdn.com/bootswatch/   ---- THIS IS A BOOTSTRAP STYLING PAGE
# https://hackerthemes.com/bootstrap-cheatsheet/  ---- THIS IS A BOOTSTRAP CHEATSHEET


# meta_tags are required for the app layout to be mobile responsive
color_mapping = {
    "ASOS": "rgb(27,158,119)",
    "SquareMeal": "rgb(217,95,2)",
    "Iceland": "rgb(117,112,179)",
    "Wasabi": "rgb(231,41,138)",
    "Visa": "rgb(27,158,119)",
    "Mastercard": "rgb(217,95,2)",
    "American Express": "rgb(231,41,138)",
    "Bink": "rgb(217,95,2)",
    "Barclays Mobile Banking": "rgb(117,112,179)",
}

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
)
cache = Cache(
    app.server,
    config={
        # try 'filesystem' if you don't want to setup redis
        "CACHE_TYPE": "RedisCache",
        "REDIS URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
    },
)


server = app.server
