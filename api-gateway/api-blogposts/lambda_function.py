import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE']
table = dynamodb.Table(table_name)
print(table_name)


def get_post(event):
    """Read post_item"""
    postID = event['pathParameters']['postID']
    response = table.get_item(
        Key={
            'postID': postID
        }
    )
    item = response.get('Item')
    if item:
        return {
            'statusCode': 200,
            'body': json.dumps(item)
        }
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Item not found'})
        }

def put_post(event):
    """Creates new post"""
    body = json.loads(event['body'])
    response = table.put_item(
        Item={
            'postID': body["postID"],
            'text': body['text']
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Post created'})
    }

def update_post(event):
    """Updates post"""
    body = json.loads(event['body'])
    response = table.update_item(
        Item={
            'postID':  body["postID"],
            'text': body['text']
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Post updated'})
    }
    
def delete_post(event):
    """Deletes post"""
    postID = event['pathParameters']['postID']
    response = table.delete_item(
        Key={
            'postID': postID
        }
    )
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Post deleted'})
    }

def lambda_handler(event, context):
    http_method = event['requestContext']['http']['method']
    print(http_method)
    if http_method == 'GET':
        return get_post(event)
    elif http_method == 'PUT':
        return put_post(event)
    elif http_method == 'POST':
        return update_post(event)
    elif http_method == 'DELETE':
        return delete_post(event)
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }