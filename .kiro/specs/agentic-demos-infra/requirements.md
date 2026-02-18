# Requirements Document

## Introduction

Proyecto de infraestructura AWS CDK en Python para desplegar un entorno de demos de agentes. El sistema consiste en múltiples APIs privadas respaldadas por funciones Lambda y tablas DynamoDB, accesibles únicamente desde una VPC a través de un bastion host EC2 con AWS SSM. La gestión de dependencias se realiza con Python Poetry y la infraestructura se organiza en stacks CDK independientes.

## Glossary

- **VPC_Stack**: Stack de CDK que crea la Virtual Private Cloud con subnets públicas y privadas
- **Endpoints_Stack**: Stack de CDK que crea los VPC Endpoints (Gateway e Interface) para servicios AWS
- **Bastion_Stack**: Stack de CDK que crea la instancia EC2 bastion host en subnet pública con acceso SSM
- **API_Stack**: Stack de CDK que crea un API Gateway privado con Lambda backend y tabla DynamoDB
- **Private_API_Gateway**: API Gateway de tipo PRIVATE accesible únicamente desde dentro de la VPC mediante VPC Endpoint
- **Bastion_Host**: Instancia EC2 en subnet pública que sirve como punto de acceso a recursos privados de la VPC
- **Single_Table_Design**: Patrón de diseño DynamoDB que usa una sola tabla con Partition Key (PK) y Sort Key (SK)
- **OpenAPI_Schema**: Especificación OpenAPI que define la estructura del API Gateway
- **Setup_Script**: Script Python que puebla las tablas DynamoDB con datos simulados
- **Poetry**: Herramienta de gestión de dependencias Python utilizada con convención de virtualenv `.venv`

## Requirements

### Requirement 1: VPC con Subnets Públicas y Privadas

**User Story:** Como ingeniero de infraestructura, quiero una VPC con subnets públicas y privadas, para que los recursos puedan desplegarse con el nivel de aislamiento de red apropiado.

#### Acceptance Criteria

1. THE VPC_Stack SHALL create a VPC with both public and private subnet tiers
2. WHEN the VPC is created, THE VPC_Stack SHALL name public subnets "public-subnet-agentic-demos"
3. WHEN the VPC is created, THE VPC_Stack SHALL name private subnets "private-subnet-agentic-demos"
4. THE VPC_Stack SHALL configure at least two Availability Zones for high availability

### Requirement 2: VPC Endpoints para Servicios AWS

**User Story:** Como ingeniero de infraestructura, quiero VPC Endpoints para DynamoDB, S3 y API Gateway, para que los recursos privados accedan a servicios AWS sin salir de la red de Amazon.

#### Acceptance Criteria

1. THE Endpoints_Stack SHALL create a VPC Gateway Endpoint for DynamoDB associated with the VPC
2. THE Endpoints_Stack SHALL create a VPC Gateway Endpoint for S3 associated with the VPC
3. THE Endpoints_Stack SHALL create a VPC Interface Endpoint for the execute-api service associated with the VPC
4. WHEN the execute-api Interface Endpoint is created, THE Endpoints_Stack SHALL place the endpoint in the private subnets of the VPC
5. WHEN the execute-api Interface Endpoint is created, THE Endpoints_Stack SHALL enable private DNS for the endpoint

### Requirement 3: Bastion Host EC2 con Acceso SSM

**User Story:** Como ingeniero de infraestructura, quiero un bastion host EC2 accesible vía SSM Session Manager, para que pueda acceder a recursos privados de la VPC sin necesidad de llaves SSH.

#### Acceptance Criteria

1. THE Bastion_Stack SHALL create an EC2 instance in a public subnet of the VPC
2. THE Bastion_Stack SHALL assign an IAM role to the EC2 instance with the AmazonSSMManagedInstanceCore managed policy
3. WHEN the bastion host is deployed, THE Bastion_Stack SHALL enable access via AWS SSM Session Manager without requiring SSH key pairs
4. WHEN a user connects to the bastion host via SSM, THE Bastion_Host SHALL have network connectivity to private subnet IP addresses
5. THE Bastion_Stack SHALL use an Amazon Linux 2023 AMI for the EC2 instance

### Requirement 4: API Privada de Salud de Datáfonos

**User Story:** Como desarrollador, quiero una API privada para consultar la salud de datáfonos, para que los agentes puedan verificar el estado de los dispositivos de pago.

#### Acceptance Criteria

1. THE API_Stack SHALL create a Private_API_Gateway for the datafonos-health API defined by an OpenAPI_Schema
2. THE API_Stack SHALL create a Lambda function in Python as backend for the datafonos-health API
3. THE API_Stack SHALL create a DynamoDB table using Single_Table_Design with PK and SK attributes for datafonos data
4. WHEN the Lambda function is invoked, THE Lambda function SHALL have read access to the datafonos DynamoDB table
5. WHEN the Private_API_Gateway is created, THE API_Stack SHALL configure a resource policy restricting access to the VPC Endpoint

### Requirement 5: API Privada de Consulta de Saldo

**User Story:** Como desarrollador, quiero una API privada para consultar saldos de usuarios, para que los agentes puedan obtener información financiera de los clientes.

#### Acceptance Criteria

1. THE API_Stack SHALL create a Private_API_Gateway for the get-balance API defined by an OpenAPI_Schema
2. THE API_Stack SHALL create a Lambda function in Python as backend for the get-balance API
3. THE API_Stack SHALL create a DynamoDB table using Single_Table_Design with PK and SK attributes for balance data
4. WHEN the Lambda function is invoked, THE Lambda function SHALL have read access to the balance DynamoDB table
5. WHEN the Private_API_Gateway is created, THE API_Stack SHALL configure a resource policy restricting access to the VPC Endpoint

### Requirement 6: API Privada de Salud de Cajeros Automáticos

**User Story:** Como desarrollador, quiero una API privada para consultar la salud de cajeros automáticos, para que los agentes puedan verificar el estado de los ATMs.

#### Acceptance Criteria

1. THE API_Stack SHALL create a Private_API_Gateway for the atm-machines-health API defined by an OpenAPI_Schema
2. THE API_Stack SHALL create a Lambda function in Python as backend for the atm-machines-health API
3. THE API_Stack SHALL create a DynamoDB table using Single_Table_Design with PK and SK attributes for ATM data
4. WHEN the Lambda function is invoked, THE Lambda function SHALL have read access to the ATM DynamoDB table
5. WHEN the Private_API_Gateway is created, THE API_Stack SHALL configure a resource policy restricting access to the VPC Endpoint

### Requirement 7: Scripts de Población de Datos

**User Story:** Como desarrollador, quiero scripts que pueblen las tablas DynamoDB con datos simulados, para que pueda probar las APIs con información realista.

#### Acceptance Criteria

1. THE Setup_Script SHALL populate the datafonos DynamoDB table with 100 simulated datafonos located in Medellín and Bogotá, Colombia
2. THE Setup_Script SHALL populate the ATM DynamoDB table with 25 simulated ATMs located in Medellín and Bogotá, Colombia
3. THE Setup_Script SHALL populate the balance DynamoDB table with accounts for users: "santi", "moni", "jero", "joachim", "fabi", "chucho", "herb", "vale", "naz", "javi", "elkin"
4. WHEN generating simulated data, THE Setup_Script SHALL include realistic attributes such as geographic coordinates, addresses, status, and device identifiers
5. WHEN generating user balance data, THE Setup_Script SHALL include realistic financial attributes such as account balance, account type, and currency

### Requirement 8: Estructura del Proyecto y Gestión de Dependencias

**User Story:** Como desarrollador, quiero una estructura de proyecto organizada con Poetry, para que el código sea mantenible y las dependencias estén gestionadas correctamente.

#### Acceptance Criteria

1. THE project SHALL use Python Poetry for dependency management with virtualenv name convention ".venv"
2. THE project SHALL organize CDK infrastructure code in an "infrastructure" folder with a "stacks" subfolder
3. THE project SHALL organize Lambda function code in a "lambdas" folder with separate subfolders per function
4. THE project SHALL organize OpenAPI schemas in an "infrastructure/openapi" folder
5. THE project SHALL organize data population scripts in a "setup" folder
6. THE project SHALL include a cdk.json configuration file at the project root pointing to the CDK app entry point
