import pandas as pd


class RecommendationEngine:
    """
    Generates actionable recommendations for
    every health facility.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def generate(self) -> pd.DataFrame:
        """
        Generate actionable recommendations for each facility.
        """

        recommendations = []

        for _, row in self.df.iterrows():

            rec = []

            # ------------------------------------------------
            # Mortality
            # ------------------------------------------------
            if row["mortality_rate"] > 40:
                rec.append(
                    "Strengthen neonatal emergency care."
                )

            # ------------------------------------------------
            # NICU
            # ------------------------------------------------
            if row["nicu_score"] < 0.5:
                rec.append(
                    "Expand NICU availability."
                )

            # ------------------------------------------------
            # Electricity
            # ------------------------------------------------
            if row["electricity_score"] < 1:
                rec.append(
                    "Improve electricity reliability."
                )

            # ------------------------------------------------
            # Generator
            # ------------------------------------------------
            if row["generator_score"] == 0:
                rec.append(
                    "Install backup generator."
                )

            # ------------------------------------------------
            # Infection Prevention
            # ------------------------------------------------
            if row["infection_prevention_score"] < 60:
                rec.append(
                    "Improve infection prevention measures."
                )

            # ------------------------------------------------
            # Workforce Training
            # ------------------------------------------------
            if row["training_rate"] < 20:
                rec.append(
                    "Conduct neonatal staff training."
                )

            # ------------------------------------------------
            # HMIS
            # ------------------------------------------------
            if row["hmis_reporting_completeness"] < 80:
                rec.append(
                    "Improve HMIS reporting quality."
                )

            # ------------------------------------------------
            # Default
            # ------------------------------------------------
            if not rec:
                rec.append(
                    "Maintain current performance."
                )

            recommendations.append("; ".join(rec))

        df = self.df.copy()

        df["recommendation"] = recommendations

        # Keep ranking if already present
        if "rank" not in df.columns:
            df = df.sort_values(
                "risk_score",
                ascending=False
            ).reset_index(drop=True)

            df.insert(
                0,
                "rank",
                df.index + 1
            )

        return df[
            [
                "rank",
                "facility_name",
                "facility_id",
                "province",
                "district",
                "performance_score",
                "risk_score",
                "risk_level",
                "recommendation"
            ]
        ]