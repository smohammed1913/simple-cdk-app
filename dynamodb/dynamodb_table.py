from aws_cdk import (
    aws_events,
    aws_events_targets as targets,
    aws_kms,
    aws_sns,
    aws_sns_subscriptions as sns_sub,
    aws_ssm,
    aws_dynamodb as dynamodb,
    aws_apigatewayv2 as apigatewayv2,
    Stack,
    aws_iam
)

from constructs import Construct


class DynamodbTable(Stack):

    def __init__(self, scope: Construct, sid: str, config: dict, **kwargs) -> None:
        super().__init__(scope, sid, **kwargs)

        table_name = config["TableName"]
        attribute_name = config["AttributeName"]

        dynamodb.CfnTable( self, f"{config['NamePrefix']}-dynamodb-table",
                                      
            key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                attribute_name=attribute_name,
                key_type="HASH"
            )],

            attribute_definitions=[dynamodb.CfnTable.AttributeDefinitionProperty(
                attribute_name=attribute_name,
                attribute_type="S"
            )],

            provisioned_throughput=dynamodb.CfnTable.ProvisionedThroughputProperty(
                read_capacity_units=1,
                write_capacity_units=1
            ),

            table_name=table_name

        )