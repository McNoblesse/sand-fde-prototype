from typing import Dict

import pandas as pd


class HealthAnalyticsEngine:
    """
    Computes analytics for the Neonatal Health
    Decision Support Platform.
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
            self.clinical["neonatal_deaths_0_7d"]+
            self.clinical["neonatal_deaths_8_28d"]).sum()

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

    def clinical_metrics(self):
        births = self.clinical["live_births"].sum()
        deaths = (
            self.clinical["neonatal_deaths_0_7d"] +
            self.clinical["neonatal_deaths_8_28d"]).sum()

        deliveries = self.clinical["total_deliveries"].sum()
        premature = (
            self.clinical["preterm_births_28_32w"] + 
            self.clinical["preterm_births_32_37w"]).sum()

        return {
            "neonatal_mortality_rate":
                float(round(deaths / births * 1000, 2)),

            "stillbirth_rate":
                float(round(self.clinical["stillbirths"].sum() / deliveries * 100, 2)),

            "prematurity_rate":
                float(round(premature / deliveries * 100, 2)),

            "low_birth_weight_rate":
                float(round(self.clinical["birth_weight_less_2500g"].sum() / deliveries * 100, 2)),

            "low_apgar_rate":
                float(round(self.clinical["apgar_less_7_at_5min"].sum() / deliveries * 100, 2))
        }

    # ==========================================================
    # Facility Metrics
    # ==========================================================

    def facility_metrics(self):
        total = len(self.facility)
        
        nicu = self._score_partial(self.facility["nicu_available"])
        electricity = self._score_partial(self.facility["electricity_reliable"])
        generator = self._score_partial(self.facility["backup_generator"])
        kangaroo = self._score_partial(self.facility["kangaroo_care_space"])

        return {
            "nicu_coverage_pct": float(round(nicu.mean() * 100, 2)),
            "electricity_reliability_pct": float(round(electricity.mean() * 100, 2)),
            "backup_generator_pct": float(round(generator.mean() * 100, 2)),
            "kangaroo_space_pct": float(round(kangaroo.mean() * 100, 2)),
            "total_nicu_beds":int(self.facility["nicu_beds"].sum()),
            "functional_incubators":int(self.facility["incubators_functional"].sum()),
            "cpap_machines":int(self.facility["cpap_machines"].sum())
        }

    # ==========================================================
    # Workforce Metrics
    # ==========================================================

    def workforce_metrics(self):
        trained_pct = (self.facility["neonatal_trained_nurses"].sum()/
                      self.facility["total_nurses"].sum()* 100)
        shift = self._score_shift(self.facility["night_shift_coverage"])

        return {
            "total_nurses": int(self.facility["total_nurses"].sum()),
            "trained_neonatal_nurses": int(self.facility["neonatal_trained_nurses"].sum()),
            "training_coverage_pct": float(round(trained_pct,2)),
            "midwives": int(self.facility["midwives"].sum()),
            "pediatricians": int(self.facility["pediatricians"].sum()),
            "neonatologists":int(self.facility["neonatologists"].sum()),
            "night_shift_coverage_pct": float(round(shift.mean() * 100, 2))
        }

    # ==========================================================
    # Governance Metrics
    # ==========================================================

    def governance_metrics(self):
        total = len(self.facility)

        protocol = self._score_partial(self.facility["newborn_protocol_exists"])

        return {
            "quality_improvement_pct":float(round(self.facility["quality_improvement_active"].mean() * 100,2)),
            "protocol_availability_pct":float(round(protocol.mean() * 100,2)),
            "average_hmis_reporting":float(round(self.facility["hmis_reporting_completeness"].mean(),2)),
            "average_protocol_training":float(round(self.facility["staff_trained_on_protocol_pct"].mean(),2)),
            "average_death_audit":float(round(self.facility["death_audits_conducted_pct"].mean(),2)),
            "infection_prevention_score":float(round(self.facility["infection_prevention_score"].mean(),2))
        }

    # ==========================================================
    # Province Analytics
    # ==========================================================

    def province_analytics(self) -> pd.DataFrame:
        """
        Province-level summary used for executive dashboards.
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
                avg_infection_score=("infection_prevention_score","mean")
            )
            .reset_index()
        )
        province["neonatal_deaths"] = (
            province["neonatal_deaths_0_7"] +
            province["neonatal_deaths_8_28"]
        )
        province["mortality_rate"] = (
            province["neonatal_deaths"] / province["live_births"] * 1000).round(2)
        province["training_rate"] = (
            province["trained_nurses"] / province["nurses"] * 100).round(2)
       
        return province.sort_values("mortality_rate",ascending=False)

    # ==========================================================
    # Facility Performance Ranking
    # ==========================================================

    def facility_performance(self) -> pd.DataFrame:
        """
        Computes an overall Facility Performance Index for each facility.
        """
        # ------------------------------------------------------
        # Aggregate clinical data
        # ------------------------------------------------------
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
            df["neonatal_deaths"] /
            df["live_births"].replace(0, pd.NA)
        ) * 1000

        # ------------------------------------------------------
        # Merge facility information
        # ------------------------------------------------------
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

        # ------------------------------------------------------
        # Infrastructure Scores
        # ------------------------------------------------------
        df["nicu_score"] = self._score_partial(df["nicu_available"])
        df["electricity_score"] = self._score_partial(df["electricity_reliable"])
        df["generator_score"] = self._score_partial(df["backup_generator"])
        df["infrastructure_score"] = (
            (df["nicu_score"] + df["electricity_score"] + df["generator_score"]) / 3) * 100

        # ------------------------------------------------------
        # Workforce Score
        # ------------------------------------------------------
        df["training_rate"] = (
            df["neonatal_trained_nurses"] /
            df["total_nurses"].replace(0, pd.NA)
        ) * 100

        df["training_rate"] = df["training_rate"].fillna(0).clip(0, 100)

        # ------------------------------------------------------
        # Mortality Score
        # Lower mortality = Higher score
        # ------------------------------------------------------
        max_rate = df["mortality_rate"].max()
        df["mortality_score"] = (
            100 - (df["mortality_rate"] / max_rate) * 100
        ).clip(0, 100)

        # ------------------------------------------------------
        # Composite Facility Performance Index
        # ------------------------------------------------------
        df["performance_score"] = (
            df["mortality_score"] * 0.35 +
            df["infection_prevention_score"] * 0.20 +
            df["hmis_reporting_completeness"] * 0.15 +
            df["training_rate"] * 0.15 +
            df["infrastructure_score"] * 0.15
        ).round(2)

        # ------------------------------------------------------
        # Facility Grade
        # ------------------------------------------------------
        df["performance_grade"] = pd.cut(
            df["performance_score"],
            bins=[0, 45, 65, 80, 100],
            labels=[
                "Needs Improvement",
                "Fair",
                "Good",
                "Excellent"
            ],
            include_lowest=True
        )

        df["status"] = df["performance_grade"].map({
            "Excellent": "🟢",
            "Good": "🟢",
            "Fair": "🟡",
            "Needs Improvement": "🔴"
        })

        # ------------------------------------------------------
        # Round display columns
        # ------------------------------------------------------
        df["mortality_rate"] = df["mortality_rate"].round(2)
        df["training_rate"] = df["training_rate"].round(2)

        # ------------------------------------------------------
        # Ranking
        # ------------------------------------------------------
        df = df.sort_values("performance_score",ascending=False).reset_index(drop=True)
        df.insert(0,"rank",range(1, len(df) + 1))

        # ------------------------------------------------------
        # Final Output
        # ------------------------------------------------------
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