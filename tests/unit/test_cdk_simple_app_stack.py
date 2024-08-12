import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_simple_app.cdk_simple_app_stack import CdkSimpleAppStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_simple_app/cdk_simple_app_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkSimpleAppStack(app, "cdk-simple-app")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
