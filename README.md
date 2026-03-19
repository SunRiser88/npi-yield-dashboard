# ⚙️ NPI Yield Learning Dashboard
### New Product Introduction · Inline Monitoring · Excursion Detection

A portfolio-grade Render application simulating an **NPI (New Product Introduction) Yield Learning** system for advanced semiconductor packaging — covering yield ramp tracking, inline SPC, excursion alerting, and product configuration.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## 📊 Features

| Page | Description |
|------|-------------|
| **NPI Overview** | Multi-product yield comparison, ramp phase breakdown |
| **Yield Ramp** | Lot-by-lot yield ramp curve with Ramp-Up → HVM phases, excursion markers |
| **Inline Control** | SPC control charts (X̄ ± 3σ), Cp calculation, distribution histogram |
| **Excursion Manager** | Rule-based excursion detection log, status tracking, severity filtering |
| **NPI Config** | Product onboarding form, threshold configuration, readiness checklist |

---

## 🏗️ Architecture

```
project2_yield_dashboard/
├── app.py               # Streamlit UI — 5 pages
├── data_generator.py    # Synthetic NPI + metrology + excursion data
└── requirements.txt
```

**Data pipeline flow:**
```
NPI Config → Lot Release → Inline Metrology → Excursion Rules Engine → Alert Log → Yield Dashboard
```

---

## 🛠️ Tech Stack
- **Python** · **Render** · **Plotly** · **pandas** · **numpy**
