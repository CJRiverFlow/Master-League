import os
import boto3

dynamodb_resource = boto3.resource("dynamodb")

if os.environ.get("IS_OFFLINE"):
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name="localhost", endpoint_url="http://localhost:8000"
    )

LEAGUE_TABLE = os.environ["LEAGUE_TABLE"]
