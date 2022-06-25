import datetime
import uuid
from typing import List


class ProductType:
    CATEGORY = 'CATEGORY'
    OFFER = 'OFFER'

    @staticmethod
    def get_id(str_type: str) -> int:
        return ProductType.get_types().index(str_type) + 1

    @staticmethod
    def get_types() -> List[str]:
        return [ProductType.CATEGORY, ProductType.OFFER]

    @staticmethod
    def get_type(id: int):
        return ProductType.get_types()[id - 1]


def is_cor_uuid(_uuid: str) -> bool:
    """ Проверяет uuid-строку на корректность. """
    # return True
    # TODO: delete comments
    try:
        u = uuid.UUID(_uuid)
        return True
    except TypeError:
        return False
    except ValueError:
        return False


def date_to_iso(date: datetime.datetime) -> str:
    return date.isoformat(timespec='milliseconds') + 'Z'


def parse_iso(date: str) -> datetime.datetime:
    return datetime.datetime.strptime(
        date, '%Y-%m-%dT%H:%M:%S.%fZ')


class ValidationException(Exception):
    pass


class ItemNotFoundException(Exception):
    pass
