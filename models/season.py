"""
This module contains the User class for dynamodb processes
"""

import re
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

from models import dynamodb_resource, LEAGUE_TABLE
from .errors import ItemAlreadyExistsError, ItemNotFoundError


class Season:
    table = dynamodb_resource.Table(LEAGUE_TABLE)

    @staticmethod
    def generate_uuid():
        return str(uuid.uuid1())

    @staticmethod
    def generate_uuid_from_text(text):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, text))

    @classmethod
    def create(cls, season_name, year):
        try:
            season_id = re.sub(
                r"[^a-zA-Z0-9-]+", "", season_name.lower().replace(" ", "-")
            )
            season_id = f"{season_id}-{year}"
            item = {
                "PK": f"SEASON#{season_id}",
                "SK": f"SEASON#{season_id}",
                "name": season_name,
                "year": year,
                "champion_id": "UNDEFINED",
                "GSI1PK": f"SEASON",
                "GSI1SK": f"YEAR#{year}#NAME#{season_name}",
            }
            cls.table.put_item(
                Item=item, ConditionExpression="attribute_not_exists(PK)"
            )
            return item
        except (
            cls.table.meta.client.exceptions.ConditionalCheckFailedException
        ) as error:
            raise ItemAlreadyExistsError(
                f"Season name {season_name} for year {year} already exists"
            ) from error

    @classmethod
    def get_by_id(cls, season_id):
        response = cls.table.query(
            KeyConditionExpression=Key("PK").eq(f"SEASON#{season_id}")
        )
        return response["Items"]

    @classmethod
    def get_all(cls):
        response = cls.table.query(
            IndexName="GSI1", KeyConditionExpression=Key("GSI1PK").eq("SEASON")
        )
        return response["Items"]

    @classmethod
    def get_by_year(cls, year):
        response = cls.table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq("SEASON")
            & Key("GSI1SK").begins_with(f"YEAR#{year}"),
        )
        return response["Items"]

    @classmethod
    def update(cls, season_id, name, year, champion_id):
        try:
            if champion_id:
                response = cls.table.query(
                    KeyConditionExpression=Key("PK").eq(f"TEAM#{champion_id}")
                )
                if not response["Items"]:
                    raise ItemNotFoundError("Champion team id does not exist")

            update_expression = (
                "SET #n = :name, #y = :year, #c = :champion_id, #gsi1sk = :gsi1sk"
            )
            expression_attribute_values = {
                ":name": name,
                ":year": year,
                ":champion_id": champion_id,
                ":gsi1sk": f"YEAR#{year}#NAME#{name}",
            }
            expression_attribute_names = {
                "#n": "name",
                "#y": "year",
                "#c": "champion_id",
                "#gsi1sk": "GSI1SK",
            }

            response = cls.table.update_item(
                Key={"PK": f"SEASON#{season_id}", "SK": f"SEASON#{season_id}"},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names,
                ConditionExpression="attribute_exists(PK)",
                ReturnValues="ALL_NEW",
            )
            return response.get("Attributes")
        except (
            cls.table.meta.client.exceptions.ConditionalCheckFailedException
        ) as error:
            raise ItemNotFoundError("Not Found") from error

    @classmethod
    def delete_by_id(cls, season_id):
        response = cls.table.delete_item(
            Key={"PK": f"SEASON#{season_id}", "SK": f"SEASON#{season_id}"},
            ReturnValues="ALL_OLD",
        )
        return response

    # SEASONS - TEAMS
    @classmethod
    def get_teams_by_season_id(cls, season_id):
        response = cls.table.query(
            KeyConditionExpression=Key("PK").eq(f"SEASON#{season_id}")
            & Key("SK").begins_with("TEAM#")
        )
        return response["Items"]

    @classmethod
    def register_team(cls, season_id, team_id):
        try:
            # season and team validation
            response = cls.table.meta.client.batch_get_item(
                RequestItems={
                    cls.table.name: {
                        "Keys": [
                            {"PK": f"SEASON#{season_id}", "SK": f"SEASON#{season_id}"},
                            {"PK": f"TEAM#{team_id}", "SK": f"TEAM#{team_id}"},
                        ]
                    }
                }
            )
            items = response["Responses"][cls.table.name]
            if len(items) != 2:
                raise ItemNotFoundError("Invalid season / team")

            # team registration
            item = {
                "PK": f"SEASON#{season_id}",
                "SK": f"TEAM#{team_id}",
                "id": team_id,
                "name": items[1]["name"],
                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            cls.table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK) and attribute_not_exists(SK)",
            )
            return item
        except (
            cls.table.meta.client.exceptions.ConditionalCheckFailedException
        ) as error:
            raise ItemAlreadyExistsError(
                "Team is already registered in season"
            ) from error

    @classmethod
    def delete_by_season_and_team_id(cls, season_id, team_id):
        response = cls.table.delete_item(
            Key={"PK": f"SEASON#{season_id}", "SK": f"TEAM#{team_id}"},
            ReturnValues="ALL_OLD",
        )
        return response

    # SEASONS - MATCHES
    @classmethod
    def register_match(
        cls, season_id, team1_id, team2_id, team1_goals, team2_goals, date
    ):
        try:
            if team1_id == team2_id:
                raise ItemNotFoundError("Match teams cannot be the same")

            response = cls.table.meta.client.batch_get_item(
                RequestItems={
                    cls.table.name: {
                        "Keys": [
                            {"PK": f"SEASON#{season_id}", "SK": f"TEAM#{team1_id}"},
                            {"PK": f"SEASON#{season_id}", "SK": f"TEAM#{team2_id}"},
                        ]
                    }
                }
            )
            items = response["Responses"][cls.table.name]
            if len(items) != 2:
                raise ItemNotFoundError("Teams not registed in season")

            match_id = cls.generate_uuid_from_text(f"{team1_id}#{team2_id}")
            reverse_match_id = cls.generate_uuid_from_text(f"{team2_id}#{team1_id}")

            response = cls.table.meta.client.batch_get_item(
                RequestItems={
                    cls.table.name: {
                        "Keys": [
                            {"PK": f"SEASON#{season_id}", "SK": f"MATCH#{match_id}"},
                            {
                                "PK": f"SEASON#{season_id}",
                                "SK": f"MATCH#{reverse_match_id}",
                            },
                        ]
                    }
                }
            )
            items = response["Responses"][cls.table.name]
            if len(items) > 0:
                raise ItemAlreadyExistsError("Match between teams already created")

            item = {
                "PK": f"SEASON#{season_id}",
                "SK": f"MATCH#{match_id}",
                "id": match_id,
                "team1_id": team1_id,
                "team2_id": team2_id,
                "team1_goals": team1_goals,
                "team2_goals": team2_goals,
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            cls.table.put_item(
                Item=item, ConditionExpression="attribute_not_exists(PK)"
            )
            return item
        except (
            cls.table.meta.client.exceptions.ConditionalCheckFailedException
        ) as error:
            raise ItemNotFoundError("Season not found") from error

    @classmethod
    def get_matches_by_season_id(cls, season_id):
        response = cls.table.query(
            KeyConditionExpression=Key("PK").eq(f"SEASON#{season_id}")
            & Key("SK").begins_with("MATCH#")
        )
        return response["Items"]

    @classmethod
    def get_by_season_and_match_id(cls, season_id, match_id):
        response = cls.table.query(
            KeyConditionExpression=Key("PK").eq(f"SEASON#{season_id}")
            & Key("SK").eq(f"MATCH#{match_id}")
        )
        return response["Items"]

    @classmethod
    def delete_by_season_and_match_id(cls, season_id, match_id):
        response = cls.table.delete_item(
            Key={"PK": f"SEASON#{season_id}", "SK": f"MATCH#{match_id}"},
            ReturnValues="ALL_OLD",
        )
        return response
