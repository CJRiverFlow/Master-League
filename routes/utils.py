"""
This module have utility functions for routes package
"""
from decimal import Decimal
from botocore.exceptions import ClientError
from functools import wraps
from flask import jsonify
from http import HTTPStatus

from .logger import get_logger
from models.errors import ItemAlreadyExistsError, ItemNotFoundError

logger = get_logger()


def handle_decimal_type(key: str):
    if isinstance(key, Decimal):
        if key % 1 == 0:
            return int(key)
        else:
            return float(key)
    return key


def format_dynamodb_item(item: dict, ignore_pk_index=False):
    item = {
        key: handle_decimal_type(value)
        for key, value in item.items()
        if not (key.startswith("GSI") or key.endswith("SK"))
    }
    if not ignore_pk_index:
        item["id"] = item["PK"].split("#")[1]
    item.pop("PK")
    return item


def handle_dynamodb_error(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            response = function(*args, **kwargs)
            return response
        except ClientError as error:
            logger.error(str(error))
            error_code = error.response["Error"]["Code"]
            if error_code == "ValidationException":
                return jsonify({"message": "Validation failed"}), HTTPStatus.BAD_REQUEST
            elif error_code == "ResourceNotFoundException":
                return jsonify({"message": "Resource not found"}), HTTPStatus.NOT_FOUND
            elif error_code == "AccessDeniedException":
                return jsonify({"message": "Access denied"}), HTTPStatus.UNAUTHORIZED
            else:
                return (
                    jsonify({"message": "Failed to complete data operation"}),
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                )
        except ItemNotFoundError as error:
            logger.error(str(error))
            return jsonify({"message": str(error)}), HTTPStatus.NOT_FOUND
        except ItemAlreadyExistsError as error:
            logger.error(str(error))
            return jsonify({"message": str(error)}), HTTPStatus.CONFLICT

    return wrapper
