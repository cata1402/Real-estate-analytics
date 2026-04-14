"""
Argenprop Scraper v2.0 - Real Estate Analytics (ITBA 2026)
=========================================================
Scraper avanzado para la extracción de departamentos en venta
del portal Argenprop (CABA). Implementa extracción por barrio,
manejo robusto de errores, logging profesional y feature
engineering sobre texto libre.

Dependencias:
    pip install requests beautifulsoup4 pandas

Uso:
    python scrapper.py                  # Corre con config por defecto
    python scrapper.py --pages 50       # Custom páginas por barrio
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
import logging
from datetime import datetime
import argparse
import json

# ─── CONFIGURACIÓN DE LOGGING ────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("scrapper.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── CONSTANTES ──────────────────────────────────────────────────────────────

BASE_URL = "https://www.argenprop.com/departamentos/venta/capital-federal"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36"
}
REQUEST_DELAY = 1.5        # segundos entre requests
MAX_RETRIES = 3            # reintentos por request fallido
RETRY_DELAY = 5            # segundos entre reintentos

# Barrios seleccionados para scraping segmentado
# Criterio: diversidad de segmentos (premium, medio, económico, emergente)
BARRIOS = [
    "palermo", "belgrano", "recoleta", "caballito", "villa-urquiza",
    "almagro", "flores", "nunez", "puerto-madero", "san-telmo",
    "la-boca", "san-nicolas", "retiro", "parque-patricios", "floresta",
    "balvanera", "boedo", "saavedra", "villa-del-parque", "constitucion",
    "chacarita"
]


# ─── FUNCIONES AUXILIARES ────────────────────────────────────────────────────

def clean_text(text):
    """Limpia texto eliminando espacios extra y caracteres no deseados."""
    if not text:
        return "N/A"
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_address(address_raw):
    """
    Extrae calle, altura y piso de una dirección cruda.
    Ej: "Av. Santa Fe 1234, 5° A" -> ("Av. Santa Fe", "1234", "5° A")
    """
    calle = altura = piso = "N/A"
    try:
        address_raw = address_raw.replace("Piso ", "").replace("piso ", "")
        match = re.search(r'^(.*?)\s(\d+)(?:,\s?(.*))?$', address_raw)
        if match:
            calle = match.group(1).strip()
            altura = match.group(2).strip()
            piso = match.group(3).strip() if match.group(3) else "0"
        else:
            calle = address_raw
    except Exception as e:
        logger.debug(f"Error parseando dirección '{address_raw}': {e}")
    return calle, altura, piso


def safe_request(url, max_retries=MAX_RETRIES):
    """
    Realiza un GET con reintentos y manejo de errores robusto.
    Retorna el objeto Response o None si falla.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                logger.warning(f"Bloqueado (403) en {url} - intento {attempt}/{max_retries}")
                time.sleep(RETRY_DELAY * attempt)  # backoff exponencial
            else:
                logger.warning(f"Status {response.status_code} en {url}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout en {url} - intento {attempt}/{max_retries}")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError:
            logger.warning(f"Error de conexión en {url} - intento {attempt}/{max_retries}")
            time.sleep(RETRY_DELAY * 2)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return None
    logger.error(f"Fallaron todos los reintentos para {url}")
    return None


def parse_price(price_text):
    """Extrae precio en USD y expensas del texto de precio."""
    precio = "Consultar"
    moneda = "N/A"
    expensas = "N/A"

    if not price_text:
        return precio, moneda, expensas

    # Precio principal
    p_match = re.search(r'(USD|U\$S|\$)\s?([\d.]+)', price_text)
    if p_match:
        moneda = "USD" if p_match.group(1) in ("USD", "U$S") else "ARS"
        precio = p_match.group(0)

    # Expensas
    e_match = re.search(r'\+\s?\$?\s?([\d.]+)', price_text)
    if e_match:
        expensas = e_match.group(0)

    return precio, moneda, expensas


def parse_features_text(features_text):
    """
    Extrae variables numéricas del texto de detalles de la card.
    Ej: "65 m² cubie. 2 dorm. 30 años 1 baño" -> dict con valores parseados
    """
    result = {
        "Sup_Cubierta_m2": None,
        "Sup_Total_m2": None,
        "Dormitorios": None,
        "Banos": None,
        "Antiguedad": None,
        "Ambientes": None,
    }

    if not features_text or features_text == "N/A":
        return result

    texto = features_text.lower()

    # Superficie cubierta
    m = re.search(r'(\d+)\s*m[²2]\s*cubie', texto)
    if m:
        result["Sup_Cubierta_m2"] = float(m.group(1))

    # Superficie total
    m = re.search(r'(\d+)\s*m[²2]\s*tot', texto)
    if m:
        result["Sup_Total_m2"] = float(m.group(1))

    # Dormitorios
    m = re.search(r'(\d+)\s*dorm', texto)
    if m:
        result["Dormitorios"] = float(m.group(1))

    # Baños
    m = re.search(r'(\d+)\s*ba[ñn]', texto)
    if m:
        result["Banos"] = float(m.group(1))

    # Antigüedad
    m = re.search(r'(\d+)\s*a[ñn]', texto)
    if m:
        result["Antiguedad"] = float(m.group(1))

    # Ambientes
    m = re.search(r'(\d+)\s*amb', texto)
    if m:
        result["Ambientes"] = float(m.group(1))

    return result


# ─── EXTRACCIÓN DETALLADA ────────────────────────────────────────────────────

def get_detail_page(url):
    """
    Extrae información detallada de la página individual del aviso.
    Retorna: descripción, características adicionales, barrio detectado.
    """
    descripcion = "Sin descripción"
    caracteristicas = "N/A"
    barrio = "N/A"
    tipo_propiedad = "Departamento"

    response = safe_request(url)
    if not response:
        return descripcion, caracteristicas, barrio, tipo_propiedad

    soup = BeautifulSoup(response.content, 'html.parser')

    # Descripción completa
    desc_section = soup.find('section', class_='section-description')
    if desc_section:
        descripcion = clean_text(desc_section.text)
        descripcion = descripcion.replace("Leer más Leer menos", "").strip()

    # Características técnicas (lista de features de la ficha)
    features_section = soup.find('ul', class_='property-features')
    if features_section:
        items = features_section.find_all('li')
        caracteristicas = " | ".join([clean_text(li.text) for li in items])

    # Barrio (desde breadcrumb o metadata)
    breadcrumb = soup.find('nav', class_='breadcrumb')
    if breadcrumb:
        links = breadcrumb.find_all('a')
        for link in links:
            text = clean_text(link.text).lower()
            if text not in ('home', 'departamentos', 'venta', 'capital federal', ''):
                barrio = clean_text(link.text)

    return descripcion, caracteristicas, barrio, tipo_propiedad


# ─── SMART FEATURES (NLP BÁSICO) ────────────────────────────────────────────

def extract_smart_features(row):
    """
    Genera variables dicotómicas (0/1) a partir del análisis de texto
    de la descripción y los detalles del aviso mediante búsqueda de keywords.
    """
    texto = (str(row.get('Descripción', '')) + " " + str(row.get('Detalles', ''))).lower()

    return pd.Series({
        # Amenities del edificio
        "Amenities": 1 if any(x in texto for x in [
            "amenities", "piscina", "pileta", "sum", "parrilla",
            "gym", "gimnasio", "sauna", "laundry", "solarium",
            "microcine", "sala de juegos", "rooftop"
        ]) else 0,

        # Sistema de calefacción central
        "Losa_Central": 1 if any(x in texto for x in [
            "losa radiante", "calefacción central", "caldera central",
            "piso radiante", "calefacción por radiadores"
        ]) else 0,

        # Aire acondicionado
        "Aire_Acond": 1 if any(x in texto for x in [
            "aire acondicionado", "split", " a/c", "frío-calor",
            "frío calor", "frio-calor", "frio calor"
        ]) else 0,

        # Financiable con crédito hipotecario
        "Apto_Credito": 1 if any(x in texto for x in [
            "apto crédito", "apto credito", "apto cred",
            "acepta crédito", "acepta credito"
        ]) else 0,

        # Cochera incluida
        "Cochera": 1 if any(x in texto for x in [
            "cochera", "espacio guarda coche", "estacionamiento",
            "guarda coche", "garage", "garaje"
        ]) else 0,

        # Seguridad del edificio
        "Seguridad": 1 if any(x in texto for x in [
            "vigilancia", "seguridad 24", "tótem", "totem",
            "seguridad permanente", "vigilador", "cámara"
        ]) else 0,

        # Luminosidad
        "Luminoso": 1 if any(x in texto for x in [
            "luminoso", "todo luz", "vista abierta",
            "vista panorámica", "muy luminoso", "gran luminosidad",
            "mucha luz"
        ]) else 0,

        # Balcón aterrazado
        "Balcon_Aterrazado": 1 if any(x in texto for x in [
            "aterrazado", "balcón terraza", "balcon terraza",
            "terraza propia"
        ]) else 0,

        # A estrenar / nuevo
        "A_Estrenar": 1 if any(x in texto for x in [
            "a estrenar", "estrenar", "0 años", "nuevo",
            "a estrena"
        ]) else 0,

        # Apto profesional
        "Apto_Profesional": 1 if any(x in texto for x in [
            "apto profesional", "uso profesional", "consultorio"
        ]) else 0,

        # Baulera
        "Baulera": 1 if any(x in texto for x in [
            "baulera", "bóveda", "espacio de guardado"
        ]) else 0,

        # Reciclado / refaccionado
        "Reciclado": 1 if any(x in texto for x in [
            "reciclado", "reciclaje", "refaccionado", "remodelado",
            "a nuevo", "todo a nuevo", "reciclado a nuevo"
        ]) else 0,

        # A refaccionar (para Gap de Flipping)
        "A_Refaccionar": 1 if any(x in texto for x in [
            "a refaccionar", "refaccionar", "para reciclar",
            "para refaccionar", "necesita refacción", "a reciclar"
        ]) else 0,

        # Pileta propia (distinto de amenities del edificio)
        "Pileta": 1 if any(x in texto for x in [
            "pileta", "piscina"
        ]) else 0,

        # SUM
        "SUM": 1 if any(x in texto for x in [
            " sum ", "salón de usos múltiples", "salon de usos",
            "salón de fiestas"
        ]) else 0,
    })


# ─── SCRAPER PRINCIPAL ───────────────────────────────────────────────────────

def scrape_barrio(barrio_slug, max_pages=50):
    """
    Scrapea todas las páginas de un barrio específico.
    Retorna lista de diccionarios con los datos extraídos.
    """
    base = f"https://www.argenprop.com/departamentos/venta/capital-federal/{barrio_slug}"
    barrio_data = []
    seen_links = set()

    logger.info(f"{'='*60}")
    logger.info(f"BARRIO: {barrio_slug.upper()} (máx {max_pages} páginas)")
    logger.info(f"{'='*60}")

    for page in range(1, max_pages + 1):
        url = f"{base}?pagina-{page}" if page > 1 else base
        logger.info(f"  Página {page}/{max_pages} - {url}")

        response = safe_request(url)
        if not response:
            logger.warning(f"  No se pudo acceder a página {page}. Saltando.")
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('div', class_='listing__item')

        if not items:
            logger.info(f"  Sin resultados en página {page}. Fin del barrio.")
            break

        new_count = 0
        for item in items:
            try:
                # Link del aviso
                link_tag = item.find('a', class_='card')
                if not link_tag:
                    continue
                link = "https://www.argenprop.com" + link_tag['href']

                # Deduplicación
                if link in seen_links:
                    continue
                seen_links.add(link)
                new_count += 1

                # Precio y expensas
                price_block = item.find('p', class_='card__price')
                price_text = clean_text(price_block.text) if price_block else ""
                precio, moneda, expensas = parse_price(price_text)

                # Dirección
                addr_tag = item.find('p', class_='card__address')
                raw_address = clean_text(addr_tag.text) if addr_tag else "N/A"
                calle, altura, piso = parse_address(raw_address)

                # Features de la card
                feat_tag = item.find('ul', class_='card__main-features')
                features_text = clean_text(feat_tag.text) if feat_tag else "N/A"
                parsed_features = parse_features_text(features_text)

                # Detalle del aviso (request individual)
                descripcion, caracteristicas, barrio_det, tipo = get_detail_page(link, )

                # Construir registro
                record = {
                    "Precio": precio,
                    "Moneda": moneda,
                    "Expensas": expensas,
                    "Calle": calle,
                    "Altura": altura,
                    "Piso": piso,
                    "Detalles": features_text,
                    "Descripción": descripcion,
                    "Caracteristicas": caracteristicas,
                    "Barrio": barrio_det if barrio_det != "N/A" else barrio_slug.replace("-", " ").title(),
                    "Tipo_Propiedad": tipo,
                    "Link": link,
                    **parsed_features,  # Sup_Cubierta, Dormitorios, etc.
                }

                barrio_data.append(record)
                time.sleep(REQUEST_DELAY)

            except Exception as e:
                logger.debug(f"  Error procesando aviso: {e}")
                continue

        logger.info(f"  -> {new_count} avisos nuevos extraídos")

        if new_count == 0:
            logger.info(f"  Sin avisos nuevos. Fin del barrio.")
            break

    logger.info(f"  TOTAL {barrio_slug}: {len(barrio_data)} avisos")
    return barrio_data


def run_scrapper(barrios=None, max_pages=50, output_dir="output"):
    """
    Ejecuta el scraping completo para todos los barrios configurados.
    Genera Smart Features y guarda el resultado en TSV y CSV.
    """
    if barrios is None:
        barrios = BARRIOS

    # Crear directorio de salida
    os.makedirs(output_dir, exist_ok=True)

    all_data = []
    stats = {}
    start_time = datetime.now()

    logger.info(f"Inicio del scraping: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Barrios a procesar: {len(barrios)}")
    logger.info(f"Páginas máximas por barrio: {max_pages}")

    for i, barrio in enumerate(barrios, 1):
        logger.info(f"\n[{i}/{len(barrios)}] Procesando {barrio}...")
        barrio_data = scrape_barrio(barrio, max_pages)
        stats[barrio] = len(barrio_data)
        all_data.extend(barrio_data)

        # Guardado parcial por seguridad (cada 5 barrios)
        if i % 5 == 0 and all_data:
            partial_df = pd.DataFrame(all_data)
            partial_path = os.path.join(output_dir, f"parcial_{i}_barrios.csv")
            partial_df.to_csv(partial_path, index=False, encoding='utf-8-sig')
            logger.info(f"  Guardado parcial: {partial_path} ({len(partial_df)} registros)")

    if not all_data:
        logger.error("No se obtuvieron datos. Finalizando.")
        return None

    # Construir DataFrame final
    df = pd.DataFrame(all_data)
    logger.info(f"\nDataFrame crudo: {df.shape[0]} filas x {df.shape[1]} columnas")

    # Aplicar Smart Features
    logger.info("Generando Smart Features (NLP sobre descripciones)...")
    features_df = df.apply(extract_smart_features, axis=1)
    df = pd.concat([df, features_df], axis=1)

    # Deduplicación final por Link
    antes = len(df)
    df = df.drop_duplicates(subset='Link', keep='first')
    logger.info(f"Deduplicación: {antes} -> {len(df)} registros ({antes - len(df)} duplicados eliminados)")

    # Guardar resultados
    timestamp = int(time.time())

    # CSV (para Python/Pandas)
    csv_path = os.path.join(output_dir, f"dataset_argenprop_{timestamp}.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # TSV (para Excel)
    tsv_path = os.path.join(output_dir, f"argenprop_export_{timestamp}.tsv")
    df.to_csv(tsv_path, sep='\t', index=False, encoding='utf-8-sig')

    # Estadísticas del scraping
    end_time = datetime.now()
    duration = end_time - start_time

    stats_report = {
        "fecha_extraccion": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "duracion_minutos": round(duration.total_seconds() / 60, 1),
        "total_registros": len(df),
        "total_barrios": len(barrios),
        "registros_por_barrio": stats,
        "columnas": list(df.columns),
        "archivos_generados": [csv_path, tsv_path],
    }

    stats_path = os.path.join(output_dir, f"scraping_stats_{timestamp}.json")
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_report, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*60}")
    logger.info(f"SCRAPING FINALIZADO")
    logger.info(f"{'='*60}")
    logger.info(f"Duración total: {duration}")
    logger.info(f"Total registros: {len(df)}")
    logger.info(f"Archivos: {csv_path} | {tsv_path}")
    logger.info(f"Estadísticas: {stats_path}")

    return df


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Argenprop Scraper v2.0")
    parser.add_argument("--pages", type=int, default=50,
                        help="Páginas máximas por barrio (default: 50)")
    parser.add_argument("--barrios", nargs="+", default=None,
                        help="Lista de barrios a scrapear (default: todos)")
    parser.add_argument("--output", type=str, default="output",
                        help="Directorio de salida (default: output)")
    args = parser.parse_args()

    df = run_scrapper(
        barrios=args.barrios,
        max_pages=args.pages,
        output_dir=args.output
    )

    if df is not None:
        print(f"\nResumen del DataFrame:")
        print(f"  Shape: {df.shape}")
        print(f"  Columnas: {list(df.columns)}")
        print(f"\nPrimeros registros:")
        print(df.head(3).to_string())
