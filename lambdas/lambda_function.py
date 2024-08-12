from aws_cdk import (
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_ssm,
    aws_cloudwatch,
    aws_cloudwatch_actions,
    aws_sns,
    Duration,
    Stack
)

from constructs import Construct


class LambdaFunction(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        topic_name = config["SNSAlertTopicName"]
        alarm_sns_arn = f"arn:aws:sns:{self.region}:{self.account}:{topic_name}"
        topic = aws_sns.Topic.from_topic_arn(self, "AuditTopic", alarm_sns_arn)


        ### Lambda Role
        lambda_role = aws_iam.Role(
            self, 'LambdaServiceRole',
            role_name=config['LambdaServiceRoleName'],
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            description='Lambda Service Role',
            inline_policies={
                'lambda_vpc_policy': aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                'ec2:CreateNetworkInterface',
                                'ec2:DescribeNetworkInterfaces',
                                'ec2:DeleteNetworkInterface'
                            ],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        lambda_role.add_managed_policy(
            aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
        )

        lambda_role.attach_inline_policy(
            aws_iam.Policy(
                self, 'lambda_dynamodb_access_policy',
                statements=[aws_iam.PolicyStatement(
                    actions=[
                        'dynamodb:PutItem',
                        'dynamodb:GetItem',
                        'dynamodb:DeleteItem',
                        'dynamodb:Scan'
                    ],
                    resources=[
                        f"*"
                    ]
                )]
            )
        )

        lambda_role.attach_inline_policy(
            aws_iam.Policy(
                self, 'lambda_logs_access_policy',
                statements=[aws_iam.PolicyStatement(
                    actions=[
                            'logs:CreateLogGroup',
                            'logs:CreateLogStream',
                            'logs:PutLogEvents'
                    ],
                    resources=[
                        f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*"
                    ]
                )]
            )
        )


        dependency_layer = self.create_dependencies_layer(config['Application'])

        ## Lambda Functions
        for lambda_function in config['Lambdas']:
            # Read global arguments from config
            config_default_arguments = lambda_function.get("LambdaArguments", {})

            lambda_name = lambda_function['Name']
            lambda_script = lambda_function['ScriptName']

            function_name=f"{config['NamePrefix']}-{lambda_name}"

            # Create Lambda function
            lambda_function = aws_lambda.Function(
                self,
                lambda_name,
                function_name=function_name,
                code=aws_lambda.Code.from_asset(f"lambda_code/{lambda_script.replace('.mjs', '')}"),
                handler='index.handler',
                runtime=aws_lambda.Runtime.NODEJS_18_X,
                timeout=Duration.minutes(15),
                environment=config_default_arguments,
                role=lambda_role,
                layers = [dependency_layer]
                # vpc=vpc,
                # security_groups=[security_group]
            )

            ### Adds alarms to lambdas that are on a per function instance
            self.setup_lambda_alarms(lambda_function, f"{function_name}", topic=topic)

            # function_arn = f"arn:aws:lambda:{self.region}:{self.account}:function:{function_name}"
            function_arn = lambda_function.function_arn
            # print(function_arn)

            apigw_arn = f"arn:{self.partition}:execute-api:{self.region}:{self.account}:*/*/*"
            # print(apigw_arn)
            cfn_permission = aws_lambda.CfnPermission(self, f"lambda-ssm-{lambda_name}",
                action="lambda:InvokeFunction",
                function_name=lambda_function.function_name,
                principal="apigateway.amazonaws.com",
                source_arn=apigw_arn
            )

            environment = config_default_arguments['Environment']

            aws_ssm.StringParameter(self, f"lambda-ssm-{function_name}",
                parameter_name=f"/cdk/{config['Application']}/{environment}/{lambda_name}",
                string_value=function_arn
            )


            
    def create_dependencies_layer(self, application) -> aws_lambda.LayerVersion:

        output_dir = f"lambda_layer"  
        # print(output_dir)
        layer_id = f"{application}-dependencies-layer" 
        layer_code = aws_lambda.Code.from_asset(output_dir)  

        lambda_layer = aws_lambda.LayerVersion(
            self,
            layer_id,
            code=layer_code,
        )

        return lambda_layer

    def setup_lambda_alarms(self, lambda_function: aws_lambda.Function, lambda_name: str, topic: aws_sns.Topic):

            ### Create lambda metrics
            error_metric = lambda_function.metric_errors()
            throttle_metric = lambda_function.metric_throttles()


            ### Create alarms for lambda metrics and send to SNS topic
            error_alarm = aws_cloudwatch.Alarm(
                self, f"ErrorAlarm{lambda_name}",
                metric=error_metric,
                threshold=1,
                evaluation_periods=1,
                datapoints_to_alarm=1,
                comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                treat_missing_data=aws_cloudwatch.TreatMissingData.NOT_BREACHING,
                alarm_name=f"lambda-error-alarm-{lambda_name}"
                )
            error_alarm.add_alarm_action(aws_cloudwatch_actions.SnsAction(topic))

            throttle_alarm = aws_cloudwatch.Alarm(
                self, f"ThrottleAlarm{lambda_name}",
                metric=throttle_metric,
                threshold=1,
                evaluation_periods=1,
                datapoints_to_alarm=1,
                comparison_operator=aws_cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                treat_missing_data=aws_cloudwatch.TreatMissingData.NOT_BREACHING,
                alarm_name=f"lambda-throttle-alarm-{lambda_name}"
                )
            throttle_alarm.add_alarm_action(aws_cloudwatch_actions.SnsAction(topic))
