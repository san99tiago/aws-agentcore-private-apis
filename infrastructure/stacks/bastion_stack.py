import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2, aws_iam as iam
from constructs import Construct


class BastionStack(cdk.Stack):
    def __init__(
        self, scope: Construct, construct_id: str, vpc: ec2.Vpc, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = config["resources_name"]
        env_suffix = config["deployment_environment"]
        bastion_name = config["bastion_name"]

        # IAM role with SSM managed policy for Session Manager access
        role = iam.Role(
            self,
            "BastionRole",
            role_name=f"{prefix}-{bastion_name}-role-{env_suffix}",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ],
        )

        # Security group allowing outbound traffic
        security_group = ec2.SecurityGroup(
            self,
            "BastionSecurityGroup",
            vpc=vpc,
            security_group_name=f"{prefix}-{bastion_name}-sg-{env_suffix}",
            description="Security group for bastion host",
            allow_all_outbound=False,
        )

        # Allow HTTPS outbound to internet (required for SSM Agent to communicate with AWS services)
        security_group.add_egress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS outbound for SSM Agent and AWS services",
        )

        # Allow all outbound traffic to VPC CIDR (for private API calls)
        security_group.add_egress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.all_traffic(),
            description="Allow outbound traffic to VPC CIDR",
        )

        # EC2 instance in public subnet with Amazon Linux 2023, no SSH key pair
        self.instance = ec2.Instance(
            self,
            "BastionHost",
            instance_name=f"{prefix}-{bastion_name}-{env_suffix}",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            role=role,
            security_group=security_group,
            associate_public_ip_address=True,
        )
