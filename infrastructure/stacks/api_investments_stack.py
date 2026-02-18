import json
import os

import aws_cdk as cdk
from aws_cdk import (
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class ApiInvestmentsStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = config["resources_name"]
        env_suffix = config["deployment_environment"]

        # DynamoDB table
        table = dynamodb.Table(
            self,
            "InvestmentsTable",
            table_name=f"{prefix}-investments-table-{env_suffix}",
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Lambda function
        investments_lambda = _lambda.Function(
            self,
            "InvestmentProductsFunction",
            function_name=f"{prefix}-investment-products-fn-{env_suffix}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "lambdas",
                    "investment_products",
                )
            ),
            environment={"TABLE_NAME": table.table_name},
        )

        table.grant_read_data(investments_lambda)

        # Load OpenAPI schema and substitute LambdaArn
        openapi_path = os.path.join(
            os.path.dirname(__file__), "..", "openapi", "investment-products-api.json"
        )
        with open(openapi_path, "r") as f:
            openapi_schema = json.load(f)

        self._replace_lambda_arn(openapi_schema, investments_lambda.function_arn)

        # PUBLIC REST API Gateway with API Key required
        api = apigw.SpecRestApi(
            self,
            "InvestmentProductsApi",
            rest_api_name=f"{prefix}-investment-products-api-{env_suffix}",
            api_definition=apigw.ApiDefinition.from_inline(openapi_schema),
            endpoint_types=[apigw.EndpointType.REGIONAL],
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        # Create API Key
        api_key = apigw.ApiKey(
            self,
            "InvestmentsApiKey",
            api_key_name=f"{prefix}-investments-api-key-{env_suffix}",
            enabled=True,
        )

        # Create Usage Plan and attach API Key
        usage_plan = apigw.UsagePlan(
            self,
            "InvestmentsUsagePlan",
            name=f"{prefix}-investments-usage-plan-{env_suffix}",
            api_stages=[
                apigw.UsagePlanPerApiStage(
                    api=api,
                    stage=api.deployment_stage,
                )
            ],
            throttle=apigw.ThrottleSettings(
                rate_limit=100,
                burst_limit=50,
            ),
        )

        usage_plan.add_api_key(api_key)

        # Grant API Gateway permission to invoke Lambda
        investments_lambda.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=api.arn_for_execute_api(),
        )

        # Expose outputs
        self.table_name = table.table_name
        self.api_url = api.url

        # CfnOutputs
        cdk.CfnOutput(
            self, "ApiUrl", value=api.url, description="Investment Products API URL"
        )
        cdk.CfnOutput(
            self,
            "ApiKeyId",
            value=api_key.key_id,
            description="API Key ID (retrieve value from console or CLI)",
        )

    @staticmethod
    def _replace_lambda_arn(schema: dict, lambda_arn: str) -> None:
        if isinstance(schema, dict):
            if "Fn::Sub" in schema:
                template = schema["Fn::Sub"]
                if isinstance(template, str) and "${LambdaArn}" in template:
                    schema.clear()
                    schema["Fn::Sub"] = [
                        "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaArn}/invocations",
                        {"LambdaArn": lambda_arn},
                    ]
                return
            for value in schema.values():
                ApiInvestmentsStack._replace_lambda_arn(value, lambda_arn)
        elif isinstance(schema, list):
            for item in schema:
                ApiInvestmentsStack._replace_lambda_arn(item, lambda_arn)
