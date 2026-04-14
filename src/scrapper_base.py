import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os

def clean_text(text):
    if not text: return "N/A"
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_address(address_raw):
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
    except: pass
    return calle, altura, piso

def get_description(url, headers):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            s = BeautifulSoup(res.content, 'html.parser')
            desc = s.find('section', class_='section-description')
            if desc:
                return clean_text(desc.text).replace("Leer más Leer menos", "").strip()
    except: pass
    return "Sin descripción"

def extract_smart_features(row):
    texto = (str(row['Descripción']) + " " + str(row['Detalles'])).lower()
    return pd.Series({
        "Amenities": 1 if any(x in texto for x in ["amenities", "piscina", "pileta", "sum", "parrilla", "gym", "sauna", "laundry"]) else 0,
        "Losa_Central": 1 if any(x in texto for x in ["losa radiante", "calefacción central", "caldera central", "piso radiante"]) else 0,
        "Aire_Acond": 1 if any(x in texto for x in ["aire acondicionado", "split", " a/c", "frío-calor"]) else 0,
        "Apto_Credito": 1 if "apto crédito" in texto or "apto credito" in texto else 0,
        "Cochera": 1 if any(x in texto for x in ["cochera", "espacio guarda coche", "estacionamiento", "guarda coche"]) else 0,
        "Seguridad": 1 if any(x in texto for x in ["vigilancia", "seguridad 24", "tótem", "totem", "encargado"]) else 0,
        "Luminoso": 1 if any(x in texto for x in ["luminoso", "todo luz", "vista abierta", "vista panorámica", "sol"]) else 0,
        "Balcon_Aterrazado": 1 if "aterrazado" in texto or "balcón terraza" in texto else 0
    })

def run_scrapper(max_pages=3):
    base_url = "https://www.argenprop.com/departamentos/venta/capital-federal"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    
    all_data = []
    seen_links = set()
    output_dir = "output"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    for i in range(1, max_pages + 1):
        # URL corregida con el formato ?pagina-X
        url = f"{base_url}?pagina-{i}" if i > 1 else base_url
        print(f"\n--- PROCESANDO PÁGINA {i} ---")
        print(f"URL: {url}")
        
        try:
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.content, 'html.parser')
            items = soup.find_all('div', class_='listing__item')

            if not items: break

            for item in items:
                try:
                    link_tag = item.find('a', class_='card')
                    if not link_tag: continue
                    link = "https://www.argenprop.com" + link_tag['href']
                    
                    if link in seen_links: continue
                    seen_links.add(link)

                    price_block = item.find('p', class_='card__price')
                    price_text = clean_text(price_block.text) if price_block else ""
                    p_match = re.search(r'(USD|S)\s?([\d.]+)', price_text)
                    precio = p_match.group(0) if p_match else "Consultar"
                    e_match = re.search(r'\+\s?\$?\s?([\d.]+)', price_text)
                    expensas = e_match.group(0) if e_match else "N/A"

                    raw_address = clean_text(item.find('p', class_='card__address').text)
                    calle, altura, piso = parse_address(raw_address)
                    features = clean_text(item.find('ul', class_='card__main-features').text)
                    
                    print(f"-> Extrayendo: {calle} {altura}...")
                    desc = get_description(link, headers)
                    
                    all_data.append({
                        "Precio": precio, "Expensas": expensas, "Calle": calle,
                        "Altura": altura, "Piso": piso, "Detalles": features,
                        "Descripción": desc, "Link": link
                    })
                    time.sleep(1.2)
                except: continue
        except: break

    if all_data:
        df = pd.DataFrame(all_data)
        features_df = df.apply(extract_smart_features, axis=1)
        df = pd.concat([df, features_df], axis=1)
        
        filename = f"argenprop_export_{int(time.time())}.tsv"
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, sep='\t', index=False, encoding='utf-8-sig')
        print(f"\n¡Éxito! Archivo en: {filepath}")
    else:
        print("No se obtuvieron datos.")

if __name__ == "__main__":
    run_scrapper(max_pages=3)