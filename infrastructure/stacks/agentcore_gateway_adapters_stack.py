import os

import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class AgentCoreGatewayAdaptersStack(cdk.Stack):
    """CDK Stack for Lambda adapter functions that proxy requests from
    AgentCore Gateway to Private API Gateways inside the VPC.

    These Lambdas run in the VPC private subnets so they can reach
    the Private APIs via the execute-api VPC Endpoint.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        datafonos_api_url: str,
        balance_api_url: str,
        atm_api_url: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = config["resources_name"]
        env_suffix = config["deployment_environment"]

        # Security group for adapter Lambdas - needs HTTPS outbound to VPC
        adapter_sg = ec2.SecurityGroup(
            self,
            "AdapterSecurityGroup",
            vpc=vpc,
            security_group_name=f"{prefix}-adapter-sg-{env_suffix}",
            description="Security group for AgentCore Gateway adapter Lambdas",
            allow_all_outbound=False,
        )

        # Allow HTTPS outbound to VPC CIDR (to reach Private API via VPC Endpoint)
        adapter_sg.add_egress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS to VPC for Private API access",
        )

        # ── Datafonos Adapter Lambda ──
        self.datafonos_adapter = _lambda.Function(
            self,
            "DatafonosAdapterFunction",
            function_name=f"{prefix}-adapter-datafonos-{env_suffix}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "lambdas",
                    "adapter_datafonos",
                )
            ),
            environment={"API_BASE_URL": datafonos_api_url},
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[adapter_sg],
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
        )

        # ── Balance Adapter Lambda ──
        self.balance_adapter = _lambda.Function(
            self,
            "BalanceAdapterFunction",
            function_name=f"{prefix}-adapter-balance-{env_suffix}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "lambdas", "adapter_balance"
                )
            ),
            environment={"API_BASE_URL": balance_api_url},
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[adapter_sg],
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
        )

        # ── ATM Adapter Lambda ──
        self.atm_adapter = _lambda.Function(
            self,
            "AtmAdapterFunction",
            function_name=f"{prefix}-adapter-atm-{env_suffix}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", "lambdas", "adapter_atm"
                )
            ),
            environment={"API_BASE_URL": atm_api_url},
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[adapter_sg],
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
        )

        # ── CfnOutputs for Lambda ARNs (useful for AgentCore Gateway config) ──
        cdk.CfnOutput(
            self,
            "DatafonosAdapterArn",
            value=self.datafonos_adapter.function_arn,
            description="ARN of the Datafonos adapter Lambda",
        )
        cdk.CfnOutput(
            self,
            "BalanceAdapterArn",
            value=self.balance_adapter.function_arn,
            description="ARN of the Balance adapter Lambda",
        )
        cdk.CfnOutput(
            self,
            "AtmAdapterArn",
            value=self.atm_adapter.function_arn,
            description="ARN of the ATM adapter Lambda",
        )
