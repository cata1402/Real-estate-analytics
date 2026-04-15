# Real-estate-analytics
Proyecto de Analítica Descriptiva 

---

## Descripción

Proyecto integrador de Analítica Descriptiva. Analizamos el mercado de departamentos en venta en CABA usando datos reales extraídos de Argenprop mediante web scraping, cruzados con datos de Airbnb y fuentes públicas de Buenos Aires.

El objetivo es construir una base analítica para una startup PropTech que busca detectar oportunidades de inversión: flipping inmobiliario, generación de renta y zonas emergentes.

## Estructura

```
Real-estate-analytics/
├── data/
│   └── raw/
│       ├── dataset_argenprop_completo.csv   # 18.128 deptos en venta
│       └── airbnb_listings.csv              # 27.348 listings Airbnb CABA
├── notebooks/
│   └── 01_extraccion_y_validacion.ipynb     # Evidencia scraping + análisis
├── src/
│   ├── scrapper_base.py                     # Script original de cátedra
│   └── scrapper_v2.py                       # Versión optimizada del equipo
├── docs/
│   └── TP1_PreEntrega.pdf
├── output/                                  # Generado por el scrapper
├── .gitignore
└── README.md
```

## Datasets

### Argenprop (fuente principal)

| | |
|---|---|
| **Fuente** | [Argenprop](https://www.argenprop.com) |
| **Registros** | 18.128 departamentos únicos |
| **Variables** | 28 columnas |
| **Cobertura** | 21 barrios de CABA |
| **Representatividad** | ~23% del stock publicado |
| **Link** | https://www.argenprop.com/departamentos/venta/capital-federal |

### Inside Airbnb (fuente complementaria)

| | |
|---|---|
| **Fuente** | [Inside Airbnb](https://insideairbnb.com/buenos-aires) |
| **Registros** | 27.348 listings |
| **Cobertura** | 48 barrios de CABA |
| **Uso** | Índice de Presión Airbnb, Rentabilidad Bruta |
| **Link** | https://insideairbnb.com/buenos-aires |

## Mejoras del scrapper

El script base de cátedra entra a cada aviso individual para sacar la descripción completa (~20 requests extra por página → horas de ejecución). Nuestra versión extrae todo desde la card del listado: **1 request por página**, 15 Smart Features (vs 8), logging, reintentos, CLI configurable.

```bash
# Test rápido (~5 seg)
python src/scrapper_v2.py --pages 2 --barrios palermo

# Completo (~30 min)
python src/scrapper_v2.py
```

## KPIs

| KPI | Fórmula |
|-----|---------|
| Precio mediano m²/barrio | `mediana(precio_usd / sup_m2)` por barrio |
| Gap de Flipping | `(med_m2_estrenar − med_m2_refac) / med_m2_refac × 100` |
| Rentabilidad Bruta | `(Alquiler_mensual × 12) / Precio_compra × 100` |
| Score de Subvaluación | `(precio_pub − precio_AVM) / precio_AVM × 100` |
| Coef. Variación | `(std_m2 / media_m2) × 100` por barrio |
| Índice Presión Airbnb | `listings_airbnb / deptos_venta` por barrio |

## Fuentes externas planificadas (Fase 3)

- [BA Data — Estaciones de Subte](https://data.buenosaires.gob.ar)
- [BA Data — Espacios Verdes](https://data.buenosaires.gob.ar)
- [BA Data — Comisarías](https://data.buenosaires.gob.ar)
- [BA Data — Barrios GeoJSON](https://data.buenosaires.gob.ar)
- [CAC — Costo de construcción](https://www.camarco.org.ar)


## Equipo

Catalina Bachetti, Simón Volpato Escandarani y Matías Fleischer
