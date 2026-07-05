from health_analytics_engine import HealthAnalyticsEngine
from risk_analytics_engine import RiskAnalyticsEngine
from intervention_engine import InterventionEngine
from recommendation_engine import RecommendationEngine


class DashboardEngine:
    """
    Central dashboard service that prepares all analytics
    once and exposes them to the Streamlit application.
    """

    def __init__(self, clinical, facility):

        # --------------------------------------------------
        # Base Analytics Engine
        # --------------------------------------------------
        self.health = HealthAnalyticsEngine(clinical, facility)

        # --------------------------------------------------
        # Compute once and reuse
        # --------------------------------------------------
        self._performance = self.health.facility_performance()

        self._risk = RiskAnalyticsEngine(
            self._performance
        ).classify_risk()

        self._opportunity = InterventionEngine(
            self._risk
        ).opportunity_index()

        self._recommendations = RecommendationEngine(
            self._risk
        ).generate()

    # ======================================================
    # Executive Dashboard
    # ======================================================

    def executive(self):
        return self.health.executive_summary()

    # ======================================================
    # Clinical Analytics
    # ======================================================

    def clinical(self):
        return self.health.clinical_metrics()

    # ======================================================
    # Facility Analytics
    # ======================================================

    def facility(self):
        return self.health.facility_metrics()

    # ======================================================
    # Workforce Analytics
    # ======================================================

    def workforce(self):
        return self.health.workforce_metrics()

    # ======================================================
    # Governance Analytics
    # ======================================================

    def governance(self):
        return self.health.governance_metrics()

    # ======================================================
    # Facility Performance
    # ======================================================

    def performance(self):
        return self._performance

    # ======================================================
    # Risk Analytics
    # ======================================================

    def risk(self):
        return self._risk

    # ======================================================
    # Opportunity Index
    # ======================================================

    def opportunity(self):
        return self._opportunity

    # ======================================================
    # Recommendations
    # ======================================================

    def recommendations(self):
        return self._recommendations