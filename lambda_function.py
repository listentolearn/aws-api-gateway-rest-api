import json
import logging
import os

from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.types import Decimal
import boto3


class books:

    def __init__(self, table, hash_key):
        self.table = table
        self.hk = hash_key
    
    def _get_dynamodb_table(self):
        region = os.environ.get('AWS_REGION', 'us-east-1')
        return boto3.resource('dynamodb', region_name=region).Table(self.table)
    
    def _get_dynamodb_key(self, hash_key):
        key = {}
        key[self.hk] = hash_key
        return key

    def _problem(self, e, status=500):
        logging.info(f'Processing api method: {str(e)}')
        return {
            'statusCode': status,
            'body': json.dumps({
                'error': str(e),
                'status': status
            })
        }

    def _json_serial(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        raise TypeError("Type not serializable")

    def _exists(self, hk):
        try:
            response = self._get_dynamodb_table().get_item(
                Key=self._get_dynamodb_key(hk)
            )
        except Exception as e:
            return False
        if 'Item' not in response:
            return False
        return True

    def list_books(self, kwargs):
        query_params = kwargs['queryStringParameters']
        filter_expr = None
        if query_params is not None:
            for attr, val in sorted(query_params.items()):
                if val.isdigit():
                    val = int(val)
                expr = Attr(attr).eq(val)
                filter_expr = expr if filter_expr is None else filter_expr & expr
        items = []
        last_key = None
        while True:
            kwargs = {}
            if filter_expr is not None:
                kwargs['FilterExpression'] = filter_expr
            if last_key is not None:
                kwargs['ExclusiveStartKey'] = last_key
            response = self._get_dynamodb_table().scan(**kwargs)
            for item in response['Items']:
                item = json.loads(json.dumps(item, default=self._json_serial))
                items.append(item)
            if 'LastEvaluatedKey' in response:
                last_key = response['LastEvaluatedKey']
            else:
                break
        items.sort(key=lambda i:i[self.hk])
        return {
            'statusCode': 200,
            'body': json.dumps({
                'data': items,
                'count': len(items)
            })
        }

    def get_book(self, kwargs):
        try:
            hk = kwargs['pathParameters'][self.hk]
            response = self._get_dynamodb_table().get_item(
                Key=self._get_dynamodb_key(hk)
            )
        except Exception as e:
            return self._problem(e)
        if 'Item' not in response:
            return self._problem('Book not found.', 404)
        item = json.loads(json.dumps(response['Item'], default=self._json_serial))
        return {
            'statusCode': 200,
            'body': json.dumps(item, default=self._json_serial)
        }
        
    def post_book(self, kwargs):
        try:
            book = json.loads(kwargs['body'])
            if self._exists(book[self.hk]):
                return self._problem('Book already exists', 400)
            table = self._get_dynamodb_table()
            table.put_item(Item=book)
            return {
                'statusCode': 200,
                'body': json.dumps(book, default=self._json_serial)
            }
        except Exception as e:
            return self._problem(e)

    def put_book(self, kwargs):
        try:
            hk = kwargs['pathParameters'][self.hk]
            if not self._exists(hk):
                return self._problem('Book not found.', 404)
            book = json.loads(kwargs['body'])
            table = self._get_dynamodb_table()
            key = self._get_dynamodb_key(hk)
            kwargs = {
                'Key': key,
                'ReturnValues': 'ALL_NEW'
            }
            exp = []
            _vals = {}
            aliases = {}
            for k, v in sorted(book.items()):
                if isinstance(v, str) and v == '':
                    v = None
                aliases['#%s' % k] = k
                exp.append('#%s = :%s' % (k, k))
                _vals[':%s' % k] = v
            if len(_vals):
                kwargs['ExpressionAttributeValues'] = _vals
                kwargs['UpdateExpression'] = 'set %s' % ', '.join(exp)
            if len(aliases):
                kwargs['ExpressionAttributeNames'] = aliases
                response = table.update_item(**kwargs)
                book.update(response.get('Attributes'))
            return {
                'statusCode': 200,
                'body': json.dumps(book, default=self._json_serial)
            }
        except Exception as e:
            return self._problem(e)

    def delete_book(self, kwargs):
        try:
            hk = kwargs['pathParameters'][self.hk]
            if not self._exists(hk):
                return self._problem('Book not found.', 404)
            self._get_dynamodb_table().delete_item(
                Key=self._get_dynamodb_key(hk)
            )
        except Exception as e:
            return self._problem(e)
        return {
            'statusCode': 204
        }


def lambda_handler(event, context):
    table = os.environ.get('DYNAMODB_TABLE', 'books')
    hash_key = os.environ.get('HASH_KEY', 'isbn')
    method = getattr(
        books(table, hash_key),
        event['requestContext']['operationName'],
        None
    )
    logging.info(f'Processing api method: {method}')
    if method is None:
        return {
            'stateCode': 404,
            'body': json.dumps('Unknown method.')
        }
    kwargs = {
        'queryStringParameters': event['queryStringParameters'],
        'pathParameters': event['pathParameters'],
        'body': event['body']
    }
    return method(kwargs)

