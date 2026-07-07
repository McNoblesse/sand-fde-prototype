from typing import Dict
import pandas as pd


class HealthAnalyticsEngine:
    """
    Computes analytics for the Neonatal Health Decision Support Platform.
    Fully optimized for clean, whole-number quarterly bulletin tracking.
    """
    def __init__(self, clinical: pd.DataFrame, facility_master: pd.DataFrame) -> None:
        self.clinical = clinical
        self.facility = facility_master

    def _score_partial(self, series):
        mapping = {
            True: 1, False: 0, "True": 1, "False": 0, "Partial": 0.5, "Outdated": 0.5
        }
        return (series.map(mapping).fillna(0).astype(float))

    def _score_shift(self, series: pd.Series) -> pd.Series:
        """
        Converts shift coverage into numeric scores.
        """
        mapping = {"Full": 1, "Partial": 0.5, "None": 0}
        return (series.map(mapping).fillna(0).astype(float))

    # ==========================================================
    # Executive Summary
    # ==========================================================

    def executive_summary(self) -> Dict:
        deaths = (
            self.clinical["neonatal_deaths_0_7d"] +
            self.clinical["neonatal_deaths_8_28d"]
        ).sum()

        return {
            "total_facilities": self.facility["facility_id"].nunique(),
            "total_districts": self.facility["district"].nunique(),
            "total_provinces": self.facility["province"].nunique(),
            "total_deliveries": int(self.clinical["total_deliveries"].sum()),
            "live_births": int(self.clinical["live_births"].sum()),
            "neonatal_deaths": int(deaths),
            "stillbirths": int(self.clinical["stillbirths"].sum()),
        }

    # ==========================================================
    # Clinical Indicators
    # ==========================================================

    def clinical_metrics(self) -> Dict:
        """
        Computes clinical indicators scaled consistently per 1,000 outputs,
        fully normalized to whole numbers for senior leadership scannability.
        """
        births = self.clinical["live_births"].sum()
        deaths = (
            self.clinical["neonatal_deaths_0_7d"] +
            self.clinical["neonatal_deaths_8_28d"]
        ).sum()

        deliveries = self.clinical["total_deliveries"].sum()

        return {
            "neonatal_mortality_rate": 
                int(round(deaths / births * 1000 if births > 0 else 0)),

            "stillbirth_rate": 
                int(round(self.clinical["stillbirths"].sum() / deliveries * 1000 if deliveries > 0 else 0)),

            "low_birth_weight_rate": 
                int(round(self.clinical["birth_weight_less_2500g"].sum() / deliveries * 1000 if deliveries > 0 else 0)),

            "total_live_births": 
                int(births)
        }

    # ==========================================================
    # Facility Metrics
    # ==========================================================

    def facility_metrics(self) -> Dict:
        nicu = self._score_partial(self.facility["nicu_available"])
        electricity = self._score_partial(self.facility["electricity_reliable"])
        generator = self._score_partial(self.facility["backup_generator"])
        kangaroo = self._score_partial(self.facility["kangaroo_care_space"])

        return {
            "nicu_coverage_pct": int(round(nicu.mean() * 100)),
            "electricity_reliability_pct": int(round(electricity.mean() * 100)),
            "backup_generator_pct": int(round(generator.mean() * 100)),
            "kangaroo_space_pct": int(round(kangaroo.mean() * 100)),
            "total_nicu_beds": int(self.facility["nicu_beds"].sum()),
            "functional_incubators": int(self.facility["incubators_functional"].sum()),
            "cpap_machines": int(self.facility["cpap_machines"].sum())
        }

    # ==========================================================
    # Workforce Metrics
    # ==========================================================

    def workforce_metrics(self) -> Dict:
        total_nurses = self.facility["total_nurses"].sum()
        trained_nurses = self.facility["neonatal_trained_nurses"].sum()
        
        trained_pct = (trained_nurses / total_nurses * 100) if total_nurses > 0 else 0
        shift = self._score_shift(self.facility["night_shift_coverage"])

        return {
            "total_nurses": int(total_nurses),
            "trained_neonatal_nurses": int(trained_nurses),
            "training_coverage_pct": int(round(trained_pct)),
            "midwives": int(self.facility["midwives"].sum()),
            "pediatricians": int(self.facility["pediatricians"].sum()),
            "neonatologists": int(self.facility["neonatologists"].sum()),
            "night_shift_coverage_pct": int(round(shift.mean() * 100))
        }

    # ==========================================================
    # Governance Metrics
    # ==========================================================

    def governance_metrics(self) -> Dict:
        protocol = self._score_partial(self.facility["newborn_protocol_exists"])

        return {
            "quality_improvement_pct": int(round(self.facility["quality_improvement_active"].mean() * 100)),
            "protocol_availability_pct": int(round(protocol.mean() * 100)),
            "average_hmis_reporting": int(round(self.facility["hmis_reporting_completeness"].mean())),
            "average_protocol_training": int(round(self.facility["staff_trained_on_protocol_pct"].mean())),
            "average_death_audit": int(round(self.facility["death_audits_conducted_pct"].mean())),
            "infection_prevention_score": int(round(self.facility["infection_prevention_score"].mean()))
        }

    # ==========================================================
    # Province Analytics
    # ==========================================================

    def province_analytics(self) -> pd.DataFrame:
        """
        Province-level summary engineered for whole-number bulletin metrics.
        """
        df = self.clinical.merge(
            self.facility[
                [
                    "facility_id",
                    "province",
                    "district",
                    "nicu_available",
                    "total_nurses",
                    "neonatal_trained_nurses",
                    "infection_prevention_score"
                ]
            ],
            on="facility_id",
            how="left"
        )
        province = (
            df.groupby("province")
            .agg(
                facilities=("facility_id", "nunique"),
                districts=("district", "nunique"),
                deliveries=("total_deliveries", "sum"),
                live_births=("live_births", "sum"),
                neonatal_deaths_0_7=("neonatal_deaths_0_7d", "sum"),
                neonatal_deaths_8_28=("neonatal_deaths_8_28d", "sum"),
                nurses=("total_nurses", "sum"),
                trained_nurses=("neonatal_trained_nurses", "sum"),
                avg_infection_score=("infection_prevention_score", "mean")
            )
            .reset_index()
        )
        province["neonatal_deaths"] = (
            province["neonatal_deaths_0_7"] +
            province["neonatal_deaths_8_28"]
        )
        
        province["mortality_rate"] = (
            (province["neonatal_deaths"] / province["live_births"] * 1000)
            .fillna(0)
            .round(0)
            .astype(int)
        )
        province["training_rate"] = (
            (province["trained_nurses"] / province["nurses"] * 100)
            .fillna(0)
            .round(0)
            .astype(int)
        )
       
        return province.sort_values("mortality_rate", ascending=False)

    # ==========================================================
    # Quarterly Clinical Analytics
    # ==========================================================

    def quarterly_clinical_summary(self) -> pd.DataFrame:
        """
        Quarterly neonatal indicators for the national bulletin.
        Sorted chronologically to support sequential line/bar trends.
        """
        quarterly = (
            self.clinical
            .groupby("quarter_year")
            .agg(
                deliveries=("total_deliveries", "sum"),  # Exposed clearly for chart use
                live_births=("live_births", "sum"),
                neonatal_deaths_0_7=("neonatal_deaths_0_7d", "sum"),
                neonatal_deaths_8_28=("neonatal_deaths_8_28d", "sum"),
                stillbirths=("stillbirths", "sum"),
                low_birth_weight=("birth_weight_less_2500g", "sum")
            )
            .reset_index()
        )

        quarterly["neonatal_deaths"] = (
            quarterly["neonatal_deaths_0_7"] +
            quarterly["neonatal_deaths_8_28"]
        )

        quarterly["neonatal_mortality_rate"] = (
            quarterly["neonatal_deaths"] /
            quarterly["live_births"] * 1000
        ).fillna(0).round().astype(int)

        quarterly["stillbirth_rate"] = (
            quarterly["stillbirths"] /
            quarterly["deliveries"] * 1000
        ).fillna(0).round().astype(int)

        quarterly["low_birth_weight_rate"] = (
            quarterly["low_birth_weight"] /
            quarterly["deliveries"] * 1000
        ).fillna(0).round().astype(int)

        # Recommendation 1: Chronological sorting block execution
        quarterly = quarterly.sort_values("quarter_year").reset_index(drop=True)

        return quarterly

    # ==========================================================
    # Facility Performance Ranking
    # ==========================================================

    def facility_performance(self) -> pd.DataFrame:
        """
        Computes an overall Facility Performance Index for each facility.
        Outputs are fully cast to clean whole-number categories.
        """
        # Aggregate clinical data
        df = (
            self.clinical
            .groupby("facility_id")
            .agg(
                deliveries=("total_deliveries", "sum"),
                live_births=("live_births", "sum"),
                deaths_0_7=("neonatal_deaths_0_7d", "sum"),
                deaths_8_28=("neonatal_deaths_8_28d", "sum"),
                stillbirths=("stillbirths", "sum")
            )
            .reset_index()
        )
        df["neonatal_deaths"] = (
            df["deaths_0_7"] +
            df["deaths_8_28"]
        )
        
        df["mortality_rate"] = (
            (df["neonatal_deaths"] / df["live_births"].replace(0, pd.NA)) * 1000
        ).fillna(0).round().astype(int)

        # Merge facility configuration parameters
        df = df.merge(
            self.facility[
                [
                    "facility_id",
                    "facility_name",
                    "province",
                    "district",
                    "nicu_available",
                    "electricity_reliable",
                    "backup_generator",
                    "total_nurses",
                    "neonatal_trained_nurses",
                    "infection_prevention_score",
                    "hmis_reporting_completeness"
                ]
            ],
            on="facility_id",
            how="left"
        )

        # Infrastructure Scores
        df["nicu_score"] = self._score_partial(df["nicu_available"])
        df["electricity_score"] = self._score_partial(df["electricity_reliable"])
        df["generator_score"] = self._score_partial(df["backup_generator"])
        df["infrastructure_score"] = (
            ((df["nicu_score"] + df["electricity_score"] + df["generator_score"]) / 3) * 100
        ).round().astype(int)

        # Workforce Score
        df["training_rate"] = (
            (df["neonatal_trained_nurses"] / df["total_nurses"].replace(0, pd.NA)) * 100
        ).fillna(0).round().astype(int)

        # Mortality Score Calculation
        max_rate = df["mortality_rate"].max()
        if pd.isna(max_rate) or max_rate == 0:
            df["mortality_score"] = 100
        else:
            df["mortality_score"] = (100 - (df["mortality_rate"] / max_rate) * 100).clip(0, 100)
        df["mortality_score"] = df["mortality_score"].round().astype(int)

        # Composite Framework Index Generation
        df["performance_score"] = (
            df["mortality_score"] * 0.35 +
            df["infection_prevention_score"] * 0.20 +
            df["hmis_reporting_completeness"] * 0.15 +
            df["training_rate"] * 0.15 +
            df["infrastructure_score"] * 0.15
        ).round().astype(int)

        # Facility Grade Category
        df["performance_grade"] = pd.cut(
            df["performance_score"],
            bins=[0, 45, 65, 80, 100],
            labels=["Needs Improvement", "Fair", "Good", "Excellent"],
            include_lowest=True
        )

        df["status"] = df["performance_grade"].map({
            "Excellent": "🟢",
            "Good": "🟡",
            "Fair": "🟠",
            "Needs Improvement": "🔴"
        })

        # Final Rank sorting
        df = df.sort_values("performance_score", ascending=False).reset_index(drop=True)
        df.insert(0, "rank", range(1, len(df) + 1))

        return df[
            [
                "rank",
                "facility_name",
                "facility_id",
                "province",
                "district",
                "mortality_rate",
                "training_rate",
                "infection_prevention_score",
                "hmis_reporting_completeness",
                "nicu_score",
                "electricity_score",
                "generator_score",
                "performance_score",
                "performance_grade",
                "status"
            ]
        ]

    # ==========================================================
    # Extreme Performance Threshold Splitters
    # ==========================================================

    def top_10_facilities(self) -> pd.DataFrame:
        """
        Recommendation 3: Returns the 10 highest-performing facilities.
        """
        return (
            self.facility_performance()
            .sort_values("performance_score", ascending=False)
            .head(10)
        )

    def bottom_10_facilities(self) -> pd.DataFrame:
        """
        Returns the 10 lowest-performing facilities.
        """
        return (
            self.facility_performance()
            .sort_values("performance_score", ascending=True)
            .head(10)
        )