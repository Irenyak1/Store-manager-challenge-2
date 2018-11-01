from flask import Blueprint, jsonify, request
from api.models.SaleRecord_model import SaleRecord
from api.models.product_model import Product
from api.models.user_models import User
from api.validators import Validate
from datetime import datetime
from api.views.user_views import token_required
from flasgger import swag_from

sale = Blueprint('sale', __name__)

validate = Validate()
product = Product()
salerecord = SaleRecord()

@sale.route('/api/v2/sales', methods=['POST'])
@swag_from('../apidocs/sales/create_sale_record.yml')
@token_required
def create_sale_record():
    """ Creates a new sale record"""
    user = User()
    data = request.get_json()
    date_sold = datetime.now()
    price = product.fetch_product_price(data['product_name'])
    current_user = user.fetch_current_user()
    total_amount = int(price) * int(data['product_quantity'])
    fetched_token = request.headers['Authorization']
    token = fetched_token.split(" ")[1]
    if user.validate_token(token):
        return jsonify({"message": "Token blacklisted, login again"}), 400
    if validate.check_permission(token) is False:
        return jsonify({"message": "Permission Denied, Not an Attendant"}), 400
    valid = validate.validate_sale(data)
    try:
        if valid == "Sale_valid":
            if product.check_if_product_exists(data['product_name']) is False:
                return jsonify({"message": "Product does not exist"}), 400
            if product.compute_stock_balance(data['product_quantity'],
                                             data['product_name']) is False:
                return jsonify({
                    "message":
                    "Stock balance less than requested quantity"}), 400
            salerecord.make_a_sale(total_amount, current_user,
                                   data['product_name'],
                                   data['product_quantity'], price,
                                   date_sold)
            return jsonify({"message": "record created successfully"}), 201
        return jsonify({"message": valid}), 400
    except ValueError:
        return jsonify({"message": "Invalid"})


@sale.route('/api/v1/sales', methods=['GET'])
@swag_from('../apidocs/sales/get_all_sales.yml')
def fetch_sale_orders():
    """This endpoint fetches all sale records"""
    Sales = [record.get_dict() for record in sales]
    return jsonify({"All Sales": Sales}), 200


@sale.route('/api/v1/sales/<int:sale_id>', methods=['GET'])
@swag_from('../apidocs/sales/get_single_sale.yml')
def get_single_record(sale_id):
    single_record = []
    if sale_id != 0 and sale_id <= len(sales):
        record = sales[sale_id - 1]
        single_record.append(record.get_dict())
        return jsonify({"Record": single_record}), 200
    return jsonify({"message": "Index out of range!"}), 400
