from typing import List

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin

from app.api.utils import ProductType
from app.database import db


class Statistic(db.Model):
    __tablename__ = 'statistics'

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.String, db.ForeignKey(f'products.id'), nullable=False)

    product = relationship(
        "Product", back_populates="statistic", cascade="all,delete")

    update_date = db.Column(db.DateTime(), nullable=False)

    price = db.Column(db.Integer, nullable=True)

    name = db.Column(db.String, nullable=False)

    @staticmethod
    def select_offers(date_start, date_end):
        return db.session.query(Product).join(Statistic).filter(
            Statistic.update_date >= date_start,
            Statistic.update_date <= date_end,
            Product.type_id == ProductType.get_id(ProductType.OFFER)
        ).distinct().all()


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

    price = db.Column(db.Integer)

    type_id = db.Column(db.Integer, nullable=False)

    update_date = db.Column(db.DateTime(), nullable=False)

    @staticmethod
    def is_contains(id):
        try:
            db.session.query(Product).filter(Product.id == id).one()
        except NoResultFound as nrf:
            return False

        return True

    @staticmethod
    def select_tree(id):
        topq = db.session.query(Product). \
            filter(Product.id == id). \
            cte('cte', recursive=True)

        botq = db.session.query(Product). \
            join(topq, Product.parent_id == topq.c.id)

        return db.session.query(Product). \
            select_entity_from(topq.union(botq)).all()

    @staticmethod
    def add_or_update_tree(products: List):
        if len(products) == 0:
            return

        new_date = products[0].update_date
        inserts = []

        for product in products:
            try:
                p_copy = db.session.query(Product). \
                    filter(Product.id == product.id).one()
                if p_copy.type_id != product.type_id:
                    """ Нельзя менять тип товара/категории (404). """
                    raise Exception
            except NoResultFound as nrf:
                """ Нет в базе данных. """
                inserts.append(product)

        for product in inserts:
            db.session.add(product)
        db.session.commit()

        """ 
        Предпроцессинг поиска в дереве: 
            used - посещенные вершины;
            из products делаем множество для быстрого поиска элемента.
        """
        used = {p.id: False for p in products}
        products = set(products[:])

        """ Поиск в дереве: идем вверх (к корню) по дереву. """
        while len(products) != 0:
            product = products.pop()
            used[product.id] = True

            if product.parent_id is not None and \
                    product.parent_id not in used.keys():

                used[product.parent_id] = False

                parent = db.session.query(Product). \
                    filter(Product.id == product.parent_id).first()

                products.add(parent)

            db.session.query(Product).filter(Product.id == product.id).\
                update({
                    'update_date': new_date,
                    'price': product.price,
                    'name': product.name,
                    'parent_id': product.parent_id
                })

            """ Сохранение старых данных. """
            db.session.add(Statistic(
                product_id=product.id,
                update_date=new_date,
                price=product.price,
                name=product.name
            ))

        db.session.commit()

    @staticmethod
    def delete_with_children(id):
        product = Product.query.filter_by(id=id).first_or_404()
        db.session.delete(product)
        db.session.commit()
