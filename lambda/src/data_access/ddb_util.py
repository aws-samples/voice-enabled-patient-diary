
import json
import logging

import boto3
from data_access.data_config import LOG_LEVEL
from botocore.exceptions import ClientError
from decimal import Decimal

logger = logging.getLogger('DDB_Utils')
logger.setLevel(LOG_LEVEL)

dynamodb = boto3.resource('dynamodb')


def convert_num_to_dec(num):
    """
    Convert a number to decimal. This is required when writing floating point numbers to DDB.
    :param num: a float
    :return: representation of the number in Decimal
    """
    return Decimal(str(num))


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def put_item_ddb(table_name, item, ddb_client=None):
    if ddb_client is not None:
        table = ddb_client.Table(table_name)
        logger.info('putting in ddb using ddb client override')
    else:
        table = dynamodb.Table(table_name)
    try:
        table.put_item(Item=item)
        logger.info(f'success putting item to {table_name} DDB table.')
    except ClientError as e:
        logger.error(f'Error putting item to ddb: {table_name}', exc_info=True)
        raise e


def update_item_ddb(table_name, ddb_client=None, **kwargs):
    if ddb_client is not None:
        table = ddb_client.Table(table_name)
        logger.info('updating ddb using ddb client override')
    else:
        table = dynamodb.Table(table_name)
    try:
        table.update_item(**kwargs)
        logger.info(f'Success updating item to {table_name} DDB table.')
    except ClientError as e:
        logger.error(f'Error updating item to ddb: {table_name}', exc_info=True)
        raise e


def query_item_ddb(table_name, ddb_client=None, **kwargs):
    if ddb_client is not None:
        table = ddb_client.Table(table_name)
        logger.info('querying ddb using ddb client override')
    else:
        table = dynamodb.Table(table_name)
    try:
        response = table.query(**kwargs)
        for i, item in enumerate(response["Items"]):
            logger.debug(f'item {i}: {json.dumps(item, cls=DecimalEncoder)}')
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.query(ExclusiveStartKey=response['LastEvaluatedKey'], **kwargs)
            logger.info(f'DDBQuery: Found {len(response["Items"])} items in next page.')
            result.extend(response['Items'])
        return result
    except ClientError as e:
        logger.error(f'Error querying {table_name} DDB table', exc_info=True)
        raise e


def scan_item_ddb(table_name, ddb_client=None, **kwargs):
    if ddb_client is not None:
        table = ddb_client.Table(table_name)
        logger.info('querying ddb using ddb client override')
    else:
        table = dynamodb.Table(table_name)
    try:
        response = table.scan(**kwargs)
        for i, item in enumerate(response["Items"]):
            logger.debug(f'item {i}: {json.dumps(item, cls=DecimalEncoder)}')
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'], **kwargs)
            logger.info(f'DDBQuery: Found {len(response["Items"])} items in next page.')
            result.extend(response['Items'])
        return result
    except ClientError as e:
        logger.error(f'Error scanning {table_name} DDB table', exc_info=True)
        raise e


def get_item_ddb(table_name, ddb_client=None, **kwargs):
    if ddb_client is not None:
        table = ddb_client.Table(table_name)
        logger.info('getting ddb data using ddb client override')
    else:
        table = dynamodb.Table(table_name)

    try:
        valid_args = ['Key', 'AttributesToGet', 'ProjectionExpression']
        response = table.get_item(**{k: v for k, v in kwargs.items() if k in valid_args})
    except ClientError as e:
        logger.error('Error querying %s DDB table', table_name, exc_info=True)
        raise e
    else:
        if 'Item' not in response:
            return None
        item = response['Item']
        logger.info('Success querying %s DDB table. Found item', table_name)
        logger.debug('item %s', json.dumps(item, cls=DecimalEncoder))
        return item


class DDBUpdateBuilder(object):
    def __init__(self, key, table_name, ddb_client=None):
        self.key = key
        self.table_name = table_name
        self.ddb_client = ddb_client
        self.update_expressions = []
        self.expression_attr_names = {}
        self.expression_attr_vals = {}

    def update_attr(self, attr_name, attr_value, convert=lambda x: x):
        self.update_expressions.append(f'#{attr_name} = :{attr_name}')
        self.expression_attr_names[f'#{attr_name}'] = attr_name
        self.expression_attr_vals[f':{attr_name}'] = convert(attr_value)

    def update_params(self):
        return {
            'Key': self.key,
            'UpdateExpression': 'set ' + ','.join(self.update_expressions),
            'ExpressionAttributeNames': self.expression_attr_names,
            'ExpressionAttributeValues': self.expression_attr_vals
        }

    def commit(self):
        if self.update_expressions:
            ddb_update_item = self.update_params()
            update_item_ddb(self.table_name, self.ddb_client, **ddb_update_item)
        else:
            logger.info('DDBUpdateBuilder: nothing to update. will do nothing.')

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        logger.info(f'Committing params to dynamodb [{self.table_name}: {self.key}]')
        self.commit()
