from aws_cdk import (
    aws_events,
    aws_events_targets as targets,
    aws_kms,
    aws_sns,
    aws_sns_subscriptions as sns_sub,
    aws_ssm,
    aws_apigatewayv2 as apigatewayv2,
    Stack,
    aws_iam
)

from constructs import Construct


class Gwapi(Stack):

    def __init__(self, scope: Construct, sid: str, config: dict, **kwargs) -> None:
        super().__init__(scope, sid, **kwargs)

        stage = config["Stage"]

        cfn_api = apigatewayv2.CfnApi(self, f"{config['NamePrefix']}-api-gw",
            # api_key_selection_expression="apiKeySelectionExpression",


            # TODO adjust cors for required resources only
            cors_configuration=apigatewayv2.CfnApi.CorsProperty(
                allow_credentials=False,
                allow_headers=["*"],
                allow_methods=["*"],
                allow_origins=["*"],
                expose_headers=["*"],
                max_age=96400
            ),
    
            description=f"{config['Description']}",
            name=f"{config['NamePrefix']}-{config['Name']}",
            protocol_type=f"{config['Protocol']}"

            # target="target"
        )


        # Api Gateway stage
        apigw_stage = apigatewayv2.CfnStage(self, f"{config['NamePrefix']}-api-gw-stage",
                api_id=cfn_api.attr_api_id,
                stage_name=stage
        )


        ## API Gateway Routes
        for apigw_route in config['Routes']:

            route_name = apigw_route['Name']
            lambda_arn_smm = apigw_route['LambdaArn']
            integration_method = apigw_route['IntegrationMethod']
            route_key = apigw_route['RouteKey']

            # Retrive Lambda ARN from SSM
            lambda_arn = aws_ssm.StringParameter.from_string_parameter_name(
                self,
                f"{route_name}-lambda-arn",
                string_parameter_name=lambda_arn_smm,
            ).string_value
            # lambda_arn = "arn:aws:lambda:us-east-2:338459378644:function:cdk-simple-app-dev-create-item"

            cfn_integration = apigatewayv2.CfnIntegration(self, f"{config['NamePrefix']}-{route_name}-api-gw-integration",
                    api_id=cfn_api.attr_api_id,
                    integration_type="AWS_PROXY",
                    integration_uri=f"arn:{self.partition}:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
                    # integration_method=integration_method,
                    integration_method="POST",
                    payload_format_version="2.0"
            )
            # cfn_integration.add_depends_on(apigw_stage)

            
            cfn_route = apigatewayv2.CfnRoute(self, f"{config['NamePrefix']}-{route_name}-api-gw-route",
                api_id=cfn_api.attr_api_id,
                route_key=f"{integration_method} {route_key}",
                target=f"integrations/{cfn_integration.ref}"
            )

            # cfn_route.add_depends_on(cfn_integration)
            # cfn_route.add_depends_on(cfn_api)

            

        cfn_deployment = apigatewayv2.CfnDeployment(self, f"{config['NamePrefix']}-api-gw-deployment",
            api_id=cfn_api.attr_api_id,

            description=f"{config['Description']}",
            stage_name=stage
        )

        # cfn_deployment.add_depends_on(apigw_stage)
        # cfn_deployment.add_depends_on(cfn_api)


        # Api Gateway Invoke Url ssm
        invoke_url = f"https://{cfn_api.attr_api_id}.execute-api.{self.region}.amazonaws.com"
        aws_ssm.StringParameter(self, f"apigw-invoke-url",
            parameter_name=f"/cdk/{config['Application']}/{config['Stage']}/apigw/invokeurl",
            string_value=invoke_url
        )