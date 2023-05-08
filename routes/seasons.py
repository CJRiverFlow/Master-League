"""
This file contains the api reoutes for season endpoints
"""

from flask import Blueprint, request, jsonify
from http import HTTPStatus
from marshmallow import Schema, fields, ValidationError

from models.season import Season
from .utils import format_dynamodb_item, handle_dynamodb_error

seasons_blueprint = Blueprint("seasons", __name__)


class SeasonSchema(Schema):
    name = fields.Str(required=True)
    year = fields.Int(required=True)
    champion_id = fields.Str(missing="UNDEFINED")


class TeamRegistrationSchema(Schema):
    team_id = fields.Str(required=True)


class MatchRegistrationSchema(Schema):
    team1_id = fields.Str(required=True)
    team2_id = fields.Str(required=True)
    team1_goals = fields.Int(required=True)
    team2_goals = fields.Int(required=True)
    date = fields.DateTime(required=True)

    class Meta:
        ordered = True


@seasons_blueprint.route("/seasons", methods=["POST"])
@handle_dynamodb_error
def create_season():
    data = request.get_json()
    try:
        validated_data = SeasonSchema().load(data)
    except ValidationError as error:
        return jsonify(error.messages), HTTPStatus.BAD_REQUEST
    season = Season.create(validated_data["name"], validated_data["year"])
    season = format_dynamodb_item(season)
    return jsonify(season), HTTPStatus.CREATED


@seasons_blueprint.route("/seasons/<string:season_id>", methods=["GET"])
@handle_dynamodb_error
def get_season_by_id(season_id):
    seasons = Season.get_by_id(season_id)
    if not seasons:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    seasons = format_dynamodb_item(seasons[0])
    return jsonify(seasons), HTTPStatus.ACCEPTED


@seasons_blueprint.route("/seasons", methods=["GET"])
@handle_dynamodb_error
def get_seasons():
    year = request.args.get("year")
    if year is not None:
        if not year.isdigit():
            return (
                jsonify({"message": "Invalid year parameter"}),
                HTTPStatus.BAD_REQUEST,
            )
        results = Season.get_by_year(year)
    else:
        results = Season.get_all()
    formatted_seasons = []
    for season in results:
        season = format_dynamodb_item(season)
        formatted_seasons.append(season)
    return jsonify({"seasons": formatted_seasons}), HTTPStatus.OK


@seasons_blueprint.route("/seasons/<string:season_id>", methods=["PUT"])
@handle_dynamodb_error
def update_season(season_id):
    data = request.get_json()
    try:
        validated_data = SeasonSchema().load(data)
    except ValidationError as error:
        return jsonify(error.messages), HTTPStatus.BAD_REQUEST
    season = Season.update(
        season_id,
        validated_data["name"],
        validated_data["year"],
        validated_data["champion_id"],
    )
    print(season)
    season = format_dynamodb_item(season)
    return jsonify(season), HTTPStatus.OK


@seasons_blueprint.route("/seasons/<string:season_id>", methods=["DELETE"])
@handle_dynamodb_error
def delete_season_by_id(season_id):
    response = Season.delete_by_id(season_id)
    if response.get("Attributes") is None:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    return "", HTTPStatus.NO_CONTENT


# SEASON - TEAMS
@seasons_blueprint.route("/seasons/<string:season_id>/teams", methods=["POST"])
@handle_dynamodb_error
def register_season_team(season_id):
    data = request.get_json()
    try:
        validated_data = TeamRegistrationSchema().load(data)
    except ValidationError as error:
        return jsonify(error.messages), HTTPStatus.BAD_REQUEST
    team_id = validated_data["team_id"]
    registration = Season.register_team(season_id, team_id)
    registration = format_dynamodb_item(registration, ignore_pk_index=True)
    return jsonify(registration), HTTPStatus.CREATED


@seasons_blueprint.route("/seasons/<string:season_id>/teams", methods=["GET"])
@handle_dynamodb_error
def get_teams_by_season_id(season_id):
    teams = Season.get_teams_by_season_id(season_id)
    teams = [format_dynamodb_item(item, ignore_pk_index=True) for item in teams]
    return jsonify({"teams": teams}), HTTPStatus.OK


@seasons_blueprint.route(
    "/seasons/<string:season_id>/teams/<string:team_id>", methods=["DELETE"]
)
@handle_dynamodb_error
def delete_by_season_and_team_id(season_id, team_id):
    response = Season.delete_by_season_and_team_id(season_id, team_id)
    if response.get("Attributes") is None:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    return "", HTTPStatus.NO_CONTENT


# SEASON - MATCHES
@seasons_blueprint.route("/seasons/<string:season_id>/matches", methods=["POST"])
@handle_dynamodb_error
def register_season_match(season_id):
    data = request.get_json()
    try:
        validated_data = MatchRegistrationSchema().load(data)
    except ValidationError as error:
        return jsonify(error.messages), HTTPStatus.BAD_REQUEST
    registration = Season.register_match(
        season_id,
        validated_data["team1_id"],
        validated_data["team2_id"],
        validated_data["team1_goals"],
        validated_data["team2_goals"],
        validated_data["date"],
    )
    registration = format_dynamodb_item(registration, ignore_pk_index=True)
    return jsonify(registration), HTTPStatus.CREATED


@seasons_blueprint.route("/seasons/<string:season_id>/matches", methods=["GET"])
@handle_dynamodb_error
def get_matches_by_season_id(season_id):
    matches = Season.get_matches_by_season_id(season_id)
    matches = [format_dynamodb_item(match, ignore_pk_index=True) for match in matches]
    return jsonify({"matches": matches}), HTTPStatus.OK


@seasons_blueprint.route(
    "/seasons/<string:season_id>/matches/<string:match_id>", methods=["GET"]
)
@handle_dynamodb_error
def get_by_season_and_match_id(season_id, match_id):
    season = Season.get_by_season_and_match_id(season_id, match_id)
    if not season:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    season = format_dynamodb_item(season[0], ignore_pk_index=True)
    return jsonify(season), HTTPStatus.OK


@seasons_blueprint.route(
    "/seasons/<string:season_id>/matches/<string:match_id>", methods=["DELETE"]
)
@handle_dynamodb_error
def delete_by_season_and_match_id(season_id, match_id):
    response = Season.delete_by_season_and_match_id(season_id, match_id)
    if response.get("Attributes") is None:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    return "", HTTPStatus.NO_CONTENT
