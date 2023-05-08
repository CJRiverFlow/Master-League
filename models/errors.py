"""
This file contains the custom error definitions
"""


class ItemAlreadyExistsError(Exception):
    """Exception raised when trying to create an item that already exists"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ItemNotFoundError(Exception):
    """Exception raised when trying to read or delete an item that does not exist"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
