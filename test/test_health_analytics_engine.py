from data_loader import DataLoader
from health_analytics_engine import HealthAnalyticsEngine
from risk_analytics_engine import RiskAnalyticsEngine
from intervention_engine import InterventionEngine
from recommendation_engine import RecommendationEngine

loader = DataLoader()

clinical, facility_master, quality = loader.process()

engine = HealthAnalyticsEngine(clinical, facility_master)

# print("\nEXECUTIVE SUMMARY")
# print(engine.executive_summary())

# print("\nCLINICAL METRICS")
# print(engine.clinical_metrics())

# print("\nFACILITY METRICS")
# print(engine.facility_metrics())

# print("\nWORKFORCE METRICS")
# print(engine.workforce_metrics())

# print("\nGOVERNANCE METRICS")
# print(engine.governance_metrics())

# print("\nPROVINCE ANALYTICS")
# print(engine.province_analytics())

# print("\nFACILITY PERFORMANCE")
# print(engine.facility_performance().head())

performance = engine.facility_performance()
risk = RiskAnalyticsEngine(performance)
risk_df = risk.classify_risk()

# print("\nRISK SCORES")
# print(risk_df)

# opportunity = InterventionEngine(risk_df)
# print("\nOPPORTUNITY INDEX")
# print(opportunity.opportunity_index())

recommendation = RecommendationEngine(risk_df)

print("\nRECOMMENDATIONS")
print(recommendation.generate())