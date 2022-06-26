import datetime
from typing import List, Optional

from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin
from app.api.utils import ProductType, is_cor_uuid, ValidationException, parse_iso, date_to_iso
from app.database import db


class Statistic(db.Model):
    """
    Model for table 'statistics'. Table contains change statistics
    products whose contains in table 'products'.
    """
    __tablename__ = 'statistics'

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.String, db.ForeignKey(f'products.id'), nullable=False)

    product = relationship(
        "Product", back_populates="statistic", cascade="all,delete")

    update_date = db.Column(db.DateTime(), nullable=False)

    price = db.Column(db.Integer, nullable=False)

    count = db.Column(db.Integer, nullable=False)

    name = db.Column(db.String, nullable=False)

    parent_id = db.Column(db.String, nullable=True)

    type_id = db.Column(db.Integer, nullable=False)

    @staticmethod
    def get(product_id, dateStart: Optional[datetime.datetime] = None,
            dateEnd: Optional[datetime.datetime] = None) -> dict:
        """
        Return statistics for [dateStart, dateEnd). If dateStart or dateEnd
        is None, then returning statistics from all period.
        :param dateStart: date of begin period
        :param dateEnd: date of end period
        :param product_id: id of searching element
        :type product_id: type of Product.id
        :return: {
            items=List[{
                id: Statistic.product_id,
                name: str,
                date: da
                TODO:
            }]
        }
        """
        if dateStart is None or dateEnd is None:
            res = db.session.query(Statistic). \
                filter(Statistic.product_id == product_id).all()
        else:
            res = db.session.query(Statistic).filter(
                Statistic.product_id == product_id,
                Statistic.update_date >= dateStart,
                Statistic.update_date < dateEnd).all()

        return {
            "items": [dict(
                id=el.parent_id, name=el.name,
                date=date_to_iso(el.update_date),
                parentId=el.parent_id,
                price=None if el.count == 0 else el.price // el.count,
                type=ProductType.get_type(el.type_id)
            ) for el in res]
        }


class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'

    id = db.Column(db.String, primary_key=True)

    name = db.Column(db.String, nullable=False)

    parent_id = db.Column(
        db.String, db.ForeignKey(f'{__tablename__}.id'),
        default=None, nullable=True, )

    statistic = relationship(
        "Statistic", back_populates="product", cascade="all,delete")

    children = relationship(
        "Product", back_populates="parent", cascade="all, delete")

    parent = relationship(
        "Product", back_populates="children", remote_side=[id])

    price = db.Column(db.Integer, nullable=False)

    count = db.Column(db.Integer, nullable=False)

    type_id = db.Column(db.Integer, nullable=False)

    update_date = db.Column(db.DateTime(), nullable=False)

    def update_dict(self) -> dict:
        """
        Converts this object to dict. Result dict contains only fields whose
        may be updated:
            name, price, count, update_date, parent_id.
        """
        # TODO: remove this method and crete method update
        return self.to_dict(
            only=('name', 'price', 'count', 'update_date', 'parent_id'))

    def get_statistic(self):
        """ Convert this object ot Statistic object. """
        return Statistic(
            product_id=self.id, update_date=self.update_date,
            name=self.name, price=self.price, type_id=self.type_id,
            parent_id=self.parent_id, count=self.count)

    @staticmethod
    def write_statistics(date):
        """ Inserts Products where update_date == date to table 'statistics'. """
        updated = db.session.query(Product). \
            filter(Product.update_date == date).all()
        db.session.add_all([product.get_statistic() for product in updated])
        db.session.commit()

    @staticmethod
    def get_from_period(start_date: datetime.datetime,
                        end_date: datetime.datetime) -> dict:
        """
        Returns items where update_date in [start_date, end_date] and type == 'OFFER'.
        TODO: returns object of ShopUnitStatisticUnit
        :return dict : {
            'items': List[dict]
        }
        """
        result = db.session.query(Product).filter(
            Product.update_date >= start_date,
            Product.update_date <= end_date,
            Product.type_id == ProductType.get_id(ProductType.OFFER)
        ).all()
        return {
            "items": [dict(
                id=p.id, name=p.name, date=p.update_date, parentId=p.parent_id,
                price=p.price, type=ProductType.get_type(p.type_id)
            ) for p in result]
        }


class ShopUnitImport:
    """
    Class for validate imports data.

    Attributes:
    -----------
    id: str (uuid)
        primary key in table 'products'
    name: str
        offer/category name
    parent_id: str
        foreign key in table 'products
    price: int
    type_id: int
        type id from utils.ProductTypes
    """
    def __init__(self, id: str, name: str, type: str,
                 price: Optional[int] = None,
                 parentId: Optional[str] = None):
        """
        Validate and set attributes for object. Validate parameters:
            id -- must be uuid;
            parentId -- must be uuid;
            type -- must be in ['OFFER', 'CATEGORY'];
            price -- must be None if type == 'CATEGORY' else must be int;
            name -- must be not None.
        If can not validate raised ValidationException.
        """
        if not is_cor_uuid(id):
            raise ValidationException(f'Not correct uuid "{id}"')

        if parentId is not None and not is_cor_uuid(parentId):
            raise ValidationException('parentId must be None or uuid')

        if name is None:
            raise ValidationException(f'Name must be not None')

        if type not in ProductType.get_types():
            raise ValidationException(f'Type must be in {ProductType.get_types()}')

        if type == ProductType.CATEGORY and price is not None:
            raise ValidationException(f'CATEGORY must not has price')

        if type == ProductType.OFFER and price is None:
            raise ValidationException(f'OFFER must have price')

        self.id = id
        self.name = name
        self.type_id = ProductType.get_id(type)
        self.parent_id = parentId

        try:
            self.price = int(price) if price is not None else 0
        except Exception:
            raise ValidationException(f'Price must be "int"')

    def to_dict(self):
        return self.__dict__


class ShopUnitImportRequest:
    """
    Class for validate import data:

    Attributes:
    ----------
    items: List[ShopUnitImport]
        ShopUnitImport elements for updating date
    update_date: datetime.datetime
        updating time
    """
    def __init__(self, items: List, updateDate: str):
        """
        Converts items to List[ShopUnitImport] and updateDate to datetime.datetime.
        If can not validate raised ValidationException.
        """
        try:
            self.items = [ShopUnitImport(**item) for item in items]
            self.update_date = parse_iso(updateDate)
        except Exception:
            raise ValidationException('Datetime not has ISO format')

    def get_products_list(self) -> List[Product]:
        """ Converts self to List[Product] and returns him. """
        return [Product(
            update_date=self.update_date, **item.to_dict()
        ) for item in self.items]


class NodeExistException(Exception):
    pass


class NodeNotFoundException(Exception):
    pass


class NodeTypeError(Exception):
    pass


class ProductTree:
    """ Class for working with Product model as with tree. """

    @staticmethod
    def get_subtree(node_id):
        """ Returns nested dict like subtree for node where root is node_id. """
        nodes_list = ProductTree.__subtree_query(node_id).all()

        res_nodes = dict()
        for node in nodes_list:
            res_nodes[node.id] = dict(
                id=node.id, name=node.name, parentId=node.parent_id,
                date=date_to_iso(node.update_date), type=ProductType.get_type(node.type_id))

            price = None
            if node.count != 0:
                if node.type_id == ProductType.get_id(ProductType.OFFER):
                    price = node.price
                else:
                    price = node.price // node.count

            res_nodes[node.id]['price'] = price

            res_nodes[node.id]['children'] = [] \
                if node.type_id == ProductType.get_id(ProductType.CATEGORY) else None

        result_dict = res_nodes.pop(node_id)
        while len(res_nodes) != 0:
            x = res_nodes.popitem()[1]
            if x['parentId'] == node_id:
                result_dict['children'].append(x)
            else:
                res_nodes[x['parentId']]['children'].append(x)

        return result_dict

    @staticmethod
    def has_node(node_id: str) -> bool:
        return ProductTree.get_node(node_id) is not None

    @staticmethod
    def get_node(node_id: str) -> Product or None:
        return db.session.query(Product).filter(Product.id == node_id).one_or_none()

    @staticmethod
    def __add_nodes(products: List[Product]) -> None:
        """
        Adds products in database table and updates all nodes whose contains the way
        from node to root. If product already in table then raised database exception.

        WARNING: If exception is raised then changes not be committed.
        """
        for product in products:
            if product.type_id == ProductType.get_id(ProductType.OFFER):
                product.count = 1
            else:
                product.count = 0
                product.price = 0

        db.session.add_all(products)

        for product in products:
            price_delta = product.price
            count_delta = 1
            if product.type_id == ProductType.get_id(ProductType.CATEGORY):
                count_delta = 0
                price_delta = 0

            ProductTree.__update_from_this_to_root(
                product.parent_id, product.update_date, price_delta, count_delta)
        db.session.commit()

    @staticmethod
    def __from_this_to_root_query(node_id: str):
        #  TODO: like __subtree_query
        top_query = db.session.query(Product). \
            filter(Product.id == node_id). \
            cte('cte', recursive=True)

        bot_query = db.session.query(Product). \
            join(top_query, Product.id == top_query.c.parent_id)

        return db.session.query(Product). \
            select_entity_from(top_query.union(bot_query))

    @staticmethod
    def __subtree_query(node_id: str):
        #  TODO: like __from_this_to_root_query
        top_query = db.session.query(Product). \
            filter(Product.id == node_id). \
            cte('cte', recursive=True)

        bot_query = db.session.query(Product). \
            join(top_query, Product.parent_id == top_query.c.id)

        return db.session.query(Product). \
            select_entity_from(top_query.union(bot_query))

    @staticmethod
    def __update_from_this_to_root(node_id, new_date=None, price_delta=0,
                                   count_delta=0) -> None:
        """
        Updates all nodes in database whose contains the way from node to root.

        :param node_id: str
            product id in database
        :param new_date: datetime.datetime or None
            for all parents set update_date = new_date. If None then not update parents
        :param price_delta:
            for all parents set price = price + price_delta
        :param count_delta:
            for all parents set count = count + count_delta
        :return: None
        """
        if not ProductTree.has_node(node_id):
            return

        nodes = ProductTree.__from_this_to_root_query(node_id). \
            with_for_update().all()

        update_dict = dict(
            price=Product.price + price_delta,
            count=Product.count + count_delta)

        if new_date is not None:
            update_dict['update_date'] = new_date

        db.session.query(Product). \
            filter(Product.id.in_([el.id for el in nodes])). \
            update(update_dict)
        # db.session.commit()

    @staticmethod
    def __update_nodes(products: List[Product]) -> None:
        """
        Updates products in database table and updates all nodes whose contains the way
        from node to root. If product not in table then raised database exception.

        WARNING: If exception is raised then changes not be committed.
        """
        for product in products:
            old_node = ProductTree.get_node(product.id)

            if product.type_id != old_node.type_id:
                raise NodeTypeError(f'Can not change the node type')

            """ Если поменялся родитель, то нужно перевесить вершину. """
            if product.parent_id != old_node.parent_id:

                ProductTree.__update_from_this_to_root(
                    old_node.parent_id, product.update_date,
                    -old_node.price, -old_node.count)

                if product.type_id == ProductType.get_id(ProductType.CATEGORY):
                    ProductTree.__update_from_this_to_root(
                        product.parent_id, product.update_date,
                        old_node.price, old_node.count)
                else:
                    ProductTree.__update_from_this_to_root(
                        product.parent_id, product.update_date,
                        product.price, 1)
            else:
                if product.type_id == ProductType.get_id(ProductType.CATEGORY):
                    ProductTree.__update_from_this_to_root(
                        product.parent_id, product.update_date,
                        0, 0)
                else:
                    ProductTree.__update_from_this_to_root(
                        product.parent_id, product.update_date,
                        product.price - old_node.price, 0)

            update_dict = product.update_dict()
            if product.type_id == ProductType.get_id(ProductType.CATEGORY):
                update_dict.pop('price')

            update_dict['count'] = ProductTree.get_node(product.id).count

            db.session.query(Product).filter(Product.id == product.id). \
                update(update_dict)
            # db.session.add(ProductTree.get_node(product.id).get_statistic())
        db.session.commit()

    @staticmethod
    def remove_node(node_id) -> None:
        """
        Cascade delete product where product.id == node_id from 'products'.
        Deletes all descendants from 'products' and all entities from 'statistics'
        whose product_id depended on them.
        """
        if not ProductTree.has_node(node_id):
            raise NodeExistException(f'Database not contains node {node_id}')

        node = ProductTree.get_node(node_id)

        ProductTree.__update_from_this_to_root(
            node.parent_id, price_delta=-node.price, count_delta=-node.count)

        db.session.delete(ProductTree.get_node(node_id))
        db.session.commit()

    @staticmethod
    def add_or_update_all(products: List[Product]) -> None:
        """
        Inserts or updates all products in the database, and also updates all the
        ancestors of these nodes.
        """
        updates = []
        inserts = []
        for product in products:
            if not ProductTree.has_node(product.id):
                inserts.append(product)
            else:
                updates.append(product)

        ProductTree.__add_nodes(inserts)
        ProductTree.__update_nodes(updates)
