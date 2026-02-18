#!/usr/bin/env python3
"""
Script para poblar la tabla DynamoDB de datáfonos con 100 registros simulados.
Genera datáfonos con datos realistas en Medellín y Bogotá, Colombia.

Uso: python setup/populate_datafonos.py TABLE_NAME
"""

import sys
import uuid
import random
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Datos realistas colombianos ---

MERCHANT_NAMES_MEDELLIN = [
    "Tienda Don Pedro",
    "Farmacia La Salud",
    "Panadería El Trigal",
    "Restaurante El Arriero",
    "Café Velvet",
    "Minimercado La Esquina",
    "Droguería Pasteur",
    "Carnicería El Novillo",
    "Frutería Tropical",
    "Papelería El Estudiante",
    "Ferretería El Maestro",
    "Tienda Naturista Vida Sana",
    "Peluquería Estilo",
    "Lavandería Express",
    "Miscelánea La 80",
    "Restaurante Mondongos",
    "Heladería Mimo's",
    "Cigarrería El Paisa",
    "Supermercado Euro",
    "Tienda D1 Laureles",
    "Restaurante Hatoviejo",
    "Café Pergamino",
    "Panadería Santa Elena",
    "Droguería La Rebaja",
    "Minimercado Don José",
    "Tienda Ara Envigado",
    "Restaurante El Herbario",
    "Frutería La Cosecha",
    "Papelería Panamericana",
    "Ferretería Homecenter",
    "Barbería Clásica",
    "Lavandería Clean Express",
    "Miscelánea El Poblado",
    "Restaurante Carmen",
    "Heladería Popsy",
    "Cigarrería La 70",
    "Supermercado Éxito Poblado",
    "Tienda Justo y Bueno",
    "Café Cliché",
    "Panadería Pan Pa' Ya",
    "Droguería Colsubsidio",
    "Minimercado La Candelaria",
    "Restaurante Alambique",
    "Frutería Vitaminas",
    "Papelería Kilómetro",
    "Ferretería Constructor",
    "Peluquería Imagen",
    "Lavandería Burbujas",
    "Miscelánea Belén",
    "Restaurante OCI",
    "Heladería Crepes",
    "Cigarrería La 33",
]

MERCHANT_NAMES_BOGOTA = [
    "Tienda Doña Rosa",
    "Farmacia Cruz Verde",
    "Panadería La Floresta",
    "Restaurante Andrés Carne de Res",
    "Café Juan Valdez Usaquén",
    "Minimercado El Vecino",
    "Droguería Cafam",
    "Carnicería Santa Fe",
    "Frutería El Paraíso",
    "Papelería Éxito",
    "Ferretería El Constructor",
    "Tienda Naturista Salud Total",
    "Peluquería Color",
    "Lavandería Lavamatic",
    "Miscelánea Chapinero",
    "Restaurante La Puerta Falsa",
    "Heladería San Jerónimo",
    "Cigarrería La Séptima",
    "Supermercado Jumbo",
    "Tienda D1 Suba",
    "Restaurante Criterion",
    "Café Azahar",
    "Panadería Masa",
    "Droguería La Rebaja",
    "Minimercado Don Luis",
    "Tienda Ara Kennedy",
    "Restaurante Leo Cocina",
    "Frutería Fruver",
    "Papelería Panamericana",
    "Ferretería Easy",
    "Barbería Bogotana",
    "Lavandería Mr. Jeff",
    "Miscelánea Teusaquillo",
    "Restaurante Salvo Patria",
    "Heladería Popsy",
    "Cigarrería La 13",
    "Supermercado Éxito Calle 80",
    "Tienda Justo y Bueno Suba",
    "Café Libertario",
    "Panadería Artesanal",
    "Droguería Colsubsidio",
    "Minimercado La Perseverancia",
    "Restaurante Villanos en Bermudas",
    "Frutería Orgánica",
    "Papelería Kilómetro",
    "Ferretería Homecenter",
    "Peluquería Trends",
    "Lavandería Clean",
    "Miscelánea Fontibón",
    "Restaurante El Cielo",
    "Heladería Crepes",
    "Cigarrería Candelaria",
]

ADDRESSES_MEDELLIN = [
    "Cra 43A #1-50, El Poblado",
    "Calle 10 #32-15, La Candelaria",
    "Cra 70 #44-30, Laureles",
    "Calle 33 #76-20, Belén",
    "Cra 80 #32A-45, La América",
    "Calle 52 #43-100, Centro",
    "Cra 65 #48-10, Suramericana",
    "Calle 44 #70-55, San Juan",
    "Cra 43A #14-50, Manila",
    "Calle 10A #35-20, Provenza",
    "Cra 48 #10-45, Patio Bonito",
    "Calle 7 #43-80, Astorga",
    "Cra 35 #8-20, El Tesoro",
    "Calle 30A #82-15, Belén Rosales",
    "Cra 76 #48-30, Estadio",
    "Calle 53 #45-60, Maracaibo",
    "Cra 46 #52-20, Bomboná",
    "Calle 49 #50-10, Ayacucho",
    "Cra 81 #33-45, Los Colores",
    "Calle 44B #68-20, Conquistadores",
    "Cra 43A #11-30, El Poblado",
    "Calle 37 #81-10, Envigado Centro",
    "Cra 70 #40-15, Circular",
    "Calle 50 #41-20, La Playa",
    "Cra 52 #49-30, Centro Comercial",
    "Calle 33 #65-40, San Javier",
    "Cra 74 #48-55, Floresta",
    "Calle 45 #72-10, Nutibara",
    "Cra 43 #16-20, Lleras",
    "Calle 10 #40-30, Las Palmas",
    "Cra 48 #32-15, Buenos Aires",
    "Calle 58 #45-20, Jesús Nazareno",
    "Cra 65 #33-10, Simón Bolívar",
    "Calle 30 #65-45, Guayabal",
    "Cra 80 #48-20, Robledo",
    "Calle 77 #52-30, Aranjuez",
    "Cra 55 #40-15, Candelaria",
    "Calle 67 #53-20, Manrique",
    "Cra 70 #52-10, Suramericana",
    "Calle 44 #65-30, Carlos E Restrepo",
    "Cra 43B #13-20, Provenza",
    "Calle 9 #43-55, El Poblado",
    "Cra 35 #10-40, Patio Bonito",
    "Calle 10 #34-15, Manila",
    "Cra 48 #15-20, Aguacatala",
    "Calle 30 #43-10, El Poblado Sur",
    "Cra 76 #33-45, Belén La Palma",
    "Calle 52 #70-20, Estadio",
    "Cra 65 #44-30, Laureles",
    "Calle 33 #80-15, Belén",
]

ADDRESSES_BOGOTA = [
    "Cra 7 #71-52, Chapinero",
    "Calle 85 #15-10, Zona Rosa",
    "Cra 15 #93-20, Chicó",
    "Calle 116 #18-30, Usaquén",
    "Cra 11 #82-45, Zona G",
    "Calle 72 #10-15, Centro Internacional",
    "Cra 13 #63-20, Chapinero Central",
    "Calle 53 #13-40, Galerías",
    "Cra 68 #24-10, Zona Industrial",
    "Calle 140 #11-20, Cedritos",
    "Cra 9 #69-30, Quinta Camacho",
    "Calle 26 #13-15, Centro",
    "Cra 19 #84-20, Antiguo Country",
    "Calle 100 #19-45, Chicó Norte",
    "Cra 7 #32-10, La Merced",
    "Calle 45 #13-30, Palermo",
    "Cra 15 #76-20, Zona T",
    "Calle 122 #15-40, Santa Bárbara",
    "Cra 11 #93-55, Chicó",
    "Calle 63 #15-10, Chapinero Alto",
    "Cra 68 #80-20, Minuto de Dios",
    "Calle 170 #9-30, Toberín",
    "Cra 30 #45-15, Teusaquillo",
    "Calle 19 #4-20, La Candelaria",
    "Cra 50 #26-10, Puente Aranda",
    "Calle 80 #68-30, Minuto de Dios",
    "Cra 7 #45-20, Palermo",
    "Calle 147 #19-15, Cedritos",
    "Cra 13 #27-40, La Macarena",
    "Calle 67 #7-10, Quinta Camacho",
    "Cra 15 #106-20, Usaquén",
    "Calle 90 #19-30, Chicó",
    "Cra 11 #73-45, Zona G",
    "Calle 57 #13-20, Galerías",
    "Cra 9 #116-10, Santa Bárbara",
    "Calle 134 #9-40, Cedritos Norte",
    "Cra 7 #82-30, Zona G",
    "Calle 39 #14-15, Teusaquillo",
    "Cra 68 #90-20, Suba",
    "Calle 127 #15-10, Niza",
    "Cra 13 #85-40, Chicó",
    "Calle 72 #15-20, Chapinero",
    "Cra 19 #104-10, Usaquén",
    "Calle 53 #68-30, Normandía",
    "Cra 50 #13-20, Galerías",
    "Calle 26 #68-40, CAN",
    "Cra 7 #28-15, La Candelaria",
    "Calle 100 #11-30, Chicó",
    "Cra 15 #120-20, Santa Bárbara",
    "Calle 80 #11-45, Polo Club",
]

STATUSES = ["active", "inactive", "maintenance"]
STATUS_WEIGHTS = [0.7, 0.15, 0.15]  # 70% activos, 15% inactivos, 15% mantenimiento


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


def generate_last_transaction() -> str:
    """Genera un timestamp de última transacción en los últimos 30 días."""
    now = datetime.utcnow()
    delta = timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (now - delta).isoformat() + "Z"


def generate_datafonos(count: int = 100) -> list:
    """Genera una lista de datáfonos con datos realistas."""
    datafonos = []
    # Dividir entre Medellín (50) y Bogotá (50)
    medellin_count = count // 2
    bogota_count = count - medellin_count

    for i in range(medellin_count):
        device_id = str(uuid.uuid4())
        lat, lon = generate_coordinate("medellin")
        merchant = MERCHANT_NAMES_MEDELLIN[i % len(MERCHANT_NAMES_MEDELLIN)]
        address = ADDRESSES_MEDELLIN[i % len(ADDRESSES_MEDELLIN)]
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        datafonos.append(
            {
                "PK": {"S": "CITY#medellin"},
                "SK": {"S": f"DATAFONO#{device_id}"},
                "device_id": {"S": device_id},
                "merchant_name": {"S": merchant},
                "address": {"S": address},
                "latitude": {"N": str(lat)},
                "longitude": {"N": str(lon)},
                "status": {"S": status},
                "last_transaction": {"S": generate_last_transaction()},
                "city": {"S": "medellin"},
            }
        )

    for i in range(bogota_count):
        device_id = str(uuid.uuid4())
        lat, lon = generate_coordinate("bogota")
        merchant = MERCHANT_NAMES_BOGOTA[i % len(MERCHANT_NAMES_BOGOTA)]
        address = ADDRESSES_BOGOTA[i % len(ADDRESSES_BOGOTA)]
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        datafonos.append(
            {
                "PK": {"S": "CITY#bogota"},
                "SK": {"S": f"DATAFONO#{device_id}"},
                "device_id": {"S": device_id},
                "merchant_name": {"S": merchant},
                "address": {"S": address},
                "latitude": {"N": str(lat)},
                "longitude": {"N": str(lon)},
                "status": {"S": status},
                "last_transaction": {"S": generate_last_transaction()},
                "city": {"S": "bogota"},
            }
        )

    return datafonos


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
            logger.info(f"Progreso: {written}/{total} datáfonos escritos.")

        except ClientError as e:
            logger.error(f"Error escribiendo lote: {e.response['Error']['Message']}")
            raise

    logger.info(f"Escritura completada: {written} datáfonos en tabla '{table_name}'.")


def main():
    if len(sys.argv) < 2:
        print("Uso: python setup/populate_datafonos.py TABLE_NAME")
        sys.exit(1)

    table_name = sys.argv[1]
    logger.info(f"Generando 100 datáfonos para tabla '{table_name}'...")

    datafonos = generate_datafonos(100)
    logger.info(
        f"Generados {len(datafonos)} datáfonos: "
        f"{sum(1 for d in datafonos if d['city']['S'] == 'medellin')} en Medellín, "
        f"{sum(1 for d in datafonos if d['city']['S'] == 'bogota')} en Bogotá."
    )

    write_to_dynamodb(table_name, datafonos)
    logger.info("¡Población de datáfonos completada exitosamente!")


if __name__ == "__main__":
    main()
