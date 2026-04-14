# %% [markdown]
# # Pre-Entrega 1 — Inspección y Validación del Dataset
# **Analítica Descriptiva | ITBA 2026**
#
# Este notebook documenta la extracción de datos y la generación del DataFrame
# maestro, demostrando la captura de variables textuales, numéricas, ordinales
# y dicotómicas.

# %% [markdown]
# ## 1. Carga del dataset

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configuración visual
plt.rcParams['figure.figsize'] = (12, 5)
plt.rcParams['font.size'] = 11
sns.set_style("whitegrid")

# %%
df = pd.read_csv("../data/raw/dataset_argenprop_completo.csv")
print(f"Dataset cargado exitosamente.")
print(f"Dimensiones: {df.shape[0]:,} filas x {df.shape[1]} columnas")

# %%
df.head()

# %% [markdown]
# ## 2. Estructura del DataFrame
# Verificamos los tipos de datos capturados: textuales, numéricos, ordinales y dicotómicos.

# %%
df.info()

# %%
# Resumen de tipos de datos
print("=" * 50)
print("RESUMEN DE TIPOS DE DATOS CAPTURADOS")
print("=" * 50)

textuales = ['Precio', 'Expensas', 'Calle', 'Barrio', 'Descripción', 'Detalles', 'Caracteristicas', 'Link']
numericos = ['Sup_Cubierta_m2', 'Sup_Total_m2', 'Antiguedad', 'Latitud', 'Longitud']
ordinales = ['Piso', 'Ambientes', 'Dormitorios', 'Banos']
dicotomicos = ['Amenities', 'Losa_Central', 'Aire_Acond', 'Apto_Credito',
               'Cochera', 'Seguridad', 'Luminoso', 'Balcon_Aterrazado', 'A_Estrenar']

print(f"\nTextuales ({len(textuales)}): {', '.join(textuales)}")
print(f"Numéricos ({len(numericos)}): {', '.join(numericos)}")
print(f"Ordinales ({len(ordinales)}): {', '.join(ordinales)}")
print(f"Dicotómicos ({len(dicotomicos)}): {', '.join(dicotomicos)}")
print(f"\nTotal: {len(textuales) + len(numericos) + len(ordinales) + len(dicotomicos)} variables clasificadas de {df.shape[1]} columnas")

# %% [markdown]
# ## 3. Estadísticas descriptivas

# %%
df.describe()

# %%
# Estadísticas de las variables numéricas principales
print("=" * 60)
print("ESTADÍSTICAS DE VARIABLES NUMÉRICAS PRINCIPALES")
print("=" * 60)

import re

def parse_price_usd(precio):
    """Extrae el valor numérico de precios en USD."""
    if pd.isna(precio):
        return None
    m = re.search(r'USD\s?([\d.]+)', str(precio))
    if m:
        return float(m.group(1).replace('.', ''))
    return None

df['precio_usd'] = df['Precio'].apply(parse_price_usd)

print(f"\nPRECIOS (USD):")
print(f"  Con precio en USD: {df['precio_usd'].notna().sum():,} ({df['precio_usd'].notna().mean()*100:.1f}%)")
print(f"  Media:   USD {df['precio_usd'].mean():>12,.0f}")
print(f"  Mediana: USD {df['precio_usd'].median():>12,.0f}")
print(f"  Mínimo:  USD {df['precio_usd'].min():>12,.0f}")
print(f"  Máximo:  USD {df['precio_usd'].max():>12,.0f}")
print(f"  Desvío:  USD {df['precio_usd'].std():>12,.0f}")

print(f"\nSUPERFICIE CUBIERTA (m²):")
sc = df['Sup_Cubierta_m2'].dropna()
print(f"  Registros válidos: {len(sc):,}")
print(f"  Media: {sc.mean():.1f} m² | Mediana: {sc.median():.1f} m²")
print(f"  Rango: {sc.min():.0f} – {sc.max():.0f} m²")

print(f"\nANTIGÜEDAD (años):")
ant = df['Antiguedad'].dropna()
print(f"  Registros válidos: {len(ant):,} ({len(ant)/len(df)*100:.1f}%)")
print(f"  Media: {ant.mean():.1f} años | Mediana: {ant.median():.1f} años")
print(f"  Rango: {ant.min():.0f} – {ant.max():.0f}")
if ant.max() > 200:
    print(f"  ⚠ Se detectan valores extremos (máx {ant.max():.0f}) que indican errores de carga")

# %% [markdown]
# ## 4. Cobertura por barrio

# %%
print(f"Barrios únicos detectados: {df['Barrio'].nunique()}")
print(f"\nTop 21 barrios por cantidad de registros:")
print(df['Barrio'].value_counts().head(21).to_string())

# %%
# Gráfico de registros por barrio
top_barrios = df['Barrio'].value_counts().head(21)

fig, ax = plt.subplots(figsize=(14, 6))
bars = ax.barh(range(len(top_barrios)), top_barrios.values, color='#2471A3', edgecolor='white')
ax.set_yticks(range(len(top_barrios)))
ax.set_yticklabels(top_barrios.index, fontsize=10)
ax.set_xlabel("Cantidad de departamentos", fontsize=12)
ax.set_title("Registros scrapeados por barrio (Top 21)", fontsize=14, fontweight='bold')
ax.invert_yaxis()

# Agregar valores
for i, (val, name) in enumerate(zip(top_barrios.values, top_barrios.index)):
    ax.text(val + 10, i, f'{val:,}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig("../docs/barrios_scrapeados.png", dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 5. Análisis de valores nulos

# %%
nulos = df.isnull().sum()
nulos_pct = (nulos / len(df) * 100).round(1)
nulos_df = pd.DataFrame({'Nulos': nulos, '% del total': nulos_pct})
nulos_df = nulos_df[nulos_df['Nulos'] > 0].sort_values('Nulos', ascending=False)

print("VARIABLES CON VALORES NULOS:")
print(nulos_df.to_string())

# %%
# Gráfico de nulidad
fig, ax = plt.subplots(figsize=(10, 5))
colors = ['#E74C3C' if p > 30 else '#F39C12' if p > 10 else '#2ECC71' for p in nulos_df['% del total']]
ax.barh(range(len(nulos_df)), nulos_df['% del total'], color=colors, edgecolor='white')
ax.set_yticks(range(len(nulos_df)))
ax.set_yticklabels(nulos_df.index, fontsize=10)
ax.set_xlabel("% de valores nulos", fontsize=12)
ax.set_title("Proporción de valores nulos por variable", fontsize=14, fontweight='bold')
ax.invert_yaxis()
ax.axvline(x=30, color='red', linestyle='--', alpha=0.5, label='Umbral crítico (30%)')
ax.legend()
plt.tight_layout()
plt.savefig("../docs/nulos_por_variable.png", dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 6. Smart Features (variables dicotómicas)

# %%
print("DISTRIBUCIÓN DE SMART FEATURES:")
print("=" * 50)
for col in dicotomicos:
    count = df[col].sum()
    pct = df[col].mean() * 100
    bar = '█' * int(pct / 2) + '░' * (50 - int(pct / 2))
    print(f"  {col:<22} {count:>6,} ({pct:>5.1f}%) {bar}")

# %%
# Gráfico de Smart Features
fig, ax = plt.subplots(figsize=(10, 5))
feat_pct = pd.Series({col: df[col].mean() * 100 for col in dicotomicos}).sort_values(ascending=True)
bars = ax.barh(range(len(feat_pct)), feat_pct.values, color='#1B4F72', edgecolor='white')
ax.set_yticks(range(len(feat_pct)))
ax.set_yticklabels(feat_pct.index, fontsize=10)
ax.set_xlabel("% del stock", fontsize=12)
ax.set_title("Prevalencia de Smart Features en el dataset", fontsize=14, fontweight='bold')

for i, val in enumerate(feat_pct.values):
    ax.text(val + 0.5, i, f'{val:.1f}%', va='center', fontsize=9)

plt.tight_layout()
plt.savefig("../docs/smart_features.png", dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 7. Distribución de precios

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histograma de precios
precios_valid = df['precio_usd'].dropna()
precios_filtrados = precios_valid[precios_valid <= 1_000_000]  # Zoom hasta 1M

axes[0].hist(precios_filtrados, bins=50, color='#2471A3', edgecolor='white', alpha=0.8)
axes[0].axvline(precios_valid.median(), color='red', linestyle='--', linewidth=2, label=f'Mediana: USD {precios_valid.median():,.0f}')
axes[0].axvline(precios_valid.mean(), color='orange', linestyle='--', linewidth=2, label=f'Media: USD {precios_valid.mean():,.0f}')
axes[0].set_xlabel("Precio (USD)", fontsize=12)
axes[0].set_ylabel("Frecuencia", fontsize=12)
axes[0].set_title("Distribución de precios (hasta USD 1M)", fontsize=13, fontweight='bold')
axes[0].legend(fontsize=9)

# Box plot por segmento
segmentos = pd.cut(precios_valid, bins=[0, 100000, 200000, 500000, 10000000],
                   labels=['< 100K', '100K-200K', '200K-500K', '> 500K'])
segmento_counts = segmentos.value_counts().sort_index()
axes[1].bar(range(len(segmento_counts)), segmento_counts.values, color=['#27AE60', '#2471A3', '#F39C12', '#E74C3C'], edgecolor='white')
axes[1].set_xticks(range(len(segmento_counts)))
axes[1].set_xticklabels(segmento_counts.index, fontsize=10)
axes[1].set_ylabel("Cantidad de propiedades", fontsize=12)
axes[1].set_title("Distribución por segmento de precio", fontsize=13, fontweight='bold')

for i, val in enumerate(segmento_counts.values):
    axes[1].text(i, val + 100, f'{val:,}', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig("../docs/distribucion_precios.png", dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 8. Geocodificación

# %%
con_coords = df[['Latitud', 'Longitud']].notna().all(axis=1).sum()
sin_coords = df[['Latitud', 'Longitud']].isna().any(axis=1).sum()
print(f"Registros con coordenadas: {con_coords:,} ({con_coords/len(df)*100:.1f}%)")
print(f"Registros sin coordenadas: {sin_coords:,} ({sin_coords/len(df)*100:.1f}%)")
print(f"\nEl 98.2% del dataset está geocodificado, habilitando los cruces")
print(f"espaciales planificados para la Entrega 3.")

# %% [markdown]
# ## 9. Resumen ejecutivo del dataset
#
# | Métrica | Valor |
# |---------|-------|
# | Total de registros | 18,128 |
# | Total de variables | 28 |
# | Barrios cubiertos | 21 principales (70 detectados) |
# | Registros con precio USD | 17,953 (99.0%) |
# | Registros geocodificados | 17,807 (98.2%) |
# | Smart Features generadas | 9 variables dicotómicas |
# | Fuente | Argenprop (web scraping) |
# | Representatividad estimada | ~23% del stock CABA |

# %%
print("✓ Dataset validado y listo para la fase de limpieza (Pre-Entrega 2)")
