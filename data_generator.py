import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

PRODUCTS = {
    "PKG-A100": {"layers": 8, "target_yield": 88, "target_density": 0.05, "color": "#38bdf8"},
    "PKG-B200": {"layers": 12, "target_yield": 82, "target_density": 0.07, "color": "#22c55e"},
    "PKG-C300": {"layers": 6,  "target_yield": 91, "target_density": 0.04, "color": "#f97316"},
    "PKG-D400": {"layers": 16, "target_yield": 78, "target_density": 0.09, "color": "#8b5cf6"},
}

PROCESS_STEPS = ["Die Attach", "Wire Bond", "Encapsulation", "Singulation", "Inspection", "Test"]
INLINE_METRICS = ["Defect Density", "Overlay Error (nm)", "CD Uniformity (%)", "Film Thickness (Å)"]

EXCURSION_RULES = {
    "Defect Density": {"threshold": 0.10, "direction": "above", "severity": "critical"},
    "Overlay Error (nm)": {"threshold": 5.0, "direction": "above", "severity": "warning"},
    "CD Uniformity (%)": {"threshold": 3.0, "direction": "above", "severity": "warning"},
    "Film Thickness (Å)": {"threshold": 15.0, "direction": "deviation", "center": 100.0, "severity": "critical"},
}


def generate_npi_timeline(product_id: str, n_lots: int = 30, seed: int = 42):
    np.random.seed(seed)
    product = PRODUCTS[product_id]
    base_date = datetime(2024, 1, 1)
    records = []

    # Yield ramp: starts low, improves over time
    for i in range(n_lots):
        date = base_date + timedelta(days=i * 2)
        # Sigmoid yield ramp
        ramp_factor = 1 / (1 + np.exp(-0.3 * (i - n_lots / 2)))
        yield_base = product["target_yield"] * ramp_factor + np.random.normal(0, 2)
        yield_val = float(np.clip(yield_base, 20, 100))

        defect_density = product["target_density"] * (1.5 - ramp_factor) + abs(np.random.normal(0, 0.01))
        overlay_error = np.random.normal(3.0, 0.8) * (1.2 - ramp_factor * 0.4)
        cd_uniformity = np.random.normal(2.0, 0.5) * (1.2 - ramp_factor * 0.4)
        film_thickness = np.random.normal(100.0, 8.0 * (1.2 - ramp_factor * 0.5))

        excursion = False
        excursion_metric = None
        if defect_density > EXCURSION_RULES["Defect Density"]["threshold"]:
            excursion = True
            excursion_metric = "Defect Density"
        elif overlay_error > EXCURSION_RULES["Overlay Error (nm)"]["threshold"]:
            excursion = True
            excursion_metric = "Overlay Error (nm)"

        step = PROCESS_STEPS[i % len(PROCESS_STEPS)]
        records.append({
            "lot_id": f"LOT{str(i+1).zfill(3)}",
            "date": date,
            "product_id": product_id,
            "process_step": step,
            "lot_index": i + 1,
            "yield_pct": round(yield_val, 2),
            "defect_density": round(float(defect_density), 5),
            "overlay_error_nm": round(float(overlay_error), 3),
            "cd_uniformity_pct": round(float(cd_uniformity), 3),
            "film_thickness_A": round(float(film_thickness), 2),
            "excursion": excursion,
            "excursion_metric": excursion_metric,
            "ramp_phase": "Ramp-Up" if i < n_lots * 0.4 else ("Ramp-Mid" if i < n_lots * 0.7 else "HVM"),
        })

    return pd.DataFrame(records)


def generate_all_products(n_lots: int = 30):
    dfs = []
    for pid in PRODUCTS:
        seed = abs(hash(pid)) % 1000
        dfs.append(generate_npi_timeline(pid, n_lots=n_lots, seed=seed))
    return pd.concat(dfs, ignore_index=True)


def generate_inline_control_chart(product_id: str, metric: str, n_points: int = 60, seed: int = 0):
    np.random.seed(seed)
    product = PRODUCTS[product_id]
    rule = EXCURSION_RULES.get(metric, {})

    if metric == "Defect Density":
        center, sigma = product["target_density"], product["target_density"] * 0.3
    elif metric == "Overlay Error (nm)":
        center, sigma = 3.0, 0.8
    elif metric == "CD Uniformity (%)":
        center, sigma = 2.0, 0.5
    else:
        center, sigma = 100.0, 5.0

    values = np.random.normal(center, sigma, n_points)
    # Inject a few excursions
    excursion_idx = np.random.choice(n_points, size=4, replace=False)
    values[excursion_idx] += sigma * np.random.uniform(2, 4, 4) * np.random.choice([-1, 1], 4)

    ucl = center + 3 * sigma
    lcl = center - 3 * sigma

    return pd.DataFrame({
        "sample": range(1, n_points + 1),
        "value": np.round(values, 4),
        "UCL": ucl,
        "LCL": lcl,
        "CL": center,
        "out_of_control": (values > ucl) | (values < lcl),
    })


def generate_excursion_log(all_df: pd.DataFrame):
    exc = all_df[all_df["excursion"]].copy()
    exc["severity"] = exc["excursion_metric"].map(
        lambda m: EXCURSION_RULES.get(m, {}).get("severity", "warning") if m else "info"
    )
    exc["status"] = np.random.choice(["Open", "In Review", "Closed"], len(exc),
                                     p=[0.3, 0.3, 0.4])
    return exc[["lot_id", "date", "product_id", "process_step",
                "excursion_metric", "severity", "status", "yield_pct"]].reset_index(drop=True)
