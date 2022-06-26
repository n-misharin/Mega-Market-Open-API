import datetime

from flask import Blueprint, request, jsonify, make_response

from .models import ProductTree, ShopUnitImportRequest, Product, Statistic
from .utils import ValidationException, ItemNotFoundException, parse_iso, \
    is_cor_uuid

api_module = Blueprint('api', __name__, url_prefix='')


def json_message(code, message):
    """ Convert dict(code=code, message=message) to json. """
    return jsonify({'code': code, 'message': message})


@api_module.post('/imports')
def imports():
    print(request.json)
    try:
        import_data = ShopUnitImportRequest(**request.json)
        ProductTree.add_or_update_all(import_data.get_products_list())
        """ 
        Обновляем статистику после изменений товаров/категорий, 
        т.к. гарантируется, что updateDate возрастает с каждым запросом. 
        """
        Product.write_statistics(import_data.update_date)

    except Exception as e:
        print(e)
        raise ValidationException

    return json_message(200, 'Accepted')


@api_module.delete('/delete/<id>')
def delete(id):
    if not is_cor_uuid(id):
        raise ValidationException

    try:
        ProductTree.remove_node(id)
    except Exception:
        raise ItemNotFoundException

    return json_message(200, 'Accepted')


@api_module.get('/nodes/<id>')
def nodes(id):
    if not is_cor_uuid(id):
        raise ValidationException

    try:
        return jsonify(ProductTree.get_subtree(id))
    except Exception:
        raise ItemNotFoundException


""" Дополнительные задания. """


@api_module.get('/sales')
def sales():
    try:
        now = parse_iso(request.values['date'])
        day_before = now - datetime.timedelta(days=1)
        return jsonify(Product.get_from_period(day_before, now))
    except Exception as e:
        raise ValidationException


@api_module.get('/node/<id>/statistic')
def node_statistic(id):
    if not is_cor_uuid(id):
        raise ValidationException

    date_start = request.values.get('dateStart', None)
    date_end = request.values.get('dateEnd', None)

    if date_end is not None and date_start is not None:
        try:
            date_start = parse_iso(date_start)
            date_end = parse_iso(date_end)
        except Exception:
            raise ValidationException

    res = Statistic.get(id, date_start, date_end)

    return jsonify(res)


@api_module.app_errorhandler(ValidationException)
def validation_failed(error):
    return json_message(400, 'Validation Failed'), 400


@api_module.app_errorhandler(ItemNotFoundException)
def not_found(error):
    return json_message(404, 'Item not found'), 404
