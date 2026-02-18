# Implementation Plan: Agentic Demos Infrastructure

## Overview

Implementación incremental de la infraestructura AWS CDK en Python. Se comienza con la estructura del proyecto y dependencias, luego los stacks base (VPC, Endpoints, Bastion), seguido de los API stacks con sus Lambda functions y OpenAPI schemas, y finalmente los scripts de población de datos. Cada paso construye sobre el anterior.

## Tasks

- [x] 1. Inicializar proyecto con Poetry y estructura de carpetas
  - [x] 1.1 Create `pyproject.toml` with Poetry configuration, aws-cdk-lib, constructs, and boto3 dependencies. Set virtualenv name to `.venv`
    - Include project metadata and Python version constraint (>=3.9)
    - Dependencies: aws-cdk-lib, constructs, boto3
    - _Requirements: 8.1_
  - [x] 1.2 Create `cdk.json` pointing to `infrastructure/app.py` as the CDK app entry point
    - _Requirements: 8.6_
  - [x] 1.3 Create directory structure: `infrastructure/stacks/`, `infrastructure/openapi/`, `lambdas/datafonos_health/`, `lambdas/get_balance/`, `lambdas/atm_machines_health/`, `setup/`
    - Add `__init__.py` files where needed
    - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [x] 2. Implement VPC Stack
  - [x] 2.1 Create `infrastructure/stacks/vpc_stack.py` with VPC, public subnets named "public-subnet-agentic-demos", private subnets named "private-subnet-agentic-demos", 2 AZs
    - Expose `self.vpc` as stack output for cross-stack references
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Implement VPC Endpoints Stack
  - [x] 3.1 Create `infrastructure/stacks/endpoints_stack.py` that receives VPC and creates Gateway Endpoints for DynamoDB and S3, and Interface Endpoint for execute-api in private subnets with private DNS enabled
    - Expose `self.api_vpce_id` for API stacks to reference in resource policies
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. Implement Bastion Host Stack
  - [x] 4.1 Create `infrastructure/stacks/bastion_stack.py` with EC2 instance in public subnet, Amazon Linux 2023 AMI, IAM role with AmazonSSMManagedInstanceCore policy, no SSH key pair
    - Configure security group to allow outbound traffic to VPC CIDR
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Checkpoint - Verify base infrastructure stacks
  - Ensure `cdk synth` runs successfully for VpcStack, EndpointsStack, and BastionStack. Ask the user if questions arise.

- [x] 6. Implement Datafonos Health API Stack
  - [x] 6.1 Create OpenAPI schema `infrastructure/openapi/datafonos-health-api.json` with GET /datafonos and GET /datafonos/{city} endpoints, including x-amazon-apigateway-integration for Lambda proxy
    - _Requirements: 4.1_
  - [x] 6.2 Create Lambda function `lambdas/datafonos_health/index.py` that reads TABLE_NAME from env, queries DynamoDB by city (PK=CITY#city) or scans all, returns JSON response with proper status codes and error handling
    - _Requirements: 4.2, 4.4_
  - [x] 6.3 Create `infrastructure/stacks/api_datafonos_stack.py` that receives VPC and vpce_id, creates DynamoDB table (PK string, SK string, PAY_PER_REQUEST), Lambda function with Python runtime, Private API Gateway from OpenAPI schema with resource policy restricting to VPC Endpoint, and grants Lambda read access to table
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Implement Get Balance API Stack
  - [x] 7.1 Create OpenAPI schema `infrastructure/openapi/get-balance-api.json` with GET /balance/{username} endpoint, including x-amazon-apigateway-integration for Lambda proxy
    - _Requirements: 5.1_
  - [x] 7.2 Create Lambda function `lambdas/get_balance/index.py` that reads TABLE_NAME from env, queries DynamoDB by username (PK=USER#username), returns JSON response with balance data and proper error handling
    - _Requirements: 5.2, 5.4_
  - [x] 7.3 Create `infrastructure/stacks/api_balance_stack.py` following same pattern as datafonos stack: DynamoDB table, Lambda, Private API Gateway from OpenAPI schema with resource policy, read permissions
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 8. Implement ATM Machines Health API Stack
  - [x] 8.1 Create OpenAPI schema `infrastructure/openapi/atm-machines-health-api.json` with GET /atms and GET /atms/{city} endpoints, including x-amazon-apigateway-integration for Lambda proxy
    - _Requirements: 6.1_
  - [x] 8.2 Create Lambda function `lambdas/atm_machines_health/index.py` that reads TABLE_NAME from env, queries DynamoDB by city (PK=CITY#city) or scans all, returns JSON response with proper status codes and error handling
    - _Requirements: 6.2, 6.4_
  - [x] 8.3 Create `infrastructure/stacks/api_atm_stack.py` following same pattern as datafonos stack: DynamoDB table, Lambda, Private API Gateway from OpenAPI schema with resource policy, read permissions
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 9. Wire all stacks together in CDK App
  - [x] 9.1 Create `infrastructure/app.py` that instantiates all stacks (VpcStack, EndpointsStack, BastionStack, ApiDatafonosStack, ApiBalanceStack, ApiAtmStack) with proper cross-stack references and dependency order
    - Pass vpc from VpcStack to all dependent stacks
    - Pass api_vpce_id from EndpointsStack to all API stacks
    - _Requirements: 8.2_

- [x] 10. Checkpoint - Verify all CDK stacks synthesize
  - Ensure `cdk synth` runs successfully for all stacks. Ask the user if questions arise.

- [x] 11. Implement Setup Scripts for Data Population
  - [x] 11.1 Create `setup/populate_datafonos.py` that generates 100 datafonos with realistic data (device_id, merchant_name, address, lat/lon coordinates in Medellín and Bogotá, status, last_transaction) and writes to DynamoDB using batch_write_item
    - Use PK=CITY#city, SK=DATAFONO#device_id pattern
    - Include realistic Colombian addresses and coordinates
    - _Requirements: 7.1, 7.4_
  - [x] 11.2 Create `setup/populate_atms.py` that generates 25 ATMs with realistic data (atm_id, address, lat/lon coordinates in Medellín and Bogotá, status, cash_level, last_service) and writes to DynamoDB using batch_write_item
    - Use PK=CITY#city, SK=ATM#atm_id pattern
    - Include realistic Colombian addresses and coordinates
    - _Requirements: 7.2, 7.4_
  - [x] 11.3 Create `setup/populate_balances.py` that generates accounts for users (santi, moni, jero, joachim, fabi, chucho, herb, vale, naz, javi, elkin) with realistic financial data (balance in COP, account_type, currency) and writes to DynamoDB using batch_write_item
    - Use PK=USER#username, SK=ACCOUNT#account_type pattern
    - Each user gets savings and/or checking accounts
    - _Requirements: 7.3, 7.5_

- [x] 12. Final Checkpoint - Full project verification
  - Ensure `cdk synth` passes for all stacks, all files are in place, and project structure matches requirements. Ask the user if questions arise.

## Notes

- No se incluyen unit tests por indicación del usuario
- Cada tarea referencia los requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental con `cdk synth`
- Los API stacks siguen un patrón común (DynamoDB + Lambda + Private API Gateway)
- Los setup scripts usan batch_write_item para eficiencia
