from aws_cdk import (
    aws_events,
    aws_events_targets as targets,
    aws_kms,
    aws_sns,
    aws_sns_subscriptions as sns_sub,
    aws_ssm,
    aws_s3,
    aws_s3_deployment as s3_deployment,
    Stack,
    aws_iam
)
import os
from constructs import Construct


class S3DeploymentBucket(Stack):

    def __init__(self, scope: Construct, sid: str, config: dict, **kwargs) -> None:
        super().__init__(scope, sid, **kwargs)

        bucket_name = config["BucketName"]

        # Define the CORS rules
        cors_rule = aws_s3.CorsRule(
            allowed_methods=[aws_s3.HttpMethods.GET],  # Allowed HTTP methods
            allowed_origins=["*"],  # Allow all origins,
            allowed_headers=["*"],  # Allow all headers
            exposed_headers=[],  # Headers that are exposed to the browser
            max_age=3000  # Cache the response for 3000 seconds
        )
        s3_deployment_bucket = aws_s3.Bucket(
            self, f"{config['NamePrefix']}-{bucket_name}",
            bucket_name=f"{config['NamePrefix']}-{bucket_name}",
            versioned=True,
            # enforce_ssl=True,
            cors=[cors_rule],
            block_public_access=aws_s3.BlockPublicAccess(
                block_public_policy=False,
                block_public_acls=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
                ),
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            object_ownership=aws_s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            # public_read_access=True,
            website_index_document="index.html"
            )
        

        s3_deployment_bucket.add_to_resource_policy(aws_iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[f"{s3_deployment_bucket.bucket_arn}/*"],
            principals=[aws_iam.StarPrincipal()]
        ))
        
        sources=[s3_deployment.Source.asset(os.path.join(os.path.abspath(os.curdir), "./client/build"))]
        print(sources)
        s3_deployment.BucketDeployment(
            self,
            f"{config['NamePrefix']}-bucket-deployment",
            # sources=[s3_deployment.Source.asset("../client/build")],
            sources=sources,
            destination_bucket=s3_deployment_bucket)
        
        
        

        s3_url = f"https://{s3_deployment_bucket.bucket_name}.s3.amazonaws.com"
        # s3 Invoke Url ssm
        aws_ssm.StringParameter(self, f"bucket-deployment-url",
            parameter_name=f"/cdk/{config['Application']}/{config['Environment']}/s3deployment/bucketurl",
            # string_value=s3_deployment_bucket.bucket_domain_name
            string_value=s3_url
        )
        aws_ssm.StringParameter(self, f"bucket-deployment-name",
            parameter_name=f"/cdk/{config['Application']}/{config['Environment']}/s3deployment/bucketname",
            string_value=s3_deployment_bucket.bucket_name
        )