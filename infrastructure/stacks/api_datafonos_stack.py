import json
import os

import aws_cdk as cdk
from aws_cdk import (
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class ApiDatafonosStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        vpce_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = config["resources_name"]
        env_suffix = config["deployment_environment"]
        table_name_cfg = config["datafonos_table_name"]
        lambda_name_cfg = config["datafonos_lambda_name"]
        api_name_cfg = config["datafonos_api_name"]

        # DynamoDB table with Single Table Design (PK + SK)
        table = dynamodb.Table(
            self,
            "DatafonosTable",
            table_name=f"{prefix}-{table_name_cfg}-{env_suffix}",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Lambda function for datafonos health API
        datafonos_lambda = _lambda.Function(
            self,
            "DatafonosHealthFunction",
            function_name=f"{prefix}-{lambda_name_cfg}-{env_suffix}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "lambdas", "datafonos_health"
                )
            ),
            environment={"TABLE_NAME": table.table_name},
        )

        # Grant Lambda read access to the DynamoDB table
        table.grant_read_data(datafonos_lambda)

        # Load OpenAPI schema and substitute LambdaArn placeholder
        openapi_path = os.path.join(
            os.path.dirname(__file__), "..", "openapi", "datafonos-health-api.json"
        )
        with open(openapi_path, "r") as f:
            openapi_schema = json.load(f)

        # Replace Fn::Sub placeholders with actual Lambda ARN
        self._replace_lambda_arn(openapi_schema, datafonos_lambda.function_arn)

        # Private REST API Gateway from OpenAPI schema
        api = apigw.SpecRestApi(
            self,
            "DatafonosHealthApi",
            rest_api_name=f"{prefix}-{api_name_cfg}-{env_suffix}",
            api_definition=apigw.ApiDefinition.from_inline(openapi_schema),
            endpoint_types=[apigw.EndpointType.PRIVATE],
            policy=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        principals=[iam.AnyPrincipal()],
                        actions=["execute-api:Invoke"],
                        resources=["execute-api:/*"],
                        conditions={
                            "StringEquals": {
                                "aws:sourceVpce": vpce_id,
                            }
                        },
                    )
                ]
            ),
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        # Grant API Gateway permission to invoke the Lambda function
        datafonos_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=api.arn_for_execute_api(),
        )

        # Expose table name for setup scripts
        self.table_name = table.table_name

    @staticmethod
    def _replace_lambda_arn(schema: dict, lambda_arn: str) -> None:
        """Recursively replace Fn::Sub LambdaArn placeholders with Fn::Join using the actual Lambda ARN."""
        if isinstance(schema, dict):
            if "Fn::Sub" in schema:
                template = schema["Fn::Sub"]
                if isinstance(template, str) and "${LambdaArn}" in template:
                    # Split the template around ${LambdaArn} and ${AWS::Region}
                    # Build a Fn::Sub with explicit variable mapping for LambdaArn
                    schema.clear()
                    schema["Fn::Sub"] = [
                        "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaArn}/invocations",
                        {"LambdaArn": lambda_arn},
                    ]
                return
            for value in schema.values():
                ApiDatafonosStack._replace_lambda_arn(value, lambda_arn)
        elif isinstance(schema, list):
            for item in schema:
                ApiDatafonosStack._replace_lambda_arn(item, lambda_arn)
