from data_loader import DataLoader

loader = DataLoader()

clinical, facility_master, quality = loader.process()

print()

print("=" * 70)
print("CLINICAL DATASET")
print("=" * 70)

print(clinical.head())

print()

print("=" * 70)
print("FACILITY MASTER")
print("=" * 70)

print(facility_master.head())

print()

print("=" * 70)
print("QUALITY REPORT")
print("=" * 70)

for section, report in quality.items():

    print()

    print(section.upper())

    print("-" * 40)

    print(report)