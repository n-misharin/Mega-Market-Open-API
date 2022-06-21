import datetime

from flask import Blueprint, request, jsonify

from .models import Product, Statistic
from .utils import is_cor_uuid, ShopUnitStatisticUnit, ShopUnitImportRequest, ShopUnit, parse_iso, \
    ProductType, ValidationException

api_module = Blueprint('api', __name__, url_prefix='')


def json_message(code, message):
    return jsonify({'code': code, 'message': message})


@api_module.post('/imports')
def imports():
    import_request = ShopUnitImportRequest(**request.json)

    if not all([is_cor_uuid(item.id) for item in import_request.items]):
        raise ValidationException

    if len(import_request.items) != len(set(import_request.items)):
        raise ValidationException

    import_units = [Product(
        id=item.id, name=item.name, parent_id=item.parentId,
        price=item.price, type_id=ProductType.get_id(item.type),
        update_date=import_request.updateDate
    ) for item in import_request.items]

    Product.add_or_update_tree(import_units)

    return json_message(200, 'Accepted')


@api_module.delete('/delete/<id>')
def delete(id):
    if not is_cor_uuid(id):
        raise ValidationException

    Product.delete_with_children(id)

    return json_message(200, 'Accepted')


@api_module.get('/nodes/<id>')
def nodes(id):
    if not is_cor_uuid(id):
        raise ValidationException

    if not Product.is_contains(id):
        raise Exception

    products = Product.select_tree(id)

    if len(products) == 0:
        raise Exception

    products_dict = {product.id: ShopUnit(
        product.id, product.name, product.type_id,
        product.update_date, product.parent_id, product.price
    ) for product in products}

    for key, val in products_dict.items():
        if val.parentId in products_dict.keys():
            products_dict[val.parentId].add_child(val)

    #  TODO: calc price on database level
    products_dict[id].calc_price()

    return jsonify(products_dict[id].to_dict())


""" Дополнительные задания. """


@api_module.get('/sales')
def sales():
    if 'date' not in request.values.keys():
        raise ValidationException

    now = parse_iso(request.values['date'])
    day_before = now - datetime.timedelta(days=1)
    res = Statistic.select_offers(day_before, now)

    return jsonify({
        'items': [ShopUnitStatisticUnit(**product.to_dict(only=(
            'name', 'id', 'update_date', 'parent_id', 'price', 'type_id'
        ))).__dict__ for product in res]
    })


@api_module.get('/node/<id>/statistic')
def node_statistic(id):
    if not is_cor_uuid(id):
        raise ValidationException

    if 'dateStart' in request.values and 'dateEnd' in request.values:
        pass

    return json_message(200, 'Not realized')


@api_module.app_errorhandler(ValidationException)
def validation_failed(error):
    return json_message(400, 'Validation Failed'), 400


@api_module.app_errorhandler(Exception)
def not_found(error):
    return json_message(404, 'Item not found'), 404
