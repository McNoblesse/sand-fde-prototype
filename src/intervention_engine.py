import pandas as pd


class InterventionEngine:
    """
    Identifies facilities where investments
    will have the greatest impact.
    """

    def __init__(self, risk_df: pd.DataFrame):
        self.df = risk_df.copy()

    # ==========================================================
    # Opportunity Index
    # ==========================================================

    def opportunity_index(self) -> pd.DataFrame:

        df = self.df.copy()

        #remove previous ranks if it exists
        df = df.drop(columns=["rank"], errors="ignore")

        df["opportunity_score"] = (
            (100 - df["performance_score"]) * 0.60 +
            (100 - df["risk_score"]) * 0.40
        ).round(2)

        df["opportunity_level"] = pd.cut(
            df["opportunity_score"],
            bins=[0, 40, 60, 80, 100],
            labels=[
                "Low",
                "Medium",
                "High",
                "Very High"
            ],
            include_lowest=True
        )

        df = df.sort_values(
            "opportunity_score",
            ascending=False
        ).reset_index(drop=True)

        df["rank"] = range(1, len(df) + 1)

        return df[
            [
                "rank",
                "facility_name",
                "facility_id",
                "province",
                "district",
                "performance_score",
                "risk_score",
                "opportunity_score",
                "opportunity_level"
            ]
        ]