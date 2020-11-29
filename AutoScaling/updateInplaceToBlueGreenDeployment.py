import json

import boto3
from botocore.vendored import requests

# Test data for lambda function
# {
#   "RequestType": "Create",
#   "ResponseURL": "http://pre-signed-S3-url-for-response",
#   "StackId": "arn:aws:cloudformation:ap-northeast-2:086403489859:stack/web1/eab9ed70-2d4c-11eb-9c8c-0a859ca39880",
#   "RequestId": "1231djfsafassfds",
#   "ResourceType": "Custom::TestResource",
#   "LogicalResourceId": "MyTestResource",
#   "ResourceProperties": {
#     "StackName": "MyStack",
#     "ApplicationName": "CodeDeployGitHubDemo-App",
#     "DeploymentGroupName": "CodeDeployGitHubDemo-DepGrp",
#     "AutoscalingGroupName": "web1-WebAutoScalingGroup",
#     "TargetGroupName": "web1-DefaultRoutingTargetGroup"
#   }
# }

def lambda_handler(event, context):
    try:
        print("event ---> ", event)
        print("context ---> ", context)
        
        application_name = event['ResourceProperties']['ApplicationName']
        deployment_group_name = event['ResourceProperties']['DeploymentGroupName']
        autoscaling_group_name = event['ResourceProperties']['AutoscalingGroupName']
        target_group_name = event['ResourceProperties']['TargetGroupName']
        TriggerTargetArn = event['ResourceProperties']['TriggerTargetArn']

        codedeploy_client = boto3.client('codedeploy')

        if event['RequestType'] == 'Create':
            response = codedeploy_client.update_deployment_group(
                applicationName=application_name,
                currentDeploymentGroupName=deployment_group_name,
                deploymentConfigName="CodeDeployDefault.AllAtOnce",
                autoScalingGroups=[autoscaling_group_name],
                deploymentStyle={
                    "deploymentType": "BLUE_GREEN",
                    "deploymentOption": "WITH_TRAFFIC_CONTROL"
                },
                blueGreenDeploymentConfiguration={
                    "terminateBlueInstancesOnDeploymentSuccess": {
                        "action": "TERMINATE"
                    },
                    "deploymentReadyOption": {
                        "actionOnTimeout": "CONTINUE_DEPLOYMENT"
                    },
                    "greenFleetProvisioningOption": {
                        "action": "COPY_AUTO_SCALING_GROUP"
                    }
                },
                triggerConfigurations=[
                    {
                        "triggerName": "DeploymentFailureTr",
                        "triggerTargetArn": TriggerTargetArn,
                        "triggerEvents": ["DeploymentFailure"]
                    }
                    ],
                loadBalancerInfo={
                    "targetGroupInfoList": [
                        {
                            "name": target_group_name
                        }
                        ]
                }
                )
            print("Updated Deployment Type to BLUE_GREEN {} --> response: {}".format(deployment_group_name , response))
        elif event['RequestType'] == 'Delete':
            client = boto3.client('autoscaling')
            try:
                response = codedeploy_client.get_deployment_group(
                    applicationName=application_name, 
                    deploymentGroupName=deployment_group_name
                    )
                
                autoScalingGroups = response.get("deploymentGroupInfo", {}).get("autoScalingGroups", []) or []
                
                for autoScalingGroup in autoScalingGroups:
                    name = autoScalingGroup.get("name")
                    try: #if autoScalingGroup name doesn't exist, it must not the execution
                        if name:
                            response = client.delete_auto_scaling_group(
                                AutoScalingGroupName=name,
                                ForceDelete=True
                            )
                            print("Deleted auto scaling group {} --> response: {}".format(name , response))
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)
        sendResponseToCloudformation(event, context, "SUCCESS")
    except Exception as e:
        print(e)
        sendResponseToCloudformation(event, context, "FAILURE")
    
    
def sendResponseToCloudformation(event, context, responseStatus):
    response_body = {'Status': responseStatus,
                     'Reason': 'Log stream name: ' + context.log_stream_name,
                     'PhysicalResourceId': context.log_stream_name,
                     'StackId': event['StackId'],
                     'RequestId': event['RequestId'],
                     'LogicalResourceId': event['LogicalResourceId'],
                     'Data': json.loads("{}")}

    response = requests.put(event['ResponseURL'], data=json.dumps(response_body))
    
    print("response ---> ", response)