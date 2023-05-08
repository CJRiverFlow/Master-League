"""
Flask application and api routes
"""
from flask import Flask
from routes.seasons import seasons_blueprint
from routes.teams import teams_blueprint


app = Flask(__name__)

app.register_blueprint(seasons_blueprint, url_prefix="/api")
app.register_blueprint(teams_blueprint, url_prefix="/api")
