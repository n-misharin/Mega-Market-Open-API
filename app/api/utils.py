import datetime
import uuid
from typing import Optional, List


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
    def get_type_by_id(id: int):
        return ProductType.get_types()[id - 1]


def is_cor_uuid(_uuid: str) -> bool:
    """ Проверяет uuid-строку на корректность. """
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
        date,
        '%Y-%m-%dT%H:%M:%S.%fZ'
    )


class ValidationException(Exception):
    pass


class ShopUnitImport:
    def __init__(self, id: str, name: str, type: str,
                 parentId: Optional[str] = None,
                 price: Optional[int] = None):

        self.id = id

        if name is None:
            raise ValidationException()

        self.name = name
        self.parentId = parentId

        if type not in ProductType.get_types():
            raise ValidationException()

        if type == ProductType.OFFER and (price is None or price < 0):
            raise ValidationException()

        if type == ProductType.CATEGORY and price is not None:
            raise ValidationException()

        self.price = int(price) if price is not None else None
        self.type = type


class ShopUnitStatisticUnit(ShopUnitImport):
    def __init__(self, id: str, name: str, type_id: int,
                 update_date: datetime.datetime, parent_id: Optional[str] = None,
                 price: Optional[int] = None):
        super().__init__(id, name, ProductType.get_type_by_id(type_id),
                         parent_id, price)
        self.date = update_date


class ShopUnitStatisticResponse:
    def __init__(self, items: List[ShopUnitStatisticUnit]):
        self.items = items


class ShopUnitImportRequest:
    def __init__(self, items: List, updateDate: str):
        self.items = [ShopUnitImport(**item) for item in items]
        self.updateDate = parse_iso(updateDate)


class ShopUnit(ShopUnitStatisticUnit):
    def __init__(self, id: str, name: str, type_id: int,
                 update_date: datetime.datetime,
                 parent_id: Optional[str] = None,
                 price: Optional[int] = None):

        super().__init__(id, name, type_id, update_date, parent_id, price)
        self.children = [] if self.type == ProductType.CATEGORY else None

    def add_child(self, child):
        if self.children is not None:
            self.children.append(child)

    def calc_price(self):
        if self.children is not None and self.type == ProductType.CATEGORY:
            res_count, res_price = 0, 0
            for child in self.children:
                child.calc_price()
                count, price = child.calc_price()
                res_price += price
                res_count += count

            self.price = res_price // res_count

            return res_count, res_price

        return 1, self.price

    def to_dict(self):
        res = dict()
        for key, val in self.__dict__.items():
            if type(val) == list:
                res[key] = [el.to_dict() for el in val]
            elif type(val) == datetime.datetime:
                res[key] = date_to_iso(val)
            else:
                res[key] = val
        return res
