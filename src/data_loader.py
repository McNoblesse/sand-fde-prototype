from pathlib import Path
from typing import Dict, Any

import pandas as pd


class DataLoader:
    """
    ETL pipeline for the Neonatal Health Analytics Platform.

    Responsibilities
    ----------------
    1. Load raw datasets
    2. Validate source datasets
    3. Clean and standardize values
    4. Build a Facility Master table
    5. Return structured datasets for analytics
    """
    def __init__(self, data_folder: str = "data") -> None:

        self.data_folder = Path(data_folder)

        # Raw datasets
        self.clinical = None
        self.facilities = None
        self.operations = None
        self.workers = None
        self.governance = None

        # Integrated datasets
        self.facility_master = None

        # Data quality report
        self.quality_report = {}

    # ==========================================================
    # Generic CSV Loader
    # ==========================================================

    def _load_csv(self, filename: str) -> pd.DataFrame:
        """
        Load a CSV file from the data directory.
        """
        filepath = self.data_folder / filename

        if not filepath.exists():

            raise FileNotFoundError(

                f"Cannot find {filename} inside {self.data_folder}"

            )
        df = pd.read_csv(filepath)

        print(f"Loaded {filename}: {len(df)} rows")

        return df

    # ==========================================================
    # Load Raw Datasets
    # ==========================================================

    def load_datasets(self) -> None:
        """
        Load all datasets required for analysis.
        """

        self.clinical = self._load_csv("clinical_neonatal.csv")

        self.facilities = self._load_csv("facilities.csv")

        self.operations = self._load_csv("operations.csv")

        self.workers = self._load_csv("healthcare_workers.csv")

        self.governance = self._load_csv("governance.csv")

    # ==========================================================
    # Standardize Text Fields
    # ==========================================================

    def clean_text(self) -> None:
        """
        Remove unnecessary whitespace from text columns.
        """
        datasets = [self.clinical,self.facilities,self.operations,self.workers,self.governance]

        for df in datasets:
            for column in df.columns:
                if df[column].dtype == object:
                    df[column] = (df[column].astype(str).str.strip())

    # ==========================================================
    # Clean Percentage Columns
    # ==========================================================

    def clean_percentages(self) -> None:
        """
        Convert percentage strings (e.g. '85%')
        into numeric values.
        """
        datasets = [self.operations,self.governance]

        for df in datasets:
            for column in df.columns:
                if df[column].dtype == object:
                    sample = df[column].dropna().astype(str)

                    if sample.str.contains("%").any():
                        df[column] = (df[column].astype(str).str.replace("%", "", regex=False))
                        df[column] = pd.to_numeric(df[column],errors="coerce")

    # ==========================================================
    # Clean Boolean Columns
    # ==========================================================

    def clean_booleans(self) -> None:
        """
        Convert Yes/No values into True/False.
        """
        mapping = {
            "Yes": True,
            "No": False,

            "YES": True,
            "NO": False,

            "True": True,
            "False": False,

            "TRUE": True,
            "FALSE": False,

            "Y": True,
            "N": False,

            "1": True,
            "0": False
        }

        datasets = [self.facilities,self.operations,self.governance]

        for df in datasets:
            object_columns = df.select_dtypes(include="object").columns

            for column in object_columns:
                df[column] = df[column].apply(lambda x: mapping.get(x, x))

    # ==========================================================
    # Parse Date Columns
    # ==========================================================

    def parse_dates(self) -> None:
        """
        Convert date columns to datetime.
        """
        self.workers["last_neonatal_training_date"] = (pd.to_datetime(self.workers["last_neonatal_training_date"],errors="coerce"))

    # ==========================================================
    # Clean Numeric Columns
    # ==========================================================

    def clean_numeric_columns(self) -> None:
        """
        Convert known numeric columns into numeric dtype.
        """
        numeric_columns = ["nicu_beds","incubators_functional","incubators_total","radiant_warmers","phototherapy_units","cpap_machines",
                            "resuscitation_tables","oxygen_cylinders_available","oxygen_concentrators","avg_referral_time_hrs","referrals_out_monthly",
                            "referrals_in_monthly","essential_drugs_stockouts_days","total_nurses","neonatal_trained_nurses","midwives",
                            "obstetricians","pediatricians","neonatologists","anesthetists","staff_per_delivery_2024"]

        datasets = [self.facilities,self.operations,self.workers]

        for df in datasets:
            for column in numeric_columns:

                if column in df.columns:
                    df[column] = pd.to_numeric(df[column],errors="coerce")

    # ==========================================================
    # Normalize Reporting Month
    # ==========================================================

    def normalize_reporting_month(self) -> None:
        """
        Standardize reporting month format.
        """
        self.clinical["reporting_month"] = pd.to_datetime(self.clinical["reporting_month"])

    # ==========================================================
    # Dataset Validation
    # ==========================================================

    def validate_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        primary_key: str
    ) -> Dict[str, Any]:
        """
        Validate an individual dataset.
        """
        report = {}
        report["rows"] = len(df)
        report["columns"] = len(df.columns)
        report["missing_values"] = df.isna().sum().to_dict()
        report["missing_rows"] = int(df.isna().any(axis=1).sum())
        if dataset_name != "clinical":
            report["duplicate_keys"] = int(df.duplicated(subset=[primary_key]).sum())
        report["duplicate_rows"] = int(df.duplicated().sum())
        report["unique_facilities"] = df[primary_key].nunique() if primary_key in df.columns else None
        report["data_types"] = {col: str(dtype) for col, dtype in df.dtypes.items()}

        return report

    # ==========================================================
    # Clinical Validation
    # ==========================================================

    def validate_clinical(self) -> Dict[str, Any]:
        """
        Validate the longitudinal clinical dataset.
        """
        report = self.validate_dataset(self.clinical,"clinical","facility_id")
        report["duplicate_reporting_periods"] = int(self.clinical.duplicated(subset=["facility_id","reporting_month"]).sum())
        report["unique_reporting_months"] = self.clinical["reporting_month"].nunique()
        report["unique_facilities"] = self.clinical["facility_id"].nunique()

        return report

    # ==========================================================
    # Required Column Validation
    # ==========================================================

    def validate_required_columns(self) -> Dict:
        """
        Ensure required columns exist.
        """
        required = {
            "clinical": ["facility_id","reporting_month","total_deliveries","live_births"],
            "facilities": ["facility_id","facility_name","district","province"],
            "operations": ["facility_id"],
            "workers": ["facility_id"],
            "governance": ["facility_id"],
        }

        datasets = {
            "clinical": self.clinical,
            "facilities": self.facilities,
            "operations": self.operations,
            "workers": self.workers,
            "governance": self.governance
        }
        report = {}
        for name, columns in required.items():
            missing = [c for c in columns
                if c not in datasets[name].columns
            ]
            report[name] = missing
        return report

    # ==========================================================
    # Facility Master Builder
    # ==========================================================

    def build_facility_master(self) -> pd.DataFrame:
        """
        Create one integrated record per facility.
        """
        self.facility_master = (
            self.facilities.merge(self.operations, on="facility_id", how="left")
            .merge(self.workers, on="facility_id", how="left")
            .merge(self.governance, on="facility_id", how="left"))

        return self.facility_master

    # ==========================================================
    # Facility Master Validation
    # ==========================================================

    def validate_facility_master(self) -> Dict:
        """
        Validate the integrated facility table.
        """
        return {
            "rows": len(self.facility_master),
            "columns": len(self.facility_master.columns),
            "duplicate_facilities": int(self.facility_master.duplicated(subset=["facility_id"]).sum()),
            "missing_values": self.facility_master.isna().sum().to_dict()
        }

    # ==========================================================
    # Execute ETL Pipeline
    # ==========================================================

    def process(self):
        """
        Execute the complete ETL pipeline.

        Returns
        -------
        clinical : DataFrame
            Monthly neonatal clinical records.

        facility_master : DataFrame
            One integrated record per facility.

        quality : dict
            Data quality report.
        """

        # ------------------------------------------
        # Load datasets
        # ------------------------------------------

        self.load_datasets()

        # ------------------------------------------
        # Clean datasets
        # ------------------------------------------

        self.clean_text()

        self.clean_percentages()

        self.clean_booleans()

        self.clean_numeric_columns()

        self.parse_dates()

        self.normalize_reporting_month()

        # ------------------------------------------
        # Validate datasets
        # ------------------------------------------

        quality = {
            "clinical": self.validate_clinical(),
            "facilities": self.validate_dataset(self.facilities, "facilities", "facility_id"),
            "operations": self.validate_dataset(self.operations, "operations", "facility_id"),
            "workers": self.validate_dataset(self.workers, "workers", "facility_id"),
            "governance": self.validate_dataset(self.governance, "governance", "facility_id"),
            "required_columns": self.validate_required_columns()
        }

        # ------------------------------------------
        # Build Facility Master
        # ------------------------------------------
        self.build_facility_master()
        quality["facility_master"] = (self.validate_facility_master())
        self.quality_report = quality

        return (
            self.clinical,
            self.facility_master,
            self.quality_report
        )