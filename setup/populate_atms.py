#!/usr/bin/env python3
"""
Script para poblar la tabla DynamoDB de cajeros automáticos (ATMs) con 25 registros simulados.
Genera ATMs con datos realistas en Medellín y Bogotá, Colombia.

Uso: python setup/populate_atms.py TABLE_NAME
"""

import sys
import uuid
import random
import logging
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Datos realistas colombianos para ATMs ---

ATM_LOCATIONS_MEDELLIN = [
    "Bancolombia El Poblado - Cra 43A #1-50, El Poblado",
    "Banco de Bogotá Laureles - Cra 70 #44-30, Laureles",
    "BBVA Centro Comercial Santafé - Calle 7 Sur #43A-200, El Poblado",
    "Davivienda Unicentro - Cra 66B #34A-76, Laureles",
    "Bancolombia Oviedo - Cra 43A #6 Sur-15, El Poblado",
    "Banco Popular Estación Poblado - Calle 10 #43E-31, El Poblado",
    "Scotiabank Colpatria La 70 - Cra 70 #48-20, Estadio",
    "Bancolombia Centro - Calle 52 #49-40, Centro",
    "Davivienda Belén - Calle 33 #76-20, Belén",
    "BBVA Envigado - Cra 43A #38 Sur-15, Envigado",
    "Banco de Bogotá La América - Cra 80 #32A-45, La América",
    "Bancolombia Suramericana - Cra 65 #48-10, Suramericana",
    "Nequi Punto ATM Provenza - Calle 10A #35-20, Provenza",
]

ATM_LOCATIONS_BOGOTA = [
    "Bancolombia Usaquén - Calle 116 #18-30, Usaquén",
    "Banco de Bogotá Zona Rosa - Calle 85 #15-10, Zona Rosa",
    "BBVA Centro Comercial Andino - Cra 11 #82-71, Zona T",
    "Davivienda Chapinero - Cra 7 #71-52, Chapinero",
    "Bancolombia Chicó - Cra 15 #93-20, Chicó",
    "Scotiabank Colpatria Calle 72 - Calle 72 #10-15, Centro Internacional",
    "Banco Popular Kennedy - Cra 68 #24-10, Kennedy",
    "Bancolombia Cedritos - Calle 140 #11-20, Cedritos",
    "Davivienda Galerías - Calle 53 #13-40, Galerías",
    "BBVA Suba - Cra 68 #80-20, Suba",
    "Banco de Bogotá Teusaquillo - Cra 30 #45-15, Teusaquillo",
    "Bancolombia Santa Bárbara - Calle 122 #15-40, Santa Bárbara",
]

STATUSES = ["online", "offline", "low_cash", "maintenance"]
STATUS_WEIGHTS = [0.5, 0.15, 0.2, 0.15]

CASH_LEVELS = ["high", "medium", "low", "empty"]
CASH_LEVEL_WEIGHTS = [0.3, 0.35, 0.25, 0.1]

# Rangos de coordenadas por ciudad
COORDS = {
    "medellin": {"lat_min": 6.2, "lat_max": 6.3, "lon_min": -75.6, "lon_max": -75.5},
    "bogota": {"lat_min": 4.6, "lat_max": 4.7, "lon_min": -74.1, "lon_max": -74.0},
}


def generate_coordinate(city: str) -> tuple:
    """Genera coordenadas aleatorias dentro del rango de la ciudad."""
    c = COORDS[city]
    lat = round(random.uniform(c["lat_min"], c["lat_max"]), 6)
    lon = round(random.uniform(c["lon_min"], c["lon_max"]), 6)
    return lat, lon


def generate_last_service() -> str:
    """Genera un timestamp de último servicio en los últimos 90 días."""
    now = datetime.utcnow()
    delta = timedelta(
        days=random.randint(0, 90),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (now - delta).isoformat() + "Z"


def generate_atms(count: int = 25) -> list:
    """Genera una lista de ATMs con datos realistas."""
    atms = []
    # Dividir entre Medellín (~13) y Bogotá (~12)
    medellin_count = 13
    bogota_count = count - medellin_count

    for i in range(medellin_count):
        atm_id = str(uuid.uuid4())
        lat, lon = generate_coordinate("medellin")
        address = ATM_LOCATIONS_MEDELLIN[i % len(ATM_LOCATIONS_MEDELLIN)]
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        cash_level = random.choices(CASH_LEVELS, weights=CASH_LEVEL_WEIGHTS, k=1)[0]

        atms.append(
            {
                "PK": {"S": "CITY#medellin"},
                "SK": {"S": f"ATM#{atm_id}"},
                "atm_id": {"S": atm_id},
                "address": {"S": address},
                "latitude": {"N": str(lat)},
                "longitude": {"N": str(lon)},
                "status": {"S": status},
                "cash_level": {"S": cash_level},
                "last_service": {"S": generate_last_service()},
                "city": {"S": "medellin"},
            }
        )

    for i in range(bogota_count):
        atm_id = str(uuid.uuid4())
        lat, lon = generate_coordinate("bogota")
        address = ATM_LOCATIONS_BOGOTA[i % len(ATM_LOCATIONS_BOGOTA)]
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        cash_level = random.choices(CASH_LEVELS, weights=CASH_LEVEL_WEIGHTS, k=1)[0]

        atms.append(
            {
                "PK": {"S": "CITY#bogota"},
                "SK": {"S": f"ATM#{atm_id}"},
                "atm_id": {"S": atm_id},
                "address": {"S": address},
                "latitude": {"N": str(lat)},
                "longitude": {"N": str(lon)},
                "status": {"S": status},
                "cash_level": {"S": cash_level},
                "last_service": {"S": generate_last_service()},
                "city": {"S": "bogota"},
            }
        )

    return atms


def write_to_dynamodb(table_name: str, items: list) -> None:
    """Escribe items a DynamoDB usando batch_write_item en lotes de 25."""
    client = boto3.client("dynamodb")

    # Verificar que la tabla existe
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

    # Procesar en lotes de 25 (límite de batch_write_item)
    for batch_start in range(0, total, 25):
        batch = items[batch_start : batch_start + 25]
        request_items = {table_name: [{"PutRequest": {"Item": item}} for item in batch]}

        try:
            response = client.batch_write_item(RequestItems=request_items)

            # Manejar unprocessed items con reintentos
            unprocessed = response.get("UnprocessedItems", {})
            retries = 0
            while unprocessed and retries < 3:
                retries += 1
                logger.warning(
                    f"Reintentando {len(unprocessed.get(table_name, []))} items "
                    f"no procesados (intento {retries}/3)..."
                )
                response = client.batch_write_item(RequestItems=unprocessed)
                unprocessed = response.get("UnprocessedItems", {})

            if unprocessed:
                logger.error(
                    f"No se pudieron escribir {len(unprocessed.get(table_name, []))} items "
                    "después de 3 reintentos."
                )

            written += len(batch)
            logger.info(f"Progreso: {written}/{total} ATMs escritos.")

        except ClientError as e:
            logger.error(f"Error escribiendo lote: {e.response['Error']['Message']}")
            raise

    logger.info(f"Escritura completada: {written} ATMs en tabla '{table_name}'.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python setup/populate_atms.py TABLE_NAME")
        sys.exit(1)

    table_name = sys.argv[1]
    logger.info(f"Generando 25 ATMs para tabla '{table_name}'...")

    atms = generate_atms(25)
    logger.info(
        f"Generados {len(atms)} ATMs: "
        f"{sum(1 for a in atms if a['city']['S'] == 'medellin')} en Medellín, "
        f"{sum(1 for a in atms if a['city']['S'] == 'bogota')} en Bogotá."
    )

    write_to_dynamodb(table_name, atms)
    logger.info("¡Población de ATMs completada exitosamente!")


if __name__ == "__main__":
    main()
