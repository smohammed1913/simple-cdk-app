from aws_cdk import (
    aws_events,
    aws_events_targets as targets,
    aws_kms,
    aws_sns,
    aws_sns_subscriptions as sns_sub,
    aws_ssm,
    aws_apigatewayv2,
    Stack,
    aws_iam
)

from constructs import Construct


class SNSNotification(Stack):

    def __init__(self, scope: Construct, sid: str, config: dict, **kwargs) -> None:
        super().__init__(scope, sid, **kwargs)

        sns_notifications = config.get('SNSNotifications', [])

        for sns_notification in sns_notifications:

            ## SNS Topic
            self.topic = aws_sns.Topic(
                self,
                f"{sns_notification['NamePrefix']}-topic",
                topic_name=sns_notification['SNSTopicName']
                # master_key=aws_sns_kms
            )

            # Add custom principles
            aws_iam.PolicyDocument(
                assign_sids= True,
                statements=[
                    aws_iam.PolicyStatement(
                        actions=[
                            'sns:Publish'
                        ],
                        principals=[aws_iam.ServicePrincipal('lambda.amazonaws.com')],
                        resources=[self.topic.topic_arn],
                        effect=aws_iam.Effect.ALLOW
                    )
                ]
            )

            self.topic.add_to_resource_policy(aws_iam.PolicyStatement(
                        actions=[
                            'sns:Publish'
                        ],
                        principals=[aws_iam.ServicePrincipal('cloudwatch.amazonaws.com')],
                        resources=[self.topic.topic_arn],
                        effect=aws_iam.Effect.ALLOW
                    ))


            ## SNS Subscription
            self.topic.add_subscription(
                sns_sub.EmailSubscription(
                    email_address=sns_notification['SSMDefaultSubEmail']
                )
            )


