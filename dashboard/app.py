import os
import sys

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------------------------------------------
# Allow imports from src/
# -------------------------------------------------------
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from data_loader import DataLoader # pyrefly: ignore [missing-import]
from dashboard_engine import DashboardEngine # pyrefly: ignore [missing-import]

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------
st.set_page_config(
    page_title="Ministry of Health - Quarterly Bulletin Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------
# Load Data
# -------------------------------------------------------
@st.cache_data
def load_data():

    loader = DataLoader(
        os.path.join(PROJECT_ROOT, "data")
    )

    clinical, facility_master, quality = loader.process()

    dashboard = DashboardEngine(
        clinical=clinical,
        facility=facility_master
    )

    return dashboard


dashboard = load_data()

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------
st.sidebar.title("🏥 Neonatal Dashboard")

page = st.sidebar.selectbox(
    "📂 Select Dashboard",
    [
        "Overview",
        "Clinical",
        "Facility",
        "Workforce",
        "Governance",
        "Performance",
        "Risk",
        "Recommendations",
    ]
)

# -------------------------------------------------------
# Overview Page
# -------------------------------------------------------
if page == "Overview":

    st.title("🏥 Ministry of Health - Quarterly Bulletin Dashboard")
    st.caption("National Neonatal Health Monitoring & Decision Support Dashboard")

    summary = dashboard.executive()
    clinical = dashboard.clinical()
    performance = dashboard.performance()
    risk = dashboard.risk()

    # =====================================================
    # KPI Cards
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Facilities",
        f"{summary['total_facilities']:,}"
    )

    c2.metric(
        "Deliveries",
        f"{summary['total_deliveries']:,}"
    )

    c3.metric(
        "Live Births",
        f"{summary['live_births']:,}"
    )

    c4.metric(
        "Neonatal Deaths",
        f"{summary['neonatal_deaths']:,}"
    )

    c5.metric(
        "Stillbirths",
        f"{summary['stillbirths']:,}"
    )

    st.divider()

    # =====================================================
    # Clinical Indicators
    # =====================================================

    st.subheader("Clinical Indicators")

    indicator_df = pd.DataFrame({

        "Indicator":[
            "Neonatal Mortality",
            "Stillbirth",
            "Prematurity",
            "Low Birth Weight",
            "Low APGAR"
        ],

        "Rate":[
            clinical["neonatal_mortality_rate"],
            clinical["stillbirth_rate"],
            clinical["prematurity_rate"],
            clinical["low_birth_weight_rate"],
            clinical["low_apgar_rate"]
        ]
    })

    fig = px.bar(
        indicator_df,
        x="Indicator",
        y="Rate",
        text="Rate",
        color="Rate"
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        height=420,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # Top Performers vs Highest Risk
    # =====================================================

    left, right = st.columns(2)

    with left:

        st.subheader("🏆 Top Performing Facilities")

        st.dataframe(

            performance[
                [
                    "rank",
                    "facility_name",
                    "province",
                    "performance_score",
                    "performance_grade"
                ]
            ].head(10),

            use_container_width=True,
            hide_index=True
        )

    with right:

        st.subheader("⚠ Highest Risk Facilities")

        st.dataframe(

            risk.sort_values(
                "risk_score",
                ascending=False
            )[
                [
                    "facility_name",
                    "province",
                    "risk_score",
                    "risk_level"
                ]
            ].head(10),

            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # =====================================================
    # Risk Distribution
    # =====================================================

    st.subheader("Facility Risk Distribution")

    risk_counts = (
        risk["risk_level"]
        .value_counts()
        .reset_index()
    )

    risk_counts.columns = [
        "Risk Level",
        "Facilities"
    ]

    fig2 = px.pie(
        risk_counts,
        names="Risk Level",
        values="Facilities",
        hole=.45
    )

    fig2.update_layout(height=500)

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

# -------------------------------------------------------
# Clinical Outcomes Page
# -------------------------------------------------------
elif page == "Clinical":

    st.title("🩺 Clinical Outcomes")

    metrics = dashboard.clinical()
    summary = dashboard.executive()

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Neonatal Mortality",
        f"{metrics['neonatal_mortality_rate']:.2f}/1000"
    )

    c2.metric(
        "Stillbirth Rate",
        f"{metrics['stillbirth_rate']:.2f}%"
    )

    c3.metric(
        "Prematurity",
        f"{metrics['prematurity_rate']:.2f}%"
    )

    c4.metric(
        "Low Birth Weight",
        f"{metrics['low_birth_weight_rate']:.2f}%"
    )

    c5.metric(
        "Low APGAR",
        f"{metrics['low_apgar_rate']:.2f}%"
    )

    st.divider()

    # =====================================================
    # BAR CHART
    # =====================================================

    st.subheader("Clinical Indicator Comparison")

    indicator_df = pd.DataFrame({
        "Indicator": [
            "Neonatal Mortality",
            "Stillbirth Rate",
            "Prematurity Rate",
            "Low Birth Weight",
            "Low APGAR"
        ],
        "Value": [
            metrics["neonatal_mortality_rate"],
            metrics["stillbirth_rate"],
            metrics["prematurity_rate"],
            metrics["low_birth_weight_rate"],
            metrics["low_apgar_rate"]
        ]
    })

    fig = px.bar(
        indicator_df,
        x="Indicator",
        y="Value",
        text="Value",
        title="National Clinical Indicators"
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # BIRTH OUTCOME PIE CHART
    # =====================================================

    st.subheader("Birth Outcome Distribution")

    birth_df = pd.DataFrame({
        "Category": [
            "Live Births",
            "Stillbirths"
        ],
        "Count": [
            summary["live_births"],
            summary["stillbirths"]
        ]
    })

    fig = px.pie(
        birth_df,
        names="Category",
        values="Count",
        hole=0.45,
        title="Birth Outcomes"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # CLINICAL SUMMARY TABLE
    # =====================================================

    st.subheader("Clinical Summary")

    summary_df = pd.DataFrame({

        "Indicator": [

            "Total Deliveries",
            "Live Births",
            "Neonatal Deaths",
            "Stillbirths",
            "Neonatal Mortality Rate",
            "Stillbirth Rate",
            "Prematurity Rate",
            "Low Birth Weight Rate",
            "Low APGAR Rate"

        ],

        "Value": [

            f"{summary['total_deliveries']:,}",
            f"{summary['live_births']:,}",
            f"{summary['neonatal_deaths']:,}",
            f"{summary['stillbirths']:,}",
            f"{metrics['neonatal_mortality_rate']:.2f}/1000",
            f"{metrics['stillbirth_rate']:.2f}%",
            f"{metrics['prematurity_rate']:.2f}%",
            f"{metrics['low_birth_weight_rate']:.2f}%",
            f"{metrics['low_apgar_rate']:.2f}%"

        ]

    })

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

# -------------------------------------------------------
# Facility Capacity Page
# -------------------------------------------------------
elif page == "Facility":

    st.title("🏥 Facility Capacity")

    metrics = dashboard.facility()

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "NICU Coverage",
        f"{metrics['nicu_coverage_pct']:.2f}%"
    )

    c2.metric(
        "Electricity Reliability",
        f"{metrics['electricity_reliability_pct']:.2f}%"
    )

    c3.metric(
        "Backup Generator",
        f"{metrics['backup_generator_pct']:.2f}%"
    )

    c4.metric(
        "Kangaroo Care",
        f"{metrics['kangaroo_space_pct']:.2f}%"
    )

    st.divider()

    # =====================================================
    # EQUIPMENT METRICS
    # =====================================================

    e1, e2, e3 = st.columns(3)

    e1.metric(
        "NICU Beds",
        f"{metrics['total_nicu_beds']:,}"
    )

    e2.metric(
        "Functional Incubators",
        f"{metrics['functional_incubators']:,}"
    )

    e3.metric(
        "CPAP Machines",
        f"{metrics['cpap_machines']:,}"
    )

    st.divider()

    # =====================================================
    # INFRASTRUCTURE READINESS
    # =====================================================

    st.subheader("Infrastructure Readiness")

    infra_df = pd.DataFrame({

        "Indicator": [
            "NICU Availability",
            "Reliable Electricity",
            "Backup Generator",
            "Kangaroo Care Space"
        ],

        "Coverage (%)": [

            metrics["nicu_coverage_pct"],
            metrics["electricity_reliability_pct"],
            metrics["backup_generator_pct"],
            metrics["kangaroo_space_pct"]

        ]

    })

    fig = px.bar(
        infra_df,
        x="Indicator",
        y="Coverage (%)",
        text="Coverage (%)",
        title="National Facility Infrastructure Coverage"
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # EQUIPMENT DISTRIBUTION
    # =====================================================

    st.subheader("Critical Equipment")

    equipment_df = pd.DataFrame({

        "Equipment": [
            "NICU Beds",
            "Functional Incubators",
            "CPAP Machines"
        ],

        "Quantity": [

            metrics["total_nicu_beds"],
            metrics["functional_incubators"],
            metrics["cpap_machines"]

        ]

    })

    fig = px.pie(
        equipment_df,
        names="Equipment",
        values="Quantity",
        hole=0.45,
        title="Distribution of Critical Equipment"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # FACILITY SUMMARY TABLE
    # =====================================================

    st.subheader("Facility Capacity Summary")

    summary_df = pd.DataFrame({

        "Indicator": [

            "NICU Coverage",
            "Reliable Electricity",
            "Backup Generator",
            "Kangaroo Care Space",
            "NICU Beds",
            "Functional Incubators",
            "CPAP Machines"

        ],

        "Value": [

            f"{metrics['nicu_coverage_pct']:.2f}%",
            f"{metrics['electricity_reliability_pct']:.2f}%",
            f"{metrics['backup_generator_pct']:.2f}%",
            f"{metrics['kangaroo_space_pct']:.2f}%",
            f"{metrics['total_nicu_beds']:,}",
            f"{metrics['functional_incubators']:,}",
            f"{metrics['cpap_machines']:,}"

        ]

    })

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

# -------------------------------------------------------
# Workforce Page
# -------------------------------------------------------
elif page == "Workforce":

    st.title("👩🏽‍⚕️ Workforce Capacity")

    metrics = dashboard.workforce()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Nurses",
        f"{metrics['total_nurses']:,}"
    )

    c2.metric(
        "Neonatal Trained Nurses",
        f"{metrics['trained_neonatal_nurses']:,}"
    )

    c3.metric(
        "Training Coverage",
        f"{metrics['training_coverage_pct']:.1f}%"
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Midwives",
        f"{metrics['midwives']:,}"
    )

    c2.metric(
        "Pediatricians",
        f"{metrics['pediatricians']:,}"
    )

    c3.metric(
        "Neonatologists",
        f"{metrics['neonatologists']:,}"
    )

    st.divider()

    c1, c2 = st.columns(2)

    c1.metric(
        "Night Shift Coverage",
        f"{metrics['night_shift_coverage_pct']:.1f}%"
    )

    st.divider()

    workforce_df = dashboard.health.facility.copy()

    st.subheader("Facility Workforce")

    st.dataframe(
        workforce_df[
            [
                "facility_name",
                "province",
                "district",
                "total_nurses",
                "neonatal_trained_nurses",
                "midwives",
                "pediatricians",
                "neonatologists",
                "night_shift_coverage"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    cadre = pd.DataFrame({
        "Cadre": [
            "Nurses",
            "Midwives",
            "Pediatricians",
            "Neonatologists"
        ],
        "Count": [
            metrics["total_nurses"],
            metrics["midwives"],
            metrics["pediatricians"],
            metrics["neonatologists"]
        ]
    })

    fig = px.bar(
        cadre,
        x="Cadre",
        y="Count",
        text="Count",
        color="Cadre",
        title="Distribution of Healthcare Workforce"
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    trained = pd.DataFrame({
        "Category": [
            "Trained",
            "Not Trained"
        ],
        "Count": [
            metrics["trained_neonatal_nurses"],
            metrics["total_nurses"] - metrics["trained_neonatal_nurses"]
        ]
    })

    fig = px.pie(
        trained,
        names="Category",
        values="Count",
        hole=0.55,
        title="Neonatal Training Coverage"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    shift = (
        workforce_df["night_shift_coverage"]
        .value_counts()
        .rename_axis("Coverage")
        .reset_index(name="Facilities")
    )

    fig = px.bar(
        shift,
        x="Coverage",
        y="Facilities",
        text="Facilities",
        color="Coverage",
        title="Night Shift Coverage Across Facilities"
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# -------------------------------------------------------
# Governance Page
# -------------------------------------------------------
elif page == "Governance":

    st.title("📋 Governance & Quality Improvement")

    metrics = dashboard.governance()

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Quality Improvement",
        f"{metrics['quality_improvement_pct']:.1f}%"
    )

    c2.metric(
        "Protocol Availability",
        f"{metrics['protocol_availability_pct']:.1f}%"
    )

    c3.metric(
        "HMIS Reporting",
        f"{metrics['average_hmis_reporting']:.1f}%"
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Protocol Training",
        f"{metrics['average_protocol_training']:.1f}%"
    )

    c2.metric(
        "Death Audit Coverage",
        f"{metrics['average_death_audit']:.1f}%"
    )

    c3.metric(
        "IPC Score",
        f"{metrics['infection_prevention_score']:.1f}%"
    )

    st.divider()

    # =====================================================
    # GOVERNANCE TABLE
    # =====================================================

    governance_df = dashboard.health.facility.copy()

    st.subheader("Facility Governance Status")

    st.dataframe(

        governance_df[
            [
                "facility_name",
                "province",
                "district",
                "quality_improvement_active",
                "newborn_protocol_exists",
                "protocol_last_updated",
                "staff_trained_on_protocol_pct",
                "death_audits_conducted_pct",
                "hmis_reporting_completeness",
                "infection_prevention_score"
            ]
        ],

        use_container_width=True,
        hide_index=True

    )

    st.divider()

    # =====================================================
    # GOVERNANCE INDICATORS
    # =====================================================

    indicator_df = pd.DataFrame({

        "Indicator": [

            "Quality Improvement",
            "Protocol Availability",
            "HMIS Reporting",
            "Protocol Training",
            "Death Audits",
            "IPC Score"

        ],

        "Score": [

            metrics["quality_improvement_pct"],
            metrics["protocol_availability_pct"],
            metrics["average_hmis_reporting"],
            metrics["average_protocol_training"],
            metrics["average_death_audit"],
            metrics["infection_prevention_score"]

        ]

    })

    fig = px.bar(

        indicator_df,

        x="Indicator",

        y="Score",

        text="Score",

        color="Score",

        title="National Governance Indicators"

    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(

        fig,

        use_container_width=True

    )

    st.divider()

    # =====================================================
    # GOVERNANCE RADAR CHART
    # =====================================================

    radar = go.Figure()

    radar.add_trace(

        go.Scatterpolar(

            r=indicator_df["Score"],

            theta=indicator_df["Indicator"],

            fill="toself",

            name="Governance"

        )

    )

    radar.update_layout(

        polar=dict(

            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )

        ),

        title="Governance Maturity Profile"

    )

    st.plotly_chart(

        radar,

        use_container_width=True

    )

    st.divider()

    # =====================================================
    # SUMMARY TABLE
    # =====================================================

    summary_df = pd.DataFrame({

        "Indicator": indicator_df["Indicator"],

        "National Average (%)": indicator_df["Score"].round(2)

    })

    st.subheader("Governance Summary")

    st.dataframe(

        summary_df,

        use_container_width=True,

        hide_index=True

    )

# -------------------------------------------------------
# Facility Performance Page
# -------------------------------------------------------
elif page == "Performance":

    st.title("🏆 Facility Performance Ranking")

    performance = dashboard.performance()

    # =====================================================
    # TOP KPI CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Facilities Assessed",
        len(performance)
    )

    c2.metric(
        "Average Score",
        f"{performance['performance_score'].mean():.1f}"
    )

    c3.metric(
        "Highest Score",
        f"{performance['performance_score'].max():.1f}"
    )

    c4.metric(
        "Lowest Score",
        f"{performance['performance_score'].min():.1f}"
    )

    st.divider()

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2 = st.columns(2)

    provinces = ["All"] + sorted(performance["province"].dropna().unique())

    province = col1.selectbox(
        "Province",
        provinces
    )

    grades = ["All"] + sorted(
        performance["performance_grade"]
        .astype(str)
        .unique()
    )

    grade = col2.selectbox(
        "Performance Grade",
        grades
    )

    filtered = performance.copy()

    if province != "All":
        filtered = filtered[
            filtered["province"] == province
        ]

    if grade != "All":
        filtered = filtered[
            filtered["performance_grade"].astype(str) == grade
        ]

    st.divider()

    # =====================================================
    # PERFORMANCE TABLE
    # =====================================================

    st.subheader("Facility Leaderboard")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =====================================================
    # TOP 10 FACILITIES
    # =====================================================

    st.subheader("Top 10 Performing Facilities")

    top10 = filtered.nlargest(
        10,
        "performance_score"
    )

    fig = px.bar(
        top10,
        x="performance_score",
        y="facility_name",
        orientation="h",
        color="performance_score",
        text="performance_score",
        title="Top Performing Facilities"
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed")
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # BOTTOM 10 FACILITIES
    # =====================================================

    st.subheader("Lowest Performing Facilities")

    bottom10 = filtered.nsmallest(
        10,
        "performance_score"
    )

    fig = px.bar(
        bottom10,
        x="performance_score",
        y="facility_name",
        orientation="h",
        color="performance_score",
        text="performance_score",
        title="Facilities Requiring Immediate Attention"
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed")
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # GRADE DISTRIBUTION
    # =====================================================

    st.subheader("Performance Grade Distribution")

    grade_df = (
        filtered["performance_grade"]
        .astype(str)
        .value_counts()
        .reset_index()
    )

    grade_df.columns = [
        "Grade",
        "Facilities"
    ]

    fig = px.pie(
        grade_df,
        names="Grade",
        values="Facilities",
        hole=0.45,
        title="Performance Grade Distribution"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # SCORE DISTRIBUTION
    # =====================================================

    st.subheader("Performance Score Distribution")

    fig = px.histogram(
        filtered,
        x="performance_score",
        nbins=20,
        title="Distribution of Performance Scores"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# -------------------------------------------------------
# Risk Analytics Page
# -------------------------------------------------------
elif page == "Risk":

    st.title("🚨 Facility Risk Analytics")

    risk = dashboard.risk()

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Facilities",
        len(risk)
    )

    c2.metric(
        "Average Risk Score",
        f"{risk['risk_score'].mean():.2f}"
    )

    c3.metric(
        "Highest Risk",
        f"{risk['risk_score'].max():.2f}"
    )

    c4.metric(
        "Critical Facilities",
        (risk["risk_level"] == "Critical").sum()
    )

    st.divider()

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2 = st.columns(2)

    province = col1.selectbox(
        "Province",
        ["All"] + sorted(risk["province"].dropna().unique()),
        key="risk_province"
    )

    level = col2.selectbox(
        "Risk Level",
        ["All"] + list(risk["risk_level"].astype(str).unique()),
        key="risk_level"
    )

    filtered = risk.copy()

    if province != "All":
        filtered = filtered[
            filtered["province"] == province
        ]

    if level != "All":
        filtered = filtered[
            filtered["risk_level"].astype(str) == level
        ]

    st.divider()

    # =====================================================
    # RISK TABLE
    # =====================================================

    st.subheader("Facility Risk Register")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =====================================================
    # TOP 15 HIGHEST RISK
    # =====================================================

    st.subheader("Highest Risk Facilities")

    highest = filtered.nlargest(
        15,
        "risk_score"
    )

    fig = px.bar(
        highest,
        x="risk_score",
        y="facility_name",
        orientation="h",
        color="risk_level",
        text="risk_score",
        title="Highest Risk Facilities"
    )

    fig.update_layout(
        yaxis=dict(
            autorange="reversed"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # RISK LEVEL DISTRIBUTION
    # =====================================================

    st.subheader("Risk Level Distribution")

    risk_dist = (
        filtered["risk_level"]
        .astype(str)
        .value_counts()
        .reset_index()
    )

    risk_dist.columns = [
        "Risk Level",
        "Facilities"
    ]

    fig = px.pie(
        risk_dist,
        names="Risk Level",
        values="Facilities",
        hole=0.45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # RISK SCORE DISTRIBUTION
    # =====================================================

    st.subheader("Risk Score Distribution")

    fig = px.histogram(
        filtered,
        x="risk_score",
        nbins=20,
        title="Distribution of Risk Scores"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # PROVINCE RISK SUMMARY
    # =====================================================

    st.subheader("Average Risk by Province")

    province_risk = (
        filtered
        .groupby("province", as_index=False)
        .agg(
            average_risk=("risk_score", "mean")
        )
        .sort_values(
            "average_risk",
            ascending=False
        )
    )

    fig = px.bar(
        province_risk,
        x="province",
        y="average_risk",
        text="average_risk",
        color="average_risk",
        title="Average Risk Score by Province"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # RISK VS PERFORMANCE
    # =====================================================

    st.subheader("Risk vs Performance")

    fig = px.scatter(
        filtered,
        x="performance_score",
        y="risk_score",
        color="risk_level",
        size="risk_score",
        hover_name="facility_name",
        title="Risk vs Performance Score"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# -------------------------------------------------------
# Recommendations Page
# -------------------------------------------------------
elif page == "Recommendations":

    st.title("🎯 Intervention & Recommendations")

    recommendations = dashboard.recommendations()
    opportunity = dashboard.opportunity()

    # =====================================================
    # KPI CARDS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Facilities",
        len(recommendations)
    )

    c2.metric(
        "Critical Risk",
        (recommendations["risk_level"] == "Critical").sum()
    )

    c3.metric(
        "High Risk",
        (recommendations["risk_level"] == "High").sum()
    )

    c4.metric(
        "Average Opportunity Score",
        f"{opportunity['opportunity_score'].mean():.1f}"
    )

    st.divider()

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2 = st.columns(2)

    province = col1.selectbox(
        "Province",
        ["All"] + sorted(recommendations["province"].dropna().unique()),
        key="recommendation_province"
    )

    level = col2.selectbox(
        "Risk Level",
        ["All"] + list(recommendations["risk_level"].astype(str).unique()),
        key="recommendation_level"
    )

    filtered = recommendations.copy()

    if province != "All":
        filtered = filtered[
            filtered["province"] == province
        ]

    if level != "All":
        filtered = filtered[
            filtered["risk_level"].astype(str) == level
        ]

    st.divider()

    # =====================================================
    # RECOMMENDATION TABLE
    # =====================================================

    st.subheader("Facility Action Plan")

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =====================================================
    # TOP PRIORITY FACILITIES
    # =====================================================

    st.subheader("Top 15 Priority Facilities")

    top_priority = opportunity.nlargest(
        15,
        "opportunity_score"
    )

    fig = px.bar(
        top_priority,
        x="opportunity_score",
        y="facility_name",
        orientation="h",
        color="opportunity_level",
        text="opportunity_score",
        title="Facilities with Highest Improvement Opportunity"
    )

    fig.update_layout(
        yaxis=dict(
            autorange="reversed"
        )
    )

    fig.update_traces(
        texttemplate="%{text:.1f}"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # OPPORTUNITY LEVELS
    # =====================================================

    st.subheader("Opportunity Distribution")

    opp = (
        opportunity["opportunity_level"]
        .astype(str)
        .value_counts()
        .reset_index()
    )

    opp.columns = [
        "Opportunity Level",
        "Facilities"
    ]

    fig = px.pie(
        opp,
        names="Opportunity Level",
        values="Facilities",
        hole=0.45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # RECOMMENDATION FREQUENCY
    # =====================================================

    st.subheader("Most Common Recommended Actions")

    recommendation_counts = (
        filtered["recommendation"]
        .str.split(";")
        .explode()
        .str.strip()
        .value_counts()
        .reset_index()
    )

    recommendation_counts.columns = [
        "Recommendation",
        "Facilities"
    ]

    fig = px.bar(
        recommendation_counts,
        x="Facilities",
        y="Recommendation",
        orientation="h",
        color="Facilities",
        text="Facilities",
        title="Recommended Interventions Across Facilities"
    )

    fig.update_layout(
        yaxis=dict(
            autorange="reversed"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # DOWNLOAD
    # =====================================================

    csv = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Recommendations (CSV)",
        data=csv,
        file_name="facility_recommendations.csv",
        mime="text/csv"
    )

    st.divider()

    # =====================================================
    # EXECUTIVE SUMMARY
    # =====================================================

    st.info(
        f"""
### Executive Summary

- **{(recommendations['risk_level'] == 'Critical').sum()} facilities** require immediate intervention.
- **{(recommendations['risk_level'] == 'High').sum()} facilities** should receive priority monitoring.
- Average opportunity score across all facilities is **{opportunity['opportunity_score'].mean():.1f}**.
- Recommendations are generated automatically from the integrated clinical, infrastructure, workforce and governance analytics.
"""
    )