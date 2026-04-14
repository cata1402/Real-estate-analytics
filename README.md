# Real-estate-analytics
Proyecto de Analítica Descriptiva 

---

## Descripción del Proyecto

Sistema de inteligencia inmobiliaria para una startup PropTech, construido a partir de datos reales del mercado de departamentos en venta de CABA. El proyecto cubre el ciclo completo de Knowledge Discovery in Databases (KDD): desde la extracción bruta de datos hasta la generación de insights accionables para la toma de decisiones de inversión.

**Cliente:** Startup PropTech enfocada en flipping inmobiliario, generación de renta y detección de zonas emergentes.

**Dataset principal:** 18.128 departamentos en venta extraídos de Argenprop mediante web scraping.

## Estructura del Repositorio

```
real-estate-analytics/
├── README.md                          # Este archivo
├── data/
│   └── raw/                           # Datos crudos (sin procesar)
│       ├── dataset_argenprop_completo.csv
│       └── argenprop_export_*.tsv
├── notebooks/
│   └── 01_extraccion_y_validacion.py  # Evidencia del scraping y validación
├── src/
│   ├── scrapper.py                    # Scraper base (provisto por cátedra)
│   └── scrapper_v2.py                 # Scraper mejorado por el equipo
├── docs/
│   ├── TP1_PreEntrega.pdf             # Informe Pre-Entrega 1
│   └── *.png                          # Gráficos generados
└── .gitignore
```

## Dataset

| Atributo | Detalle |
|----------|---------|
| **Fuente** | [Argenprop](https://www.argenprop.com) |
| **Método** | Web Scraping (Python: requests + BeautifulSoup + Pandas) |
| **Registros** | 18.128 departamentos únicos |
| **Variables** | 28 columnas (textuales, numéricas, ordinales, dicotómicas) |
| **Cobertura** | 21 barrios de CABA |
| **Representatividad** | ~23% del stock publicado en CABA |
| **Geocodificación** | 98,2% de registros con lat/long |

### Variables capturadas

- **Identificación:** Precio, Expensas, Calle, Altura, Piso, Barrio, Lat, Long, Link
- **Numéricas:** Dormitorios, Baños, Ambientes, Antigüedad, Sup_Cubierta_m2, Sup_Total_m2
- **Textuales:** Descripción (texto libre), Detalles, Características
- **Smart Features (0/1):** Amenities, Losa_Central, Aire_Acond, Apto_Credito, Cochera, Seguridad, Luminoso, Balcon_Aterrazado, A_Estrenar


## KPIs Definidos

| KPI | Fórmula |
|-----|---------|
| Precio mediano m² por barrio | `mediana(precio_usd / sup_m2)` por barrio |
| Gap de Flipping | `(med_m2_estrenar − med_m2_refac) / med_m2_refac × 100` |
| Rentabilidad Bruta (Yield) | `(Alquiler_mensual × 12) / Precio_compra × 100` |
| Score de Subvaluación | `(precio_pub − precio_AVM) / precio_AVM × 100` |
| Coef. Variación de Precios | `(std_m2 / media_m2) × 100` por barrio |

## Cronograma

| Entrega | Fecha | Contenido |
|---------|-------|-----------|
| **Pre-Entrega 1** | 15/04 | Definición, scraping, hipótesis |
| Pre-Entrega 2 | 13/05 | Limpieza, EDA, validación estadística |
| Pre-Entrega 3 | 10/06 | Clustering, PCA, cruces espaciales |
| TP Final | 18/06 | Dashboard, presentación ejecutiva |

## Fuentes Externas (Fase 3)

- [Inside Airbnb — Buenos Aires](https://insideairbnb.com/buenos-aires)
- [BA Data — Datos Abiertos GCBA](https://data.buenosaires.gob.ar)
- [Cámara Argentina de la Construcción](https://www.camarco.org.ar)

## Equipo
Catalina Bachetti, Simon Volpato Escandarani y Matias Fleischer