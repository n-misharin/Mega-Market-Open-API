import datetime
import uuid
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from app.database import db


class ProductType:
    CATEGORY = 'CATEGORY'
    OFFER = 'OFFER'


PRODUCTS_TYPES = [ProductType.CATEGORY, ProductType.OFFER]


# class ProductType(db.Model):
#     __tablename__ = 'types'
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String, nullable=False)
#
#     __TYPES = []
#
#     @staticmethod
#     def select_all() -> List:
#         if len(ProductType.__TYPES) == 0:
#             for p_type in ProductType.query.all():
#                 ProductType.__TYPES.append(p_type)
#         return ProductType.__TYPES[:]


class ValidationException(Exception):
    pass


class ShopUnitImport:
    def __init__(
            self,
            id: str,
            name: str,
            type: str,
            parentId: Optional[str] = None,
            price: Optional[int] = None
    ):
        self.id = id

        if name is None:
            raise ValidationException()

        self.name = name
        self.parentId = parentId

        if type not in PRODUCTS_TYPES:
            raise ValidationException()

        if type == ProductType.OFFER and (price is None or price < 0):
            raise ValidationException()

        if type == ProductType.CATEGORY and price is not None:
            raise ValidationException()

        self.price = int(price) if price is not None else None
        self.type = type


class ShopUnitImportRequest:
    def __init__(
            self,
            items: List,
            updateDate: str
    ):
        self.items = [ShopUnitImport(**item) for item in items]
        self.updateDate = datetime.datetime.strptime(
            updateDate,
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )

    def to_products_list(self):
        return [
            Product(
                id=item.id,
                name=item.name,
                parent_id=item.parentId,
                price=item.price,
                type_id=PRODUCTS_TYPES.index(item.type) + 1,
                update_date=self.updateDate
            ) for item in self.items
        ]


class ShopUnit(ShopUnitImport):
    def __init__(
            self,
            id: str,
            name: str,
            type_id: int,
            update_date: datetime.datetime,
            parent_id: Optional[str] = None,
            price: Optional[int] = None
    ):
        super().__init__(
            id,
            name,
            PRODUCTS_TYPES[type_id - 1],
            parent_id,
            price
        )
        self.date = update_date
        self.price = int(price) if price is not None else 0
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
                res[key] = val.isoformat(timespec='milliseconds')[:-6] + 'Z'
            else:
                res[key] = val
        return res


class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    parent_id = db.Column(
        db.String,
        db.ForeignKey(f'{__tablename__}.id'),
        default=None,
        nullable=True,
    )
    children = relationship(
        "Product",
        back_populates="parent",
        cascade="all, delete"
    )
    parent = relationship(
        "Product",
        back_populates="children",
        remote_side=[id]
    )
    price = db.Column(db.Integer)
    type_id = db.Column(
        db.Integer,
        # db.ForeignKey(f'{ProductType.__tablename__}.id'),
        nullable=False
    )
    # type = relationship(ProductType.__name__)
    update_date = db.Column(db.DateTime(), nullable=False)

    @staticmethod
    def select(id):
        topq = db.session.query(Product).\
            filter(Product.id == id).\
            cte('cte', recursive=True)

        botq = db.session.query(Product).\
            join(topq, Product.parent_id == topq.c.id)

        return db.session.query(Product).\
            select_entity_from(topq.union(botq)).all()

    @staticmethod
    def __update(product):
        db.session.query(Product).\
            filter(Product.id == product.id).\
            update(product.to_dict(only=(
                'price',
                'update_date',
                'name',
                'parent_id'
            )))
        db.session.commit()

    @staticmethod
    def add_or_update(products: List):
        if len(products) != len(set(products)):
            raise Exception

        new_date = products[0].update_date
        inserts = []

        for product in products:
            try:
                p_copy = db.session.query(Product).\
                    filter(Product.id == product.id).\
                    one()
                if p_copy.type_id != product.type_id:
                    raise Exception()
            except NoResultFound as nrf:
                inserts.append(product)

        for product in inserts:
            db.session.add(product)
        db.session.commit()

        used = {p.id: False for p in products}
        products = set(products)

        # bfs
        while len(products) != 0:
            product = products.pop()
            used[product.id] = True

            if product.parent_id is not None and \
                    product.parent_id not in used.keys():
                used[product.parent_id] = False
                p = db.session.query(Product).\
                    filter(Product.id == product.parent_id).\
                    first()
                products.add(p)

            db.session.query(Product).\
                filter(Product.id == product.id).\
                update({
                    'update_date': new_date
                })
            db.session.commit()

    @staticmethod
    def delete(id: str):
        product = Product.query.filter_by(id=id).first_or_404()
        db.session.delete(product)
        db.session.commit()
