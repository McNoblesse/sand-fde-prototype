# Sand Technologies – Forward Deployed Engineer Assignment

## Overview

This repository contains my submission for the **Sand Technologies Forward Deployed Engineer (FDE) Recruitment Assignment**.

The solution is a prototype **Neonatal Health Decision Support Platform** that transforms raw health datasets into actionable insights for decision-makers through interactive analytics and dashboards.

The application demonstrates:

- Executive health monitoring
- Clinical outcome analytics
- Facility capacity assessment
- Workforce analytics
- Governance monitoring
- Facility performance ranking
- Risk scoring
- Intervention prioritization
- Automated recommendations

The prototype was developed using Python and Streamlit with a modular analytics architecture.

---

# Project Structure

```
sand-fde-prototype/
│
├── dashboard/
│   ├── app.py
│   ├── assets/
│   ├── components/
│   └── pages/
│
├── src/
│   ├── data_loader.py
│   ├── dashboard_engine.py
│   ├── health_analytics_engine.py
│   ├── risk_analytics_engine.py
│   ├── intervention_engine.py
│   └── recommendation_engine.py
│
├── data/
│   ├── clinical_neonatal.csv
│   ├── facilities.csv
│   ├── governance.csv
│   ├── healthcare_workers.csv
│   └── operations.csv
│
├── requirements.txt
└── README.md
```

---

# Technology Stack

- Python 3.13
- Streamlit
- Pandas
- Plotly

---

# Installation

Clone the repository

```bash
git clone https://github.com/<your-username>/sand-fde-prototype.git

cd sand-fde-prototype
```

Create a virtual environment

### Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

Launch the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

The application will automatically open in your browser.

If it does not, navigate to

```
http://localhost:8501
```

---

# Dashboard Modules

The dashboard contains the following analytical modules:

- Executive Overview
- Clinical Outcomes
- Facility Capacity
- Workforce Analytics
- Governance Analytics
- Facility Performance Ranking
- Risk Analytics
- Intervention Opportunities
- Automated Recommendations

---

# Data

The prototype uses five datasets located in the **data/** folder:

- clinical_neonatal.csv
- facilities.csv
- governance.csv
- healthcare_workers.csv
- operations.csv

These datasets are automatically loaded by the application.

---

# Prototype Workflow

```
CSV Data
     │
     ▼
Data Loader
     │
     ▼
Analytics Engine
     │
     ▼
Risk Analytics
     │
     ▼
Intervention Engine
     │
     ▼
Recommendation Engine
     │
     ▼
Dashboard Engine
     │
     ▼
Streamlit Dashboard
```

---

# Author

**Joshua Oluwole**

Forward Deployed Engineer Recruitment Assignment

Sand Technologies
