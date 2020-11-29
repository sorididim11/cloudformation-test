
import json

import boto3
from botocore.vendored import requests


def lambda_handler(event, context):
    try:
        print("event ---> ", event)
        print("context ---> ", context)

        records = event.get("Records")
        if records:
            record = records[0]
            application_name, deployment_group_name, *_ = record.get("Sns", {}).get("TopicArn", "").split(":")[
                -1].split("-")
            print("applicationName: {}, deploymentGroupName: {}, _: {}".format(application_name, deployment_group_name, _))

            client = boto3.client('autoscaling')
            codedeploy_client = boto3.client('codedeploy')

            response = codedeploy_client.list_deployments(
                applicationName=application_name,
                deploymentGroupName=deployment_group_name,
                includeOnlyStatuses=["Failed"]
            )

            deploymentIds = response.get("deployments")

            if deploymentIds:
                deploymentId = deploymentIds[0]

                response = codedeploy_client.get_deployment(
                    deploymentId=deploymentId
                )
                autoScalingGroups = response.get('deploymentInfo', {}).get("targetInstances", {}).get(
                    "autoScalingGroups", [])

                for autoScalingGroup in autoScalingGroups:
                    response = client.delete_auto_scaling_group(
                        AutoScalingGroupName=autoScalingGroup,
                        ForceDelete=True
                    )
                    print("Deleted auto scaling group {} --> response: {}".format(autoScalingGroup, response))
                    
        return {
        'statusCode': 200,
        'body': json.dumps('Success')
        } 

    except Exception as e:
        print(e)
        return {
        'statusCode': 500,
        'body': json.dumps('Failure')
        } 