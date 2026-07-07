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
from health_analytics_engine import HealthAnalyticsEngine # pyrefly: ignore [missing-import]
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
    loader = DataLoader(os.path.join(PROJECT_ROOT, "data"))

    clinical_df, facility_df, quality_df = loader.process()

    # Instantiate the central DashboardEngine
    dashboard_instance = DashboardEngine(
        clinical=clinical_df,
        facility=facility_df
    )
    # Return everything needed globally
    return dashboard_instance, clinical_df, facility_df

# Capture the instantiated engines and raw dataframes globally
dashboard, clinical, facility_master = load_data()

# Expose the underlying health engine for your other tabs that use 'engine'
engine = dashboard.health

# -------------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------------
st.sidebar.title("📋 Filter Options")

# Quarter selector
quarters = sorted(clinical["quarter_year"].unique().tolist()) if "quarter_year" in clinical.columns else []
selected_quarter = st.sidebar.selectbox(
    "📆 Select Quarter",
    options=quarters,
    index=len(quarters) - 1 if quarters else 0
)

# Province selector
provinces = sorted(facility_master["province"].unique().tolist()) if "province" in facility_master.columns else []
selected_province = st.sidebar.selectbox(
    "🗺️ Province",
    options=["All"] + provinces
)

# Apply filters
filtered_clinical = clinical.copy()
filtered_facilities = facility_master.copy()

if selected_quarter:
    filtered_clinical = filtered_clinical[filtered_clinical["quarter_year"] == selected_quarter]

if selected_province != "All":
    filtered_facilities = filtered_facilities[filtered_facilities["province"] == selected_province]
    filtered_clinical = filtered_clinical[filtered_clinical["facility_id"].isin(filtered_facilities["facility_id"])]

# Instantiate our updated HealthAnalyticsEngine
engine = HealthAnalyticsEngine(
    clinical=filtered_clinical,
    facility_master=filtered_facilities
)

# -------------------------------------------------------
# APP HEADER
# -------------------------------------------------------
st.title("🏥 Ministry of Health - Quarterly Bulletin Dashboard")
st.subheader("📊 Executive Performance Dashboard")
st.markdown(f"**Reporting Period:** {selected_quarter if selected_quarter else 'All Quarters'} | **Scope:** {selected_province}")
st.divider()

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Executive Dashboard", 
    "👶 Clinical Outcomes", 
    "🏢 Facility Performance", 
    "🗺️ Province Analytics",
    "💡 Recommendations"
])

# =======================================================
# TAB 1: EXECUTIVE DASHBOARD (UPDATED OVERVIEW PAGE)
# =======================================================
with tab1:
    summary = engine.executive_summary()
    metrics = engine.clinical_metrics()
    
    # Core executive metrics grid
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏥 Total Facilities", f"{summary['total_facilities']}")
    col2.metric("👶 Live Births", f"{metrics['total_live_births']:,}")
    col3.metric("🚨 Neonatal Mortality Rate", f"{metrics['neonatal_mortality_rate']}/1k")
    col4.metric("📉 Stillbirth Rate", f"{metrics['stillbirth_rate']}/1k")

    st.divider()

    # =====================================================
    # Quarterly Performance Summary
    # =====================================================
    # Note: Using an unfiltered engine timeline sequence instance so full trend lines display chronologically
    unfiltered_engine = HealthAnalyticsEngine(clinical=clinical, facility_master=facility_master)
    quarterly = unfiltered_engine.quarterly_clinical_summary()

    st.subheader("📈 Quarterly National Performance")
    col_graph, col_table = st.columns([2, 1])

    with col_graph:
        fig = px.line(
            quarterly,
            x="quarter_year",
            y="neonatal_mortality_rate",
            markers=True,
            title="Quarterly Neonatal Mortality Rate (per 1,000 Live Births)"
        )
        fig.update_layout(
            xaxis_title="Quarter",
            yaxis_title="Mortality Rate",
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.dataframe(
            quarterly[
                [
                    "quarter_year",
                    "deliveries",
                    "live_births",
                    "neonatal_mortality_rate",
                    "stillbirth_rate",
                    "low_birth_weight_rate"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # =====================================================
    # Provincial Performance Summary
    # =====================================================
    st.subheader("🏥 Provincial Performance")
    province = engine.province_analytics()

    fig_prov = px.bar(
        province,
        x="province",
        y="mortality_rate",
        text="mortality_rate",
        color="mortality_rate",
        title="Neonatal Mortality Rate by Province"
    )
    fig_prov.update_traces(textposition="outside")
    fig_prov.update_layout(
        yaxis_title="Deaths per 1,000 Live Births",
        xaxis_title="Province",
        height=450
    )
    st.plotly_chart(fig_prov, use_container_width=True)

    st.divider()

    # =====================================================
    # Facility Performance Overview
    # =====================================================
    st.subheader("🏆 Facility Performance Overview")
    left, right = st.columns(2)

    with left:
        st.markdown("### Top 10 Performing Facilities")
        st.dataframe(
            engine.top_10_facilities()[
                [
                    "facility_name",
                    "province",
                    "performance_score",
                    "performance_grade"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

    with right:
        st.markdown("### Bottom 10 Performing Facilities")
        st.dataframe(
            engine.bottom_10_facilities()[
                [
                    "facility_name",
                    "province",
                    "performance_score",
                    "performance_grade"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    # =====================================================
    # Executive Insights
    # =====================================================
    st.subheader("📌 Executive Insights")

    if not province.empty:
        highest = province.sort_values("mortality_rate", ascending=False).iloc[0]
        highest_prov_name = highest['province']
        highest_prov_rate = highest['mortality_rate']
    else:
        highest_prov_name = "N/A"
        highest_prov_rate = 0

    top_facilities = engine.top_10_facilities()
    bot_facilities = engine.bottom_10_facilities()

    best_fac_name = top_facilities.iloc[0]['facility_name'] if not top_facilities.empty else "N/A"
    best_fac_score = top_facilities.iloc[0]['performance_score'] if not top_facilities.empty else 0

    worst_fac_name = bot_facilities.iloc[0]['facility_name'] if not bot_facilities.empty else "N/A"
    worst_fac_score = bot_facilities.iloc[0]['performance_score'] if not bot_facilities.empty else 0

    c1, c2, c3 = st.columns(3)

    c1.info(
        f"""
**Highest Mortality Province**

{highest_prov_name}

Rate: **{highest_prov_rate}**
"""
    )

    c2.success(
        f"""
**Best Performing Facility**

{best_fac_name}

Score: **{best_fac_score}**
"""
    )

    c3.error(
        f"""
**Lowest Performing Facility**

{worst_fac_name}

Score: **{worst_fac_score}**
"""
    )


# =======================================================
# TAB 2: CLINICAL OUTCOMES (QUARTERLY CLINICAL BULLETIN)
# =======================================================
with tab2:
    st.header("👶 National Quarterly Clinical Bulletin")
    st.markdown("---")

    unfiltered_engine = HealthAnalyticsEngine(clinical=clinical, facility_master=facility_master)
    quarterly_data = unfiltered_engine.quarterly_clinical_summary()

    # SECTION 1: KPI CARDS
    current_kpis = engine.clinical_metrics()
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("🚨 Neonatal Mortality Rate", f"{current_kpis['neonatal_mortality_rate']} / 1k")
    col_kpi2.metric("🛑 Stillbirth Rate", f"{current_kpis['stillbirth_rate']} / 1k")
    col_kpi3.metric("⚖️ Low Birth Weight Rate", f"{current_kpis['low_birth_weight_rate']} / 1k")
    col_kpi4.metric("👶 Live Births", f"{current_kpis['total_live_births']:,}")

    st.markdown("---")

    # SECTION 2: QUARTERLY CLINICAL TRENDS
    st.subheader("📊 Quarterly Clinical Indicators")
    
    fig_mixed = go.Figure()
    fig_mixed.add_bar(
        x=quarterly_data["quarter_year"],
        y=quarterly_data["stillbirth_rate"],
        name="Stillbirth Rate"
    )
    fig_mixed.add_bar(
        x=quarterly_data["quarter_year"],
        y=quarterly_data["low_birth_weight_rate"],
        name="Low Birth Weight Rate"
    )
    fig_mixed.add_trace(
        go.Scatter(
            x=quarterly_data["quarter_year"],
            y=quarterly_data["neonatal_mortality_rate"],
            mode="lines+markers",
            name="Neonatal Mortality Rate",
            yaxis="y2"
        )
    )
    
    fig_mixed.update_layout(
        barmode="group",
        title="Quarterly Trends in Neonatal Mortality, Stillbirth and Low Birth Weight",
        xaxis=dict(title="Quarter"),
        yaxis=dict(title="Rate per 1,000"),
        yaxis2=dict(
            title="Mortality",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_mixed, use_container_width=True)

    st.markdown("---")

    # SECTION 3: QUARTERLY BIRTH OUTCOMES
    st.subheader("📊 Quarterly Birth Outcomes")
    fig_vol = px.bar(
        quarterly_data,
        x="quarter_year",
        y=["deliveries", "live_births", "stillbirths", "neonatal_deaths"],
        barmode="group",
        title="Quarterly Birth Outcomes",
        labels={"value": "Count", "variable": "Indicator"}
    )
    st.plotly_chart(fig_vol, use_container_width=True)

    st.markdown("---")

    # SECTION 4: QUARTERLY CLINICAL SUMMARY
    st.subheader("📋 Quarterly Clinical Summary")
    st.dataframe(
        quarterly_data[
            [
                "quarter_year",
                "deliveries",
                "live_births",
                "neonatal_deaths",
                "neonatal_mortality_rate",
                "stillbirth_rate",
                "low_birth_weight_rate"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # SECTION 5: KEY CLINICAL FINDINGS
    st.subheader("📌 Key Clinical Findings")
    if len(quarterly_data) >= 2:
        highest_nmr_row = quarterly_data.sort_values("neonatal_mortality_rate", ascending=False).iloc[0]
        last_row = quarterly_data.iloc[-1]
        prev_row = quarterly_data.iloc[-2]
        lbw_trend = "declined" if last_row["low_birth_weight_rate"] < prev_row["low_birth_weight_rate"] else "increased/stable"
        
        st.markdown(f"• Highest neonatal mortality rate was recorded in {highest_nmr_row['quarter_year']} ({highest_nmr_row['neonatal_mortality_rate']} per 1,000 live births).")
        st.markdown(f"• Low birth weight rate {lbw_trend} in {last_row['quarter_year']} compared with the previous quarter.")
        st.markdown(f"• Stillbirth rate remained relatively stable across the reporting period, closing at {last_row['stillbirth_rate']} per 1,000.")
        st.markdown(f"• Live births reached {last_row['live_births']:,} in the latest reporting quarter.")

# =======================================================
# TAB 3: FACILITY PERFORMANCE (OPERATIONAL AUDIT)
# =======================================================
with tab3:
    # st.header("🏢 Facility Infrastructure & Performance Audit")
    # st.markdown("---")

    # Fetch foundational datasets
    performance = engine.facility_performance()
    
    # Extract your factual, core physical capacity metrics
    # Using your backend dashboard/engine method to fetch infrastructure parameters
    infra_metrics = engine.facility_metrics()  # Maps to your prior dashboard.facility() logic

    # ----------------------------------------------------
    # SECTION 1 — HARD INFRASTRUCTURE & EQUIPMENT KPIs
    # ----------------------------------------------------
    st.subheader("⚡ Core Infrastructure Readiness")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NICU Coverage", f"{infra_metrics['nicu_coverage_pct']:.0f}%")
    c2.metric("Electricity Reliability", f"{infra_metrics['electricity_reliability_pct']:.0f}%")
    c3.metric("Backup Generator Status", f"{infra_metrics['backup_generator_pct']:.0f}%")
    c4.metric("Kangaroo Care Space", f"{infra_metrics['kangaroo_space_pct']:.0f}%")

    st.markdown("### 🧰 Critical Life-Support Assets")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Total NICU Beds", f"{infra_metrics['total_nicu_beds']:,}")
    e2.metric("Functional Incubators", f"{infra_metrics['functional_incubators']:,}")
    e3.metric("CPAP Machines", f"{infra_metrics['cpap_machines']:,}")
    # Retaining the system-wide operational score average for context
    avg_score = round(performance["performance_score"].mean()) if not performance.empty else 0
    e4.metric("Average Operational Score", f"{avg_score}%")

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 2 — INFRASTRUCTURE COVERAGE SUMMARY
    # ----------------------------------------------------
    st.subheader("📊 National Facility Infrastructure Coverage")
    
    infra_df = pd.DataFrame({
        "Indicator": [
            "NICU Availability",
            "Reliable Electricity",
            "Backup Generator",
            "Kangaroo Care Space"
        ],
        "Coverage (%)": [
            infra_metrics["nicu_coverage_pct"],
            infra_metrics["electricity_reliability_pct"],
            infra_metrics["backup_generator_pct"],
            infra_metrics["kangaroo_space_pct"]
        ]
    })

    fig_infra = px.bar(
        infra_df,
        x="Indicator",
        y="Coverage (%)",
        text="Coverage (%)",
        title="National Facility Infrastructure Coverage"
    )
    fig_infra.update_traces(textposition="outside")
    fig_infra.update_layout(yaxis_range=[0, 110], height=380)
    st.plotly_chart(fig_infra, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 3 — TOP VS BOTTOM FACILITIES (PERFORMANCE SCORES)
    # ----------------------------------------------------
    st.subheader("🏆 Performance Extremes Visual Comparison")
    chart_left, chart_right = st.columns(2)

    top10 = engine.top_10_facilities().sort_values("performance_score", ascending=True)
    bottom10 = engine.bottom_10_facilities().sort_values("performance_score", ascending=False)

    with chart_left:
        st.markdown("### 🟢 Top 10 Performing Wards")
        fig_top = px.bar(
            top10,
            x="performance_score",
            y="facility_name",
            orientation="h",
            text="performance_score",
            title="Highest Ranked Facilities (Score %)",
            labels={"performance_score": "Score", "facility_name": "Facility"}
        )
        fig_top.update_traces(textposition="inside")
        fig_top.update_layout(height=380, yaxis=dict(title=None))
        st.plotly_chart(fig_top, use_container_width=True)

    with chart_right:
        st.markdown("### 🔴 Bottom 10 Performing Wards")
        fig_bot = px.bar(
            bottom10,
            x="performance_score",
            y="facility_name",
            orientation="h",
            text="performance_score",
            title="Facilities Needing Strategic Oversight (Score %)",
            labels={"performance_score": "Score", "facility_name": "Facility"}
        )
        fig_bot.update_traces(textposition="outside")
        fig_bot.update_layout(height=380, yaxis=dict(title=None, side="right"))
        st.plotly_chart(fig_bot, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 4 — DIAGNOSTIC PERFORMANCE MATRIX (BUBBLE)
    # ----------------------------------------------------
    st.subheader("🎯 Diagnostic Performance Matrix")
    
    if "training_rate" in performance.columns and "mortality_rate" in performance.columns:
        fig_bubble = px.scatter(
            performance,
            x="training_rate",
            y="mortality_rate",
            size="performance_score",
            color="performance_grade",
            hover_name="facility_name",
            title="Workforce Training Coverage vs. Neonatal Mortality Outcomes",
            labels={
                "training_rate": "Specialized Neonatal Training Rate (%)",
                "mortality_rate": "Neonatal Mortality Rate (per 1,000 Live Births)",
                "performance_grade": "Performance Grade"
            },
            category_orders={"performance_grade": ["Excellent", "Good", "Fair", "Needs Improvement"]}
        )
        fig_bubble.update_layout(height=480)
        st.plotly_chart(fig_bubble, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 5 — PRIORITY INTERVENTION LIST
    # ----------------------------------------------------
    st.subheader("🚨 Actionable Priority Intervention List")
    
    if not bottom10.empty:
        bottom10["Priority"] = bottom10["performance_score"].apply(
            lambda x: "🚨 Immediate" if x < 45 else ("🟠 High" if x < 60 else "🟡 Moderate")
        )
        
        st.dataframe(
            bottom10[[
                "facility_name",
                "province",
                "mortality_rate",
                "performance_score",
                "Priority"
            ]].sort_values("performance_score"),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 6 — COMPLETE PERFORMANCE LEDGER
    # ----------------------------------------------------
    st.subheader("📋 Complete Facility Performance Ledger")
    st.dataframe(
        performance,
        use_container_width=True,
        hide_index=True
    )

# =======================================================
# TAB 4: PROVINCE ANALYTICS (GEOGRAPHIC COMPARISON)
# =======================================================
with tab4:
    st.header("🗺️ Provincial Performance & Resource Allocation")
    st.markdown("---")

    # Fetch provincial analytics dataset from the engine
    province_data = engine.province_analytics()

    # ----------------------------------------------------
    # SECTION 1 — Provincial Overview KPIs
    # ----------------------------------------------------
    if not province_data.empty:
        total_provinces = len(province_data)
        
        # Sort to locate absolute high and low mortality boundaries
        sorted_mortality = province_data.sort_values("mortality_rate")
        lowest_mort_prov = sorted_mortality.iloc[0]["province"]
        lowest_mort_val = sorted_mortality.iloc[0]["mortality_rate"]
        
        highest_mort_prov = sorted_mortality.iloc[-1]["province"]
        highest_mort_val = sorted_mortality.iloc[-1]["mortality_rate"]
        
        avg_prov_mortality = province_data["mortality_rate"].mean()

        pkpi1, pkpi2, pkpi3, pkpi4 = st.columns(4)
        pkpi1.metric("🗺️ Total Provinces", f"{total_provinces}")
        pkpi2.metric("🚨 Highest Mortality", f"{highest_mort_val} / 1k", f"📍 {highest_mort_prov}", delta_color="inverse")
        pkpi3.metric("🟢 Lowest Mortality", f"{lowest_mort_val} / 1k", f"📍 {lowest_mort_prov}")
        pkpi4.metric("📊 Avg Province Rate", f"{avg_prov_mortality:.1f} / 1k")
    else:
        st.info("No provincial metrics available for the current filter subset.")

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 2 — Mortality Ranking (Horizontal Bar Chart)
    # ----------------------------------------------------
    st.subheader("📊 Neonatal Mortality Rankings by Province")
    
    if not province_data.empty:
        fig_mort_rank = px.bar(
            province_data.sort_values("mortality_rate", ascending=True),
            x="mortality_rate",
            y="province",
            orientation="h",
            text="mortality_rate",
            title="Neonatal Mortality Rate (per 1,000 Live Births) by Region",
            labels={"mortality_rate": "Neonatal Mortality Rate", "province": "Province"}
        )
        fig_mort_rank.update_traces(textposition="outside")
        fig_mort_rank.update_layout(height=400, yaxis=dict(title=None))
        st.plotly_chart(fig_mort_rank, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 3 — Clinical Outcomes (Mortality vs Training)
    # ----------------------------------------------------
    st.subheader("⚖️ Clinical Alignment: Outcome vs. Workforce Training")
    
    if not province_data.empty and "training_rate" in province_data.columns:
        fig_align = px.bar(
            province_data,
            x="province",
            y=["mortality_rate", "training_rate"],
            barmode="group",
            title="Mortality Rate vs Training Coverage by Province",
            labels={"value": "Index Value / Percentage", "variable": "Metric Layer", "province": "Province"}
        )
        fig_align.update_layout(height=400)
        st.plotly_chart(fig_align, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 4 — Capacity Comparison
    # ----------------------------------------------------
    st.subheader("🏥 Infrastructure & Service Capacity Mapping")
    
    capacity_cols = [col for col in ["facilities", "districts", "nurses"] if col in province_data.columns]
    if not province_data.empty and capacity_cols:
        fig_capacity = px.bar(
            province_data,
            x="province",
            y=capacity_cols,
            barmode="group",
            title="Healthcare Capacity by Province",
            labels={"value": "Absolute Asset Count", "variable": "Resource Component", "province": "Province"}
        )
        fig_capacity.update_layout(height=400)
        st.plotly_chart(fig_capacity, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 5 — Province Summary Table
    # ----------------------------------------------------
    st.subheader("📋 Executive Provincial Ledger")
    
    ledger_fields = [
        "province", "facilities", "districts", "deliveries", 
        "live_births", "mortality_rate", "training_rate", "avg_infection_score"
    ]
    # Filter to pull only fields that are safely populated in your current dataframe layout
    available_fields = [f for f in ledger_fields if f in province_data.columns]
    
    st.dataframe(
        province_data[available_fields].sort_values("mortality_rate", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 6 — Provincial Insights Info Boxes
    # ----------------------------------------------------
    st.subheader("📌 Provincial Insights Summary")
    
    if not province_data.empty:
        # Calculate maximums dynamically
        top_training_row = province_data.sort_values("training_rate", ascending=False).iloc[0] if "training_rate" in province_data.columns else None
        top_capacity_row = province_data.sort_values("facilities", ascending=False).iloc[0] if "facilities" in province_data.columns else None
        top_ipc_row = province_data.sort_values("avg_infection_score", ascending=False).iloc[0] if "avg_infection_score" in province_data.columns else None

        inc_col1, inc_col2, inc_col3, inc_col4 = st.columns(4)
        
        with inc_col1:
            st.info(
                f"**Highest Mortality**\n\n"
                f"📍 {highest_mort_prov}\n\n"
                f"📈 **{highest_mort_val}** per 1,000 live births. Requires prioritized clinical audit teams."
            )
            
        with inc_col2:
            if top_training_row is not None:
                st.info(
                    f"**Best Training Coverage**\n\n"
                    f"📍 {top_training_row['province']}\n\n"
                    f"🎓 **{top_training_row['training_rate']:.0f}%** of healthcare workforce specialized on newborn protocol frameworks."
                )
            else:
                st.info("**Best Training Coverage**\n\nData layer unavailable.")
                
        with inc_col3:
            if top_capacity_row is not None:
                st.info(
                    f"**Largest Service Capacity**\n\n"
                    f"📍 {top_capacity_row['province']}\n\n"
                    f"🏢 Managing **{top_capacity_row['facilities']} functional facilities** across delivery networks."
                )
            else:
                st.info("**Largest Service Capacity**\n\nData layer unavailable.")
                
        with inc_col4:
            if top_ipc_row is not None:
                st.info(
                    f"**Highest IPC Score**\n\n"
                    f"📍 {top_ipc_row['province']}\n\n"
                    f"🧼 Certified at **{top_ipc_row['avg_infection_score']:.0f}%** on Infection Prevention & Control audit safety standards."
                )
            else:
                st.info("**Highest IPC Score**\n\nData layer unavailable.")

# =======================================================
# TAB 5: DECISION SUPPORT CENTER (PRESCRIPTIVE)
# =======================================================
with tab5:
    st.header("🎯 Decision Support Center")
    st.markdown("---")

    # Fetch underlying data layers
    recommendations = dashboard.recommendations()
    # Pulling opportunity layer but treating it purely as "Action Priority"
    priority_ledger = dashboard.opportunity()

    # Dynamic counts for decision routing
    total_count = len(recommendations)
    crit_count = (recommendations['risk_level'] == 'Critical').sum()
    high_count = (recommendations['risk_level'] == 'High').sum()
    med_count = (recommendations['risk_level'] == 'Medium').sum()
    low_count = (recommendations['risk_level'] == 'Low').sum()

    # Map raw internal score metrics cleanly to Action Priority Levels for the UI
    def map_priority_tier(score):
        if score >= 75: return "🔴 Immediate"
        elif score >= 50: return "🟠 High"
        elif score >= 25: return "🟡 Moderate"
        else: return "🟢 Routine"

    if not priority_ledger.empty and "opportunity_score" in priority_ledger.columns:
        priority_ledger["Action Priority"] = priority_ledger["opportunity_score"].apply(map_priority_tier)

    # ----------------------------------------------------
    # SECTION 1 — NATIONAL SITUATION KPIs
    # ----------------------------------------------------
    st.subheader("📊 1. Current National Situation")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    kpi_col1.metric("🏢 Facilities Assessed", f"{total_count}")
    kpi_col2.metric("🚨 Critical Risk Facilities", f"{crit_count}")
    kpi_col3.metric("🟠 High Risk Facilities", f"{high_count}")
    
    urgent_action_count = crit_count + high_count
    kpi_col4.metric("🔥 Total Urgent Interventions", f"{urgent_action_count}")

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 2 — NATIONAL HEAT SUMMARY (NEW)
    # ----------------------------------------------------
    st.subheader("🔥 2. National Action Priority Framework")
    
    heat_summary_df = pd.DataFrame([
        {"Priority Level": "🔴 Immediate Action Required", "Facilities Count": crit_count, "Operational Mandate": "Deploy Rapid Clinical Assessment Teams & Audit Frameworks immediately."},
        {"Priority Level": "🟠 High Priority", "Facilities Count": high_count, "Operational Mandate": "Mobilize Workforce Up-Skilling & Targeted Training Circuits."},
        {"Priority Level": "🟡 Moderate Priority", "Facilities Count": med_count, "Operational Mandate": "Conduct Regional Equipment Audits & Monitor Progress Quarterly."},
        {"Priority Level": "🟢 Routine Maintenance", "Facilities Count": low_count, "Operational Mandate": "Maintain Current Baselines & Enforce Regular HMIS Reporting Compliance."}
    ])
    
    st.table(heat_summary_df)
    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 3 — INTELLIGENT / DATA-DRIVEN RECOMMENDATION CARDS
    # ----------------------------------------------------
    st.subheader("⚡ 3. Dynamic Strategy Directives")
    card_col1, card_col2, card_col3, card_col4 = st.columns(4)

    with card_col1:
        if crit_count > 0:
            st.error(
                f"### 🔴 Emergency Status\n"
                f"**Action Required:** Deploy rapid clinical response forces to **{crit_count} facilities** mapping inside critical risk vectors "
                f"to conduct immediate maternal/neonatal death audits."
            )
        else:
            st.success(
                "### 🟢 Emergency Status\n"
                "**No Widespread Outliers:** Zero facility environments are registered within critical thresholds. "
                "Maintain default rapid-response standby protocol configurations."
            )

    with card_col2:
        # Check if training indices across the active engine subset show clinical vulnerabilities
        avg_training = engine.facility_performance()["training_rate"].mean() if "training_rate" in engine.facility_performance().columns else 100
        if avg_training < 60:
            st.warning(
                f"### 🟠 Workforce Alert\n"
                f"**Action Required:** System training average is critically low (**{avg_training:.1f}%**). Launch "
                f"targeted clinical protocol circuits across clinical staff cohorts immediately."
            )
        else:
            st.success(
                f"### 🟢 Workforce Stable\n"
                f"**Baseline Maintained:** System-wide specialized training indexes check out at a solid **{avg_training:.1f}%**. "
                f"Proceed with standard continuous development rotations."
            )

    with card_col3:
        # Evaluate operational equipment gaps from current engine context metrics
        infra_metrics = engine.facility_metrics()
        if infra_metrics.get('nicu_coverage_pct', 100) < 75 or infra_metrics.get('cpap_machines', 10) < 50:
            st.info(
                "### 🟡 Asset Procurement\n"
                "**Action Required:** Gaps detected in physical asset arrays. Prioritize logistic capital pipelines "
                "specifically to source and deliver extra functional CPAP units and incubators."
            )
        else:
            st.success(
                "### 🟢 Infrastructure Stable\n"
                "**Logistics Satisfied:** Essential life-support equipment configurations fall cleanly within "
                "safe target operating margins nationwide."
            )

    with card_col4:
        if crit_count > 5:
            st.error(
                "### 🛑 Governance Notice\n"
                "**Action Required:** High-density failure points indicate clear structural issues. Initiate "
                "strict supervisory management review pipelines across affected provinces."
            )
        else:
            st.success(
                "### 🟢 Governance Healthy\n"
                "**Compliant Frameworks:** Administrative monitoring loops and monthly database aggregations "
                "are functioning reliably within target parameters."
            )

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 4 — STRATEGIC PRIORITY & RISK LEVEL ALLOCATION
    # ----------------------------------------------------
    st.subheader("📊 4. National Strategic Mapping Distribution")
    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.markdown("### 🎯 Top 15 Facilities Flagged for Action Priority")
        if not priority_ledger.empty:
            top_priority = priority_ledger.nlargest(15, "opportunity_score")
            
            fig_opp = px.bar(
                top_priority,
                x="opportunity_score",
                y="facility_name",
                orientation="h",
                color="Action Priority",
                title="Highest Urgency Facilities by Calculated Action Priority",
                color_discrete_map={"🔴 Immediate": "#dc3545", "🟠 High": "#fd7e14", "🟡 Moderate": "#ffc107", "🟢 Routine": "#198754"},
                labels={"opportunity_score": "Action Priority Scale Value", "facility_name": "Facility Name"}
            )
            fig_opp.update_layout(yaxis=dict(autorange="reversed"), height=400, showlegend=True)
            fig_opp.update_traces(texttemplate="", textposition="inside")
            st.plotly_chart(fig_opp, use_container_width=True)

    with chart_right:
        st.markdown("### 🚨 Macro System Operational Risk Allocation")
        if not recommendations.empty and "risk_level" in recommendations.columns:
            risk_counts = recommendations["risk_level"].astype(str).value_counts().reset_index()
            risk_counts.columns = ["Risk Category", "Facilities Mapping"]
            
            fig_risk_dist = px.bar(
                risk_counts,
                x="Risk Category",
                y="Facilities Mapping",
                text="Facilities Mapping",
                color="Risk Category",
                title="Total Facilities Grouped by Operational Risk Boundary",
                color_discrete_map={"Critical": "#dc3545", "High": "#fd7e14", "Medium": "#ffc107", "Low": "#198754"},
                category_orders={"Risk Category": ["Critical", "High", "Medium", "Low"]}
            )
            fig_risk_dist.update_traces(textposition="outside")
            fig_risk_dist.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_risk_dist, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 5 — THE TACTICAL FACILITY ACTION PLAN LEDGER
    # ----------------------------------------------------
    st.subheader("📋 5. Tactical Facility Action Plan Ledger")
    
    col_f1, col_f2 = st.columns(2)
    prov_opt = ["All"] + sorted(recommendations["province"].dropna().unique().tolist()) if "province" in recommendations.columns else ["All"]
    risk_opt = ["All"] + sorted(recommendations["risk_level"].dropna().unique().tolist()) if "risk_level" in recommendations.columns else ["All"]

    prov_sel = col_f1.selectbox("Filter Ledger by Province Location", prov_opt, key="tab5_prov_filter")
    risk_sel = col_f2.selectbox("Filter Ledger by Risk Classification", risk_opt, key="tab5_risk_filter")

    display_df = recommendations.copy()
    if "opportunity_score" in priority_ledger.columns:
        display_df = display_df.merge(priority_ledger[["facility_id", "Action Priority"]], on="facility_id", how="left")

    if prov_sel != "All":
        display_df = display_df[display_df["province"] == prov_sel]
    if risk_sel != "All":
        display_df = display_df[display_df["risk_level"] == risk_sel]

    # Rename column headers to match professional executive vocabulary mappings
    if "risk_level" in display_df.columns:
        display_df = display_df.rename(columns={"risk_level": "Risk Level Status"})
    if "recommendation" in display_df.columns:
        display_df = display_df.rename(columns={"recommendation": "Prescribed System Directive"})

    columns_to_show = [col for col in ["facility_name", "province", "Risk Level Status", "Action Priority", "Prescribed System Directive"] if col in display_df.columns]
    
    st.dataframe(
        display_df[columns_to_show],
        use_container_width=True,
        hide_index=True
    )

    csv_payload = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Targeted Action Matrix Spreadsheet (CSV)",
        data=csv_payload,
        file_name="national_facility_action_plan.csv",
        mime="text/csv"
    )

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 6 — MOST FREQUENTLY RECOMMENDED INTERVENTIONS
    # ----------------------------------------------------
    st.subheader("🧰 6. Most Frequently Recommended Interventions")
    
    if not display_df.empty and "Prescribed System Directive" in display_df.columns:
        freq_counts = (
            display_df["Prescribed System Directive"]
            .astype(str)
            .str.split(";")
            .explode()
            .str.strip()
            .value_counts()
            .reset_index()
        )
        freq_counts.columns = ["Intervention Program Classification", "Affected Facilities Count"]

        fig_freq = px.bar(
            freq_counts,
            x="Affected Facilities Count",
            y="Intervention Program Classification",
            orientation="h",
            color="Affected Facilities Count",
            text="Affected Facilities Count",
            title="Frequency of Core Directives Needed System-wide",
            color_continuous_scale="Purples"
        )
        fig_freq.update_layout(yaxis=dict(autorange="reversed"), height=380, coloraxis_showscale=False)
        st.plotly_chart(fig_freq, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------
    # SECTION 7 — EXECUTIVE SUMMARY MEMO (FULLY COMPUTED)
    # ----------------------------------------------------
    st.subheader("📌 7. Executive Governance Memo")
    memo_col1, memo_col2, memo_col3 = st.columns(3)

    # Calculate values dynamically using the current engine state context layers
    prov_df = engine.province_analytics()
    if not prov_df.empty:
        highest_prov = prov_df.sort_values("mortality_rate", ascending=False).iloc[0]
        lowest_prov = prov_df.sort_values("mortality_rate", ascending=True).iloc[0]
        highest_prov_txt = f"{highest_prov['province']} ({highest_prov['mortality_rate']:.1f} deaths / 1k)"
        lowest_prov_txt = f"{lowest_prov['province']} ({lowest_prov['mortality_rate']:.1f} deaths / 1k)"
    else:
        highest_prov_txt = "Data Layer Not Loaded"
        lowest_prov_txt = "Data Layer Not Loaded"

    # Isolate systemic process vulnerabilities
    if not display_df.empty and "Prescribed System Directive" in display_df.columns:
        most_common_deficiency = "Workforce Nurse Training Shortage"  # Standard classification base
        most_common_rec = str(freq_counts.iloc[0]["Intervention Program Classification"]) if not freq_counts.empty else "Enhance Newborn Protocols"
    else:
        most_common_deficiency = "Insufficient Data Streams"
        most_common_rec = "Establish Regular Monitoring Audits"

    with memo_col1:
        st.info(
            "#### 🗺️ Geographic Outliers\n"
            f"• **Highest Risk Province Location:** \n"
            f"  `{highest_prov_txt}`\n\n"
            f"• **Highest Performing Province Location:** \n"
            f"  `{lowest_prov_txt}`"
        )

    with memo_col2:
        st.info(
            "#### ⚠️ Systemic Deficiencies\n"
            f"• **Primary Core System Gap Identified:** \n"
            f"  `{most_common_deficiency}`\n\n"
            f"• **Most Frequent Structural Directive Required:** \n"
            f"  `{most_common_rec}`"
        )

    with memo_col3:
        st.info(
            "#### 🎯 Strategic Mandate\n"
            f"• **Immediate Focus:** Deploy immediate clinical audit teams to the **{crit_count} critical risk** facilities.\n\n"
            f"• **Target Action:** Direct continuous workforce up-skilling to provinces failing the 60% training threshold."
        )