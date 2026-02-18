#!/usr/bin/env python3
"""
Script para poblar la tabla DynamoDB de balances con cuentas simuladas.
Genera cuentas de ahorro y/o corriente con datos financieros realistas en COP.

Uso: python setup/populate_balances.py TABLE_NAME
"""

import sys
import random
import logging
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USER_ACCOUNTS = {
    "santi": ["savings", "checking"],
    "moni": ["savings", "checking"],
    "jero": ["savings", "checking"],
    "joachim": ["savings", "checking"],
    "fabi": ["savings"],
    "chucho": ["savings", "checking"],
    "herb": ["savings", "checking"],
    "vale": ["checking"],
    "naz": ["savings", "checking"],
    "javi": ["savings", "checking"],
    "elkin": ["savings"],
}

BALANCE_RANGES = {
    "savings": (1_000_000, 50_000_000),
    "checking": (500_000, 15_000_000),
}


def generate_last_updated():
    now = datetime.now(timezone.utc)
    delta = timedelta(
        days=random.randint(0, 7),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (now - delta).isoformat().replace("+00:00", "Z")


def generate_balance(account_type):
    min_bal, max_bal = BALANCE_RANGES[account_type]
    return round(random.randint(min_bal, max_bal), -3)


def generate_balances():
    items = []
    for username, account_types in USER_ACCOUNTS.items():
        for account_type in account_types:
            balance = generate_balance(account_type)
            items.append(
                {
                    "PK": {"S": f"USER#{username}"},
                    "SK": {"S": f"ACCOUNT#{account_type}"},
                    "username": {"S": username},
                    "account_type": {"S": account_type},
                    "balance": {"N": str(balance)},
                    "currency": {"S": "COP"},
                    "last_updated": {"S": generate_last_updated()},
                }
            )
    return items


def write_to_dynamodb(table_name, items):
    client = boto3.client("dynamodb")

    try:
        client.describe_table(TableName=table_name)
        logger.info(f"Tabla '{table_name}' encontrada.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            logger.error(
                f"La tabla '{table_name}' no existe. "
                "Despliega la infraestructura primero con 'cdk deploy'."
            )
            sys.exit(1)
        raise

    total = len(items)
    written = 0

    for batch_start in range(0, total, 25):
        batch = items[batch_start : batch_start + 25]
        request_items = {table_name: [{"PutRequest": {"Item": item}} for item in batch]}
        try:
            response = client.batch_write_item(RequestItems=request_items)
            unprocessed = response.get("UnprocessedItems", {})
            retries = 0
            while unprocessed and retries < 3:
                retries += 1
                logger.warning(
                    f"Reintentando {len(unprocessed.get(table_name, []))} "
                    f"items no procesados (intento {retries}/3)..."
                )
                response = client.batch_write_item(RequestItems=unprocessed)
                unprocessed = response.get("UnprocessedItems", {})
            if unprocessed:
                unprocessed_count = len(unprocessed.get(table_name, []))
                logger.error(
                    f"No se pudieron escribir {unprocessed_count} "
                    "items después de 3 reintentos."
                )
            written += len(batch)
            logger.info(f"Progreso: {written}/{total} cuentas escritas.")
        except ClientError as e:
            logger.error(f"Error escribiendo lote: {e.response['Error']['Message']}")
            raise

    logger.info(f"Escritura completada: {written} cuentas en '{table_name}'.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python setup/populate_balances.py TABLE_NAME")
        sys.exit(1)

    table_name = sys.argv[1]
    logger.info(f"Generando cuentas para tabla '{table_name}'...")

    items = generate_balances()
    savings = sum(1 for i in items if i["account_type"]["S"] == "savings")
    checking = sum(1 for i in items if i["account_type"]["S"] == "checking")
    logger.info(
        f"Generadas {len(items)} cuentas para "
        f"{len(USER_ACCOUNTS)} usuarios: "
        f"{savings} ahorro, {checking} corrientes."
    )

    write_to_dynamodb(table_name, items)
    logger.info("Población de balances completada exitosamente!")


if __name__ == "__main__":
    main()
