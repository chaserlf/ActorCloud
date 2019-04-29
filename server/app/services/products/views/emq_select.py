from flask import request, jsonify

from actor_libs.errors import ParameterInvalid
from app import auth
from app.models import Product, DataStream, DataPoint
from . import bp


@bp.route('/emq_select/data_points')
@auth.login_required(permission_required=False)
def list_emq_select_data_points():
    records = {}
    return jsonify(records)


@bp.route('/emq_select/data_streams')
@auth.login_required(permission_required=False)
def list_emq_select_data_streams():
    records = {}
    return jsonify(records)


@bp.route('/emq_select/stream_datapoints')
@auth.login_required(permission_required=False)
def list_emq_select_stream_points():
    """ Return all data_points under data_stream """

    product_uid = request.args.get('productID', type=str)
    if not product_uid:
        raise ParameterInvalid(field='productID')
    product = Product.query.filter_by(productID=product_uid).first_or_404()
    if product.cloudProtocol == 7:
        # modbus protocol not data stream
        data_points = DataPoint.query.filter_by(productID=product_uid).all()
        streams_tree = [
            {'label': record.dataPointName, 'value': record.dataPointID}
            for record in data_points
        ]
    else:
        # other protocol
        streams_tree = []
        data_streams = DataStream.query.filter(DataStream.productID == product_uid).all()
        for data_stream in data_streams:
            data_points = []
            for data_point in data_stream.dataPoints:
                select_option = {
                    'label': data_point.dataPointName,
                    'value': data_point.dataPointID
                }
                data_points.append(select_option)
            streams_tree.append({
                'label': data_stream.streamName,
                'value': data_stream.id,
                'children': data_points
            })
    return jsonify(streams_tree)


@bp.route('/emq_select/topics')
@auth.login_required(permission_required=False)
def list_emq_select_topics():
    product_uid = request.args.get('productID', type=str)
    if not product_uid:
        raise ParameterInvalid(field='productID')
    product = Product.query.filter_by(productID=product_uid).first_or_404()
    if product.cloudProtocol == 3:
        record = [
            {
                'key': 'ad/#',
                'value': 'ad/#'
            }]
    else:
        topics = DataStream.query \
            .with_entities(DataStream.topic) \
            .filter(DataStream.productID == product_uid) \
            .many()
        record = [
            {
                'key': topic.topic,
                'value': topic.topic
            }
            for topic in topics
        ]

    return jsonify(record)
