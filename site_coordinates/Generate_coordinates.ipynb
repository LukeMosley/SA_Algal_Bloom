import pandas as pd

# ---------------------------
# Settings
# ---------------------------
input_file = "MonitoringSites_Summary_29092025.xlsx"
output_file = "site_coordinates.csv"

# ---------------------------
# Load data
# ---------------------------
df = pd.read_excel(input_file, sheet_name=0)

# Rename SiteName → Site_Description to match app expectation
df = df.rename(columns={"SiteName": "Site_Description"})

# Keep only the required columns
coords_df = df[["Site_Description", "Latitude", "Longitude"]].dropna()

# Save to CSV
coords_df.to_csv(output_file, index=False)

#print column names for reference
print("Available columns:")
for col in df.columns:
    print(f"- {col}")

print(f"✅ Saved {len(coords_df)} site coordinates to {output_file}")

