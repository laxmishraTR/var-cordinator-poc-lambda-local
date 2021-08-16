from __future__ import print_function

import json
import boto3
import base64
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
client = boto3.client('dynamodb')

table = dynamodb.Table('a207957-var-release-coordinator-POC')


def updateStage(key):
    table.update_item(
        Key={
            'contentGuid': key
        },
        UpdateExpression="set stage = :s",
        ExpressionAttributeValues={
            ':s': 'Released'
        },
        ReturnValues="UPDATED_NEW"
    )


def lambda_handler(event, context):
    print('Event : ', event)

    message = event['Records'][0]['Sns']['Message']
    data = json.loads(message)
    print('data : ', data)

    # writing CFT_REL

    if (data['entityType'] == 'CFT_REL'):
        data['stage'] = 'Released'
        print("printing cft data")
        try:
            responses = client.batch_get_item(
                RequestItems={
                    'a207957-var-release-coordinator-POC': {
                        'Keys': [{'contentGuid': {'S': data['relatedGuids'][0]}},
                                 {'contentGuid': {'S': data['relatedGuids'][1]}}
                                 ]
                    }
                }
            )

        except Exception:
            print("exception occured", Exception)

        print('Responses from CFT : ', responses)
        print('writing REL type event')
        table.put_item(Item=data)
        count = 0
    elif (data['entityType'] == "INDEX"):
        data['stage'] = "pending"
        responses = table.scan(FilterExpression=Attr('entityType').eq('INDEX') & Attr('stage').eq('pending'))
        print("response from INDEX:", responses)
        table.put_item(Item=data)
        count = len(responses['Items'])
        print("this is count", count)
    else:
        data['stage'] = 'Pending'
        print('writing ORG type event')
        table.put_item(Item=data)
        count = 0

    if count >= 2 or (data['entityType'] == 'CFT_REL'):
        data['stage'] = "Released"
        print('data:', data)

        if (data['entityType'] == 'CFT_REL'):
            for i in responses['Responses']['a207957-var-release-coordinator-POC']:
                print('updating item : ', i['contentGuid']['S'])

                updateStage(i['contentGuid']['S'])

        else:
            for i in responses['Items']:
                key = i['contentGuid']
                print('key', key)

                updateStage(key)