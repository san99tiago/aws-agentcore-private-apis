#!/usr/bin/env python3
"""CDK App entry point - Instantiates all stacks with cross-stack references."""
import os
import sys

# Add project root to path so infrastructure package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import aws_cdk as cdk

from infrastructure.stacks.vpc_stack import VpcStack
from infrastructure.stacks.endpoints_stack import EndpointsStack
from infrastructure.stacks.bastion_stack import BastionStack
from infrastructure.stacks.api_datafonos_stack import ApiDatafonosStack
from infrastructure.stacks.api_balance_stack import ApiBalanceStack
from infrastructure.stacks.api_atm_stack import ApiAtmStack

app = cdk.App()

# Load appconfig from cdk.json context
config = app.node.try_get_context("appconfig")

# Base networking
vpc_stack = VpcStack(app, "VpcStack", config=config)

# VPC Endpoints (depends on VPC)
endpoints_stack = EndpointsStack(
    app, "EndpointsStack", vpc=vpc_stack.vpc, config=config
)

# Bastion host (depends on VPC)
bastion_stack = BastionStack(app, "BastionStack", vpc=vpc_stack.vpc, config=config)

# API stacks (depend on VPC + Endpoints)
api_datafonos_stack = ApiDatafonosStack(
    app,
    "ApiDatafonosStack",
    vpc=vpc_stack.vpc,
    vpce_id=endpoints_stack.api_vpce_id,
    config=config,
)
api_balance_stack = ApiBalanceStack(
    app,
    "ApiBalanceStack",
    vpc=vpc_stack.vpc,
    vpce_id=endpoints_stack.api_vpce_id,
    config=config,
)
api_atm_stack = ApiAtmStack(
    app,
    "ApiAtmStack",
    vpc=vpc_stack.vpc,
    vpce_id=endpoints_stack.api_vpce_id,
    config=config,
)

app.synth()
