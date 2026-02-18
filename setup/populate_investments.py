#!/usr/bin/env python3
"""
Script para poblar la tabla DynamoDB de productos de inversión.
Genera inversiones para los 11 usuarios con productos colombianos realistas.

Uso: python setup/populate_investments.py TABLE_NAME
"""

import sys
import uuid
import random
import logging
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USERS = [
    "santi",
    "moni",
    "jero",
    "joachim",
    "fabi",
    "chucho",
    "herb",
    "vale",
    "naz",
    "javi",
    "elkin",
]

PRODUCTS = {
    "Fiduciaria": {
        "names": [
            "Fiducuenta Bancolombia",
            "Fidurenta",
            "Fiduciaria Davivienda",
            "Plan Semilla",
        ],
        "min_amount": 5_000_000,
        "max_amount": 200_000_000,
        "min_rate": 6.0,
        "max_rate": 12.0,
        "maturity_months": (6, 36),
    },
    "CDT": {
        "names": ["CDT 90 días", "CDT 180 días", "CDT 360 días", "CDT Digital"],
        "min_amount": 1_000_000,
        "max_amount": 100_000_000,
        "min_rate": 8.0,
        "max_rate": 14.5,
        "maturity_months": (3, 12),
    },
    "Crypto": {
        "names": ["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)", "USDT Staking"],
        "min_amount": 500_000,
        "max_amount": 50_000_000,
        "min_rate": -20.0,
        "max_rate": 45.0,
        "maturity_months": (0, 0),
    },
    "Bono": {
        "names": [
            "Bono Bancolombia 2026",
            "Bono Ecopetrol",
            "Bono ISA",
            "Bono Grupo Argos",
        ],
        "min_amount": 10_000_000,
        "max_amount": 500_000_000,
        "min_rate": 9.0,
        "max_rate": 13.0,
        "maturity_months": (12, 60),
    },
    "TES": {
        "names": [
            "TES Tasa Fija 2026",
            "TES Tasa Fija 2028",
            "TES UVR 2027",
            "TES Corto Plazo",
        ],
        "min_amount": 5_000_000,
        "max_amount": 300_000_000,
        "min_rate": 7.5,
        "max_rate": 12.5,
        "maturity_months": (12, 48),
    },
    "Cuenta Global": {
        "names": [
            "Cuenta USD Bancolombia",
            "Cuenta EUR Davivienda",
            "Global Account BBVA",
            "Multi-Currency Scotiabank",
        ],
        "min_amount": 2_000_000,
        "max_amount": 80_000_000,
        "min_rate": 1.0,
        "max_rate": 5.0,
        "maturity_months": (0, 0),
    },
    "Acciones": {
        "names": [
            "Bancolombia (CIB)",
            "Ecopetrol (EC)",
            "Grupo Argos (GRUPOARGOS)",
            "ISA (ISA)",
            "Nutresa (NUTRESA)",
        ],
        "min_amount": 1_000_000,
        "max_amount": 150_000_000,
        "min_rate": -15.0,
        "max_rate": 35.0,
        "maturity_months": (0, 0),
    },
}


STATUSES = ["active", "matured", "pending"]
STATUS_WEIGHTS = [0.75, 0.15, 0.10]


def generate_date_range(maturity_months_range):
    now = datetime.now(timezone.utc)
    start_delta = timedelta(days=random.randint(30, 365))
    start_date = now - start_delta

    min_m, max_m = maturity_months_range
    if max_m == 0:
        maturity_date = None
    else:
        maturity_days = random.randint(min_m * 30, max_m * 30)
        maturity_date = start_date + timedelta(days=maturity_days)

    return start_date.strftime("%Y-%m-%d"), (
        maturity_date.strftime("%Y-%m-%d") if maturity_date else "N/A"
    )


def generate_investments():
    items = []
    for username in USERS:
        # Each user gets 2-5 random investment products
        num_products = random.randint(2, 5)
        product_types = random.sample(
            list(PRODUCTS.keys()), min(num_products, len(PRODUCTS))
        )

        for product_type in product_types:
            config = PRODUCTS[product_type]
            product_name = random.choice(config["names"])
            invested = round(
                random.randint(config["min_amount"], config["max_amount"]), -3
            )
            rate = round(random.uniform(config["min_rate"], config["max_rate"]), 2)
            current_value = round(invested * (1 + rate / 100), -3)
            start_date, maturity_date = generate_date_range(config["maturity_months"])
            status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
            product_id = str(uuid.uuid4())[:8]

            item = {
                "PK": {"S": f"USER#{username}"},
                "SK": {"S": f"INVESTMENT#{product_type}#{product_id}"},
                "username": {"S": username},
                "product_type": {"S": product_type},
                "product_name": {"S": product_name},
                "invested_amount": {"N": str(invested)},
                "current_value": {"N": str(current_value)},
                "currency": {"S": "COP"},
                "return_rate": {"N": str(rate)},
                "start_date": {"S": start_date},
                "maturity_date": {"S": maturity_date},
                "status": {"S": status},
            }
            items.append(item)

    return items


def write_to_dynamodb(table_name, items):
    client = boto3.client("dynamodb")

    try:
        client.describe_table(TableName=table_name)
        logger.info(f"Tabla '{table_name}' encontrada.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            logger.error(
                f"La tabla '{table_name}' no existe. Despliega la infraestructura primero con 'cdk deploy'."
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
                    f"Reintentando {len(unprocessed.get(table_name, []))} items (intento {retries}/3)..."
                )
                response = client.batch_write_item(RequestItems=unprocessed)
                unprocessed = response.get("UnprocessedItems", {})
            written += len(batch)
            logger.info(f"Progreso: {written}/{total} inversiones escritas.")
        except ClientError as e:
            logger.error(f"Error escribiendo lote: {e.response['Error']['Message']}")
            raise

    logger.info(f"Escritura completada: {written} inversiones en '{table_name}'.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python setup/populate_investments.py TABLE_NAME")
        sys.exit(1)

    table_name = sys.argv[1]
    logger.info(f"Generando inversiones para tabla '{table_name}'...")

    items = generate_investments()
    product_counts = {}
    for item in items:
        pt = item["product_type"]["S"]
        product_counts[pt] = product_counts.get(pt, 0) + 1

    logger.info(f"Generadas {len(items)} inversiones para {len(USERS)} usuarios:")
    for pt, count in sorted(product_counts.items()):
        logger.info(f"  - {pt}: {count}")

    write_to_dynamodb(table_name, items)
    logger.info("Población de inversiones completada exitosamente!")


if __name__ == "__main__":
    main()
