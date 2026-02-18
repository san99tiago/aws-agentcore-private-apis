import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class EndpointsStack(cdk.Stack):
    def __init__(
        self, scope: Construct, construct_id: str, vpc: ec2.Vpc, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = config["resources_name"]

        # Gateway Endpoint for DynamoDB
        ec2.GatewayVpcEndpoint(
            self,
            "DynamoDbEndpoint",
            vpc=vpc,
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB,
        )

        # Gateway Endpoint for S3
        ec2.GatewayVpcEndpoint(
            self,
            "S3Endpoint",
            vpc=vpc,
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # Interface Endpoint for execute-api in private subnets with private DNS
        api_endpoint = ec2.InterfaceVpcEndpoint(
            self,
            "ExecuteApiEndpoint",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointAwsService.APIGATEWAY,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            private_dns_enabled=True,
        )

        # Expose the VPC Endpoint ID for API stacks to reference in resource policies
        self.api_vpce_id = api_endpoint.vpc_endpoint_id
