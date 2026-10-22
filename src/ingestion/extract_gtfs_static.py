
from pathlib import Path
from urllib.request import urlretrieve

# Dataset source
URL = "https://download.gtfs.de/germany/fv_free/latest.zip"

# Destination for raw data
OUTPUT = Path("data/raw/long_distance_rail_gtfs.zip")

# Create the directory if it doesn't exist
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Download the dataset
print("Downloading German railway data...")
urlretrieve(URL, OUTPUT)

print(f"Download complete: {OUTPUT}")
