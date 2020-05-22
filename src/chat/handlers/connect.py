import json

from boto3 import client as boto3_client


dynamodb_client = boto3_client('dynamodb')


def lambda_handler(event, context):

    connection_id = event["requestContext"].get("connectionId")
    dynamodb_client.put_item(
        TableName='connections',
        Item={
            "id": {'S': connection_id},
            "rooms": {'SS': ['lobby']}
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Helloooo from Lambda!')
    }
