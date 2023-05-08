"""
This module contains the Season class for dynamodb processes
"""

import re
import uuid
from boto3.dynamodb.conditions import Key

from models import dynamodb_resource, LEAGUE_TABLE
from .errors import ItemAlreadyExistsError, ItemNotFoundError


class Team:
    table = dynamodb_resource.Table(LEAGUE_TABLE)

    @staticmethod
    def generate_uuid():
        return str(uuid.uuid1())

    @classmethod
    def create(cls, team_name, established_year, location):
        try:
            team_id = re.sub(r"[^a-zA-Z0-9-]+", "", team_name.lower().replace(" ", "-"))
            item = {
                "PK": f"TEAM#{team_id}",
                "SK": f"TEAM#{team_id}",
                "name": team_name,
                "established_year": established_year,
                "location": location,
                "GSI1PK": f"TEAM",
                "GSI1SK": f"ESTABLISHED_YEAR#{established_year}",
            }
            cls.table.put_item(
                Item=item, ConditionExpression="attribute_not_exists(PK)"
            )
            return item
        except (
            cls.table.meta.client.exceptions.ConditionalCheckFailedException
        ) as error:
            raise ItemAlreadyExistsError(
                f"Team name {team_name} already exists"
            ) from error

    @classmethod
    def get_by_id(cls, team_id):
        response = cls.table.query(
            KeyConditionExpression=Key("PK").eq(f"TEAM#{team_id}")
        )
        return response["Items"]

    @classmethod
    def get_all(cls):
        response = cls.table.query(
            IndexName="GSI1", KeyConditionExpression=Key("GSI1PK").eq("TEAM")
        )
        return response["Items"]

    @classmethod
    def update(cls, team_id, name, established_year, location):
        try:
            update_expression = "SET #n = :name, #y = :established_year, #l = :location"
            expression_attribute_values = {
                ":name": name,
                ":established_year": established_year,
                ":location": location,
            }
            expression_attribute_names = {
                "#n": "name",
                "#y": "established_year",
                "#l": "location",
            }

            response = cls.table.update_item(
                Key={"PK": f"TEAM#{team_id}", "SK": f"TEAM#{team_id}"},
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
    def delete_by_id(cls, team_id):
        response = cls.table.delete_item(
            Key={"PK": f"TEAM#{team_id}", "SK": f"TEAM#{team_id}"},
            ReturnValues="ALL_OLD",
        )
        return response
