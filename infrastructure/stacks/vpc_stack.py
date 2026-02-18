import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class VpcStack(cdk.Stack):
    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = config["resources_name"]
        env_suffix = config["deployment_environment"]
        vpc_name = config["vpc_name"]
        public_subnet = config["public_subnet_name"]
        private_subnet = config["private_subnet_name"]

        self.vpc = ec2.Vpc(
            self,
            "AgenticDemosVpc",
            vpc_name=f"{prefix}-{vpc_name}-{env_suffix}",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{prefix}-{public_subnet}-{env_suffix}",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name=f"{prefix}-{private_subnet}-{env_suffix}",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
