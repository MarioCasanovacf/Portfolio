from pathlib import Path

import pandas as pd
import numpy as np

# Determinismo para reproducibilidad
np.random.seed(42)

# Ruta relativa al ARCHIVO, no al cwd desde donde se invoque el script:
# antes el default era "../data", que escribia fuera del proyecto si el
# script se corria desde cualquier lugar que no fuera src/.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "data" / "synthetic"


def generate_king_county_housing(output_dir=_DEFAULT_OUTPUT_DIR, n_houses=5000, seed=42):
    """
    Genera un dataset sintetico de ventas inmobiliarias estilo King County (WA).

    ADVERTENCIA DE ROL (revival T-116): este dataset es un BENCHMARK DECLARADO,
    no una fuente de verdad sobre el mercado real. El generador PLANTA una
    superficie de precio (aditiva + una interaccion + una superficie espacial
    no-aditiva via hotspots gaussianos) que un pipeline de ML luego "descubre" --
    eso es una prueba de que el instrumento recupera una senal CONOCIDA, no un
    hallazgo sobre King County. Los parametros completos del DGP estan
    declarados en `data/README.md` junto a cualquier comparacion que use este
    archivo. Ver `data/real/kc_house_data.csv` para el dataset real.

    `seed` se re-aplica AL INICIO de cada llamada (no solo al importar el
    modulo) para que dos invocaciones consecutivas en el mismo proceso -- p.ej.
    en un test -- sean tan deterministas como dos procesos separados.
    """
    np.random.seed(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "kc_house_data_synthetic.csv"

    # --- Columna auxiliar: Unnamed: 0 (indice secuencial del CSV original) ---
    unnamed_0 = np.arange(n_houses)

    # --- ID: enteros largos unicos (simulando IDs catastrales) ---
    ids = np.random.randint(1_000_000_000, 9_999_999_999, size=n_houses)

    # --- Fecha de venta: entre Mayo 2014 y Mayo 2015, formato 'YYYYMMDDTHHMMSS' ---
    start_ts = pd.Timestamp("2014-05-01")
    end_ts = pd.Timestamp("2015-05-31")
    random_days = np.random.randint(0, (end_ts - start_ts).days, size=n_houses)
    dates = [(start_ts + pd.Timedelta(days=int(d))).strftime("%Y%m%dT000000") for d in random_days]

    # --- Bedrooms: mayoria 3-4, rango 1-6 con cola derecha ---
    bedrooms = np.random.choice(
        [1, 2, 3, 4, 5, 6],
        size=n_houses,
        p=[0.04, 0.15, 0.38, 0.28, 0.10, 0.05]
    ).astype(float)

    # --- Bathrooms: valores tipicos con incrementos de 0.25 ---
    bathrooms = np.random.choice(
        [0.5, 0.75, 1.0, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0, 4.5, 5.0],
        size=n_houses,
        p=[0.01, 0.02, 0.10, 0.08, 0.10, 0.12, 0.15, 0.14, 0.08, 0.08, 0.05, 0.03, 0.02, 0.02]
    ).astype(float)

    # --- sqft_living: lognormal centrada ~1900 sqft, min 370, max ~6000 ---
    sqft_living = np.clip(
        np.random.lognormal(mean=7.5, sigma=0.4, size=n_houses).astype(int),
        370, 8000
    )

    # --- sqft_lot: lognormal con alta varianza (lotes pequenos hasta grandes terrenos) ---
    sqft_lot = np.clip(
        np.random.lognormal(mean=8.5, sigma=1.0, size=n_houses).astype(int),
        500, 500_000
    )

    # --- Floors: 1, 1.5, 2, 2.5, 3 ---
    floors = np.random.choice(
        [1.0, 1.5, 2.0, 2.5, 3.0],
        size=n_houses,
        p=[0.45, 0.10, 0.35, 0.05, 0.05]
    )

    # --- Waterfront: binario, ~1% tienen waterfront ---
    waterfront = np.random.choice([0, 1], size=n_houses, p=[0.99, 0.01]).astype(int)

    # --- View: 0-4, mayoria 0 ---
    view = np.random.choice(
        [0, 1, 2, 3, 4],
        size=n_houses,
        p=[0.75, 0.05, 0.08, 0.06, 0.06]
    ).astype(int)

    # --- Condition: 1-5, centrado en 3 ---
    condition = np.random.choice(
        [1, 2, 3, 4, 5],
        size=n_houses,
        p=[0.02, 0.05, 0.55, 0.28, 0.10]
    ).astype(int)

    # --- Grade: 1-13, centrado en 7-8 (sistema de King County) ---
    grade = np.random.choice(
        [4, 5, 6, 7, 8, 9, 10, 11, 12],
        size=n_houses,
        p=[0.01, 0.03, 0.12, 0.30, 0.28, 0.14, 0.07, 0.03, 0.02]
    ).astype(int)

    # --- sqft_above y sqft_basement: particion de sqft_living ---
    basement_fraction = np.where(
        np.random.rand(n_houses) < 0.40,
        np.random.uniform(0.15, 0.45, n_houses),
        0.0
    )
    sqft_basement = (sqft_living * basement_fraction).astype(int)
    sqft_above = (sqft_living - sqft_basement).astype(int)

    # --- yr_built: distribuido entre 1900 y 2015, sesgo hacia 1960-2000 ---
    yr_built = np.clip(
        np.random.normal(loc=1975, scale=20, size=n_houses).astype(int),
        1900, 2015
    )

    # --- yr_renovated: mayoria 0, ~10% renovadas entre 1980-2015 ---
    yr_renovated = np.where(
        np.random.rand(n_houses) < 0.10,
        np.random.randint(1980, 2016, size=n_houses),
        0
    ).astype(int)

    # --- Zipcode: codigos reales de King County (muestra representativa) ---
    kc_zipcodes = [
        98001, 98002, 98003, 98004, 98005, 98006, 98007, 98008, 98010, 98011,
        98014, 98019, 98022, 98023, 98024, 98027, 98028, 98029, 98030, 98031,
        98032, 98033, 98034, 98038, 98039, 98040, 98042, 98045, 98052, 98053,
        98055, 98056, 98058, 98059, 98065, 98070, 98072, 98074, 98075, 98077,
        98092, 98102, 98103, 98105, 98106, 98107, 98108, 98109, 98112, 98115,
        98116, 98117, 98118, 98119, 98122, 98125, 98126, 98133, 98136, 98144,
        98146, 98148, 98155, 98166, 98168, 98177, 98178, 98188, 98198, 98199
    ]
    zipcode = np.random.choice(kc_zipcodes, size=n_houses).astype(int)

    # --- Lat/Long: coordenadas acotadas al condado de King ---
    lat = np.random.uniform(47.15, 47.78, size=n_houses).round(4)
    long = np.random.uniform(-122.52, -121.31, size=n_houses).round(4)

    # --- sqft_living15 y sqft_lot15: variantes cercanas a living/lot ---
    sqft_living15 = np.clip(
        sqft_living + np.random.normal(0, 200, size=n_houses).astype(int),
        400, 8000
    ).astype(int)
    sqft_lot15 = np.clip(
        sqft_lot + np.random.normal(0, 1500, size=n_houses).astype(int),
        500, 500_000
    ).astype(int)

    # --- Price: a realistic, RECOVERABLE mix of additive, interaction and
    #     non-linear spatial structure. A linear model captures the additive bulk;
    #     tree ensembles genuinely earn their lift on the parts it cannot. ---
    #
    # Non-linear spatial premium: a sum of Gaussian "hotspots" anchored on real
    # King County high-value areas. A sum of bumps is non-monotonic in lat/long,
    # so additive lat+long (a linear model) cannot represent it, and a degree-2
    # interaction only crudely; partition-based ensembles recover it. This is the
    # genuine geographic latent structure the model comparison is meant to expose.
    hotspots = [
        (47.62, -122.21, 220_000),  # Bellevue / Medina / Mercer Is. (east-side luxury)
        (47.63, -122.35, 150_000),  # Seattle core (Queen Anne / downtown waterfront)
        (47.57, -122.04, 90_000),   # Sammamish plateau (east suburbs)
    ]
    spatial_premium = np.zeros(n_houses)
    for lat_c, lon_c, amp in hotspots:
        d2 = (lat - lat_c) ** 2 + (long - lon_c) ** 2
        spatial_premium += amp * np.exp(-d2 / 0.012)

    base_price = (
        sqft_living * 150
        + (grade - 7) * 50_000
        + sqft_living * (grade - 7) * 12       # interaction: luxury premium scales with size
        + (condition - 3) * 20_000
        + waterfront * 300_000
        + view * 25_000
        + spatial_premium                       # non-linear geographic surface
    ).astype(float)
    # Ruido lognormal para right-skew
    noise_mult = np.random.lognormal(mean=0, sigma=0.25, size=n_houses)
    price = np.clip(base_price * noise_mult, 75_000, 5_000_000).round(2)

    # --- Inyeccion de NaN en bedrooms y bathrooms (similar al dataset original) ---
    nan_bedrooms_idx = np.random.choice(n_houses, size=int(n_houses * 0.025), replace=False)
    nan_bathrooms_idx = np.random.choice(n_houses, size=int(n_houses * 0.02), replace=False)
    bedrooms[nan_bedrooms_idx] = np.nan
    bathrooms[nan_bathrooms_idx] = np.nan

    # --- Ensamble del DataFrame ---
    df = pd.DataFrame({
        'Unnamed: 0': unnamed_0,
        'id': ids,
        'date': dates,
        'price': price,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'sqft_living': sqft_living,
        'sqft_lot': sqft_lot,
        'floors': floors,
        'waterfront': waterfront,
        'view': view,
        'condition': condition,
        'grade': grade,
        'sqft_above': sqft_above,
        'sqft_basement': sqft_basement,
        'yr_built': yr_built,
        'yr_renovated': yr_renovated,
        'zipcode': zipcode,
        'lat': lat,
        'long': long,
        'sqft_living15': sqft_living15,
        'sqft_lot15': sqft_lot15
    })

    df.to_csv(output_path, index=False)
    print(f"[+] Dataset sintetico King County ({n_houses} propiedades) generado en: {output_path}")
    print(f"    NaN inyectados: {len(nan_bedrooms_idx)} en bedrooms, {len(nan_bathrooms_idx)} en bathrooms")

if __name__ == "__main__":
    print("[*] Generando dataset sintetico de ventas inmobiliarias King County...")
    generate_king_county_housing()
