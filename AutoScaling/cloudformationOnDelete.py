
import json

import boto3
from botocore.vendored import requests


def lambda_handler(event, context):
    try:
        print("event ---> ", event)
        print("context ---> ", context)

        if event['RequestType'] == 'Delete':
            bucket = event['ResourceProperties']['BucketName']
            dir = event['ResourceProperties']['Folder']
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucket)
            if dir:
                for obj in bucket.objects.filter(Prefix='{}/'.format(dir)):
                    r = s3.Object(bucket.name, obj.key).delete()
                    print("r --> ", r)
            else:
                bucket.objects.all().delete()

        sendResponseCfn(event, context, "SUCCESS")
    except Exception as e:
        print(e)
        sendResponseCfn(event, context, "FAILED")
    
    
def sendResponseCfn(event, context, responseStatus):
    response_body = {'Status': responseStatus,
                     'Reason': 'Log stream name: ' + context.log_stream_name,
                     'PhysicalResourceId': context.log_stream_name,
                     'StackId': event['StackId'],
                     'RequestId': event['RequestId'],
                     'LogicalResourceId': event['LogicalResourceId'],
                     'Data': json.loads("{}")}


    """
    'StackId': event['StackId'],
                     'RequestId': event['RequestId'],
                     'LogicalResourceId': event['LogicalResourceId'],
    """
    response = requests.put(event['ResponseURL'], data=json.dumps(response_body))
    
    print("response ---> ", response)

