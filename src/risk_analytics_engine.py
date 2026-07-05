from typing import Dict

import pandas as pd


class RiskAnalyticsEngine:
    """
    Identifies high-risk health facilities by combining
    clinical outcomes, workforce capacity, infrastructure,
    and governance indicators.
    """
    def __init__(
        self,
        facility_performance: pd.DataFrame
    ) -> None:
        self.df = facility_performance.copy()

    # ======================================================
    # Risk Score
    # ======================================================
    def calculate_risk_score(self) -> pd.DataFrame:
        """
        Higher score = higher operational risk.
        """
        df = self.df.copy()
        df["risk_score"] = (
            (100 - df["performance_score"]) * 0.60 + df["mortality_rate"] * 0.40).round(2)
        
        self.df = df

        return self.df

    # ======================================================
    # Risk Classification
    # ======================================================

    def classify_risk(self) -> pd.DataFrame:
        """
        Classify facilities into operational risk levels.
        """
        df = self.calculate_risk_score().copy()
        df["risk_level"] = pd.cut(
            df["risk_score"],
            bins=[0, 30, 50, 70, 200],
            labels=[
                "Low",
                "Moderate",
                "High",
                "Critical"
            ],
            include_lowest=True
        )
        
        self.df = df

        return self.df