"""
This file contains the api routes for team endpoints
"""

from decimal import Decimal
from flask import Blueprint, request, jsonify
from http import HTTPStatus
from marshmallow import Schema, fields, ValidationError

from models.team import Team
from .utils import handle_dynamodb_error, format_dynamodb_item

teams_blueprint = Blueprint("teams", __name__)


class TeamsSchema(Schema):
    name = fields.Str(required=True)
    established_year = fields.Int(required=True)
    location = fields.Str(required=True)


@teams_blueprint.route("/teams", methods=["POST"])
@handle_dynamodb_error
def create_team():
    data = request.get_json()
    try:
        validated_data = TeamsSchema().load(data)
    except ValidationError as error:
        return jsonify(error.messages), HTTPStatus.BAD_REQUEST
    team = Team.create(
        validated_data["name"],
        validated_data["established_year"],
        validated_data["location"],
    )
    team = format_dynamodb_item(team)
    return jsonify(team), HTTPStatus.CREATED


@teams_blueprint.route("/teams/<string:team_id>", methods=["GET"])
@handle_dynamodb_error
def get_team_by_id(team_id):
    teams = Team.get_by_id(team_id)
    if not teams:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    teams = format_dynamodb_item(teams[0])
    return jsonify(teams), HTTPStatus.ACCEPTED


@teams_blueprint.route("/teams", methods=["GET"])
@handle_dynamodb_error
def get_teams():
    results = Team.get_all()
    formatted_teams = []
    for team in results:
        team = format_dynamodb_item(team)
        formatted_teams.append(team)
    return jsonify({"teams": formatted_teams}), HTTPStatus.OK


@teams_blueprint.route("/teams/<string:team_id>", methods=["PUT"])
@handle_dynamodb_error
def update_team(team_id):
    data = request.get_json()
    try:
        validated_data = TeamsSchema().load(data)
    except ValidationError as error:
        return jsonify(error.messages), HTTPStatus.BAD_REQUEST
    team = Team.update(
        team_id,
        validated_data["name"],
        validated_data["established_year"],
        validated_data["location"],
    )
    team = format_dynamodb_item(team)
    return jsonify(team), HTTPStatus.OK


@teams_blueprint.route("/teams/<string:team_id>", methods=["DELETE"])
@handle_dynamodb_error
def delete_team_by_id(team_id):
    response = Team.delete_by_id(team_id)
    if response.get("Attributes") is None:
        return jsonify({"message": HTTPStatus.NOT_FOUND.phrase}), HTTPStatus.NOT_FOUND
    return "", HTTPStatus.NO_CONTENT
