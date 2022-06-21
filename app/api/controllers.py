import uuid

from flask import Blueprint, request, jsonify, abort

from .models import Product, ShopUnitImportRequest, ShopUnit

api_module = Blueprint('api', __name__, url_prefix='')


@api_module.post('/imports')
def imports():
    try:
        import_request = ShopUnitImportRequest(**request.json)
        Product.add_or_update(import_request.to_products_list())
        return jsonify({"code": 200, "message": "Accepted"})
    except Exception as e:
        print(e)
        abort(400)


@api_module.delete('/delete/<id>')
def delete(id):
    try:
        #  TODO: column id must be typing UUID
        id = str(uuid.UUID(id))
    except Exception:
        abort(400)

    Product.delete(id)

    return jsonify({"code": 200, "message": "Accepted"})


@api_module.get('/nodes/<id>')
def nodes(id):
    try:
        #  TODO: column id must be typing UUID
        id = str(uuid.UUID(id))
    except Exception as e:
        abort(400)

    products = Product.select(id)

    if len(products) == 0:
        abort(404)

    #  TODO: create constructor in ShopUnit which takes one argument
    #   of Product
    products_dict = {
        product.id: ShopUnit(
            product.id,
            product.name,
            product.type_id,
            product.update_date,
            product.parent_id,
            product.price
        ) for product in products
    }

    for key, val in products_dict.items():
        if val.parentId in products_dict.keys():
            products_dict[val.parentId].add_child(val)

    #  TODO: calc price on database level
    products_dict[id].calc_price()

    return jsonify(products_dict[id].to_dict())


""" Дополнительные задания """


@api_module.get('/sales')
def sales():
    return 'sales'


@api_module.get('/node/<int:id>/statistic')
def node_statistic():
    return 'node statistic'


@api_module.app_errorhandler(400)
def validation_failed(error):
    return jsonify({
        'code': 400,
        'message': 'Validation Failed'
    })


@api_module.app_errorhandler(404)
def not_found(error):
    return jsonify({
        'code': 404,
        'message': 'Item not found'
    })
