import string

import yaml
import aws_cdk as cdk

from lambdas import lambda_function
from sns import sns_notification
from apigateway import gwapi
from dynamodb import dynamodb_table
from deployment_bucket import s3_deploymet_bucket

app = cdk.App()

# Read environment name
env = app.node.get_context('env')
context = app.node.get_context(env)


def load_config(filename, context):
    """
    Read config and substitute embedded variables

    Args:
        filename (string): name of config file to be read
        context (dict): single-level dictionary with variable substitutions
    """

    def string_constructor(_, node):
        templ = string.Template(node.value)
        return templ.substitute(context)

    loader = yaml.SafeLoader
    loader.add_constructor('tag:yaml.org,2002:str', string_constructor)
    loader.add_implicit_resolver('tag:yaml.org,2002:str', string.Template.pattern, None)

    # Read configuration file
    with open(filename, 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=loader)

    return config
# print('context:::')
# print(context)

application =  context['Application']

# Tags applied to all stacks and resources
cdk.Tags.of(app).add('Project', context['Project'])
cdk.Tags.of(app).add('Environment', env)
cdk.Tags.of(app).add('Application',application)
cdk.Tags.of(app).add('SubAapplication', context['SubAapplication'])

# Deployment of sns for critical alerts and warnings
sns_config = load_config('configs/sns_config.yaml', context)
sns_notification_stack = sns_notification.SNSNotification(
    app, f"{application}-{env}-sns-notifications", config=sns_config)

# Deployment of lambda crud functions
lambda_config = load_config('configs/lambda_config.yaml', context)
lambda_function_stack = lambda_function.LambdaFunction(
    app, f"{application}-{env}-lambda-functions", config=lambda_config)

# Deployment of api gateway
apigw_config = load_config('configs/apigw_config.yaml', context)
apigw_stack = gwapi.Gwapi(
    app, f"{application}-{env}-apigw", config=apigw_config)

# Deployment of Dynamodb table
dynamo_config = load_config('configs/dynamodb_config.yaml', context)
apigw_stack = dynamodb_table.DynamodbTable(
    app, f"{application}-{env}-dynamodb-table", config=dynamo_config)

# Deployment of s3
s3_config = load_config('configs/s3_config.yaml', context)
apigw_stack = s3_deploymet_bucket.S3DeploymentBucket(
    app, f"{application}-{env}-s3-hosting-bucket", config=s3_config)



app.synth()
