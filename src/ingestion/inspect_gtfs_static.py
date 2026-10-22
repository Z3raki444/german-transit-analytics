
import zipfile
import csv
import io

zip_path = "data/raw/long_distance_rail_gtfs.zip"

with zipfile.ZipFile(zip_path, "r") as z:
    print("Files inside the dataset:")

    for filename in z.namelist():
        print(filename)

    print("\n--- Preview stops.txt ---")

    with z.open("stops.txt") as file:
        reader = csv.DictReader(io.TextIOWrapper(file, encoding="utf-8-sig"))

        print("Columns:", reader.fieldnames)

        for i, row in enumerate(reader):
            if i == 5:
                break
            print(row)
