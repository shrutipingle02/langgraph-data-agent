"""Generate the sample ride-hailing dataset the agent queries against.

Five related tables written out as CSVs into data/. Run this once before
feed_db.py. Seeded, so re-running gives the same rows.
"""

import os
import csv
import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker("en_CA")
Faker.seed(42)
random.seed(42)

CSV_DIR = "data"

N_USERS = 8000
N_VEHICLES = 2200
N_RIDES = 40000

CITIES = [
    ("Toronto", "ON"), ("Montreal", "QC"), ("Vancouver", "BC"),
    ("Calgary", "AB"), ("Ottawa", "ON"), ("Edmonton", "AB"),
    ("Halifax", "NS"), ("Winnipeg", "MB"), ("Quebec City", "QC"),
]

MAKES = {
    "Toyota": ["Corolla", "Camry", "RAV4", "Prius"],
    "Honda": ["Civic", "Accord", "CR-V"],
    "Hyundai": ["Elantra", "Sonata", "Tucson"],
    "Tesla": ["Model 3", "Model Y"],
    "Ford": ["Escape", "Fusion"],
    "Chevrolet": ["Malibu", "Equinox"],
}
COLORS = ["White", "Black", "Grey", "Silver", "Blue", "Red"]

PAYMENT_METHODS = ["credit_card", "debit_card", "wallet", "apple_pay", "google_pay", "cash"]
PAYMENT_STATUSES = ["completed", "completed", "completed", "completed", "pending", "failed", "refunded"]
CANCELLATION_REASONS = ["rider_cancelled", "driver_cancelled", "no_driver_found", "rider_no_show"]
COMMENTS = [
    "Great driver, very friendly", "Clean car, smooth ride", "Arrived on time",
    "Could have been better", "Driver took a long route", "Excellent service",
    "Car smelled bad", "Very professional", "", "", "",
]

START = datetime(2025, 1, 1)
END = datetime(2026, 8, 31)


def rand_dt(start=START, end=END):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))


def write(name, header, rows):
    path = os.path.join(CSV_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name:16} {len(rows):>7,} rows")


os.makedirs(CSV_DIR, exist_ok=True)
print("Generating sample data...")

# ---------------------------------------------------------------- USERS
# First 70% are riders, rest are drivers. Drivers get the vehicles.
users = []
n_riders = int(N_USERS * 0.7)
for uid in range(1, N_USERS + 1):
    city, province = random.choice(CITIES)
    users.append([
        uid,
        fake.first_name(),
        fake.last_name(),
        f"user{uid}@example.com",
        fake.msisdn()[:11],
        city,
        province,
        "rider" if uid <= n_riders else "driver",
        rand_dt(START, datetime(2026, 6, 1)).date(),
        random.random() > 0.12,
    ])

write("users.csv",
      ["user_id", "first_name", "last_name", "email", "phone", "city",
       "province", "user_type", "signup_date", "is_active"],
      users)

rider_ids = list(range(1, n_riders + 1))
driver_ids = list(range(n_riders + 1, N_USERS + 1))

# ------------------------------------------------------------- VEHICLES
vehicles = []
for vid in range(1, N_VEHICLES + 1):
    make = random.choice(list(MAKES))
    vehicles.append([
        vid,
        random.choice(driver_ids),
        make,
        random.choice(MAKES[make]),
        random.randint(2016, 2026),
        f"{fake.lexify('??').upper()}{fake.numerify('###')}",
        random.choice(COLORS),
        random.random() > 0.1,
    ])

write("vehicles.csv",
      ["vehicle_id", "driver_id", "make", "model", "year",
       "license_plate", "color", "is_active"],
      vehicles)

# ---------------------------------------------------------------- RIDES
rides = []
completed_rides = []
for rid in range(1, N_RIDES + 1):
    requested = rand_dt()
    cancelled = random.random() < 0.12

    pickup_lat = round(random.uniform(43.0, 49.5), 6)
    pickup_lon = round(random.uniform(-123.5, -63.0), 6)
    drop_lat = round(pickup_lat + random.uniform(-0.25, 0.25), 6)
    drop_lon = round(pickup_lon + random.uniform(-0.25, 0.25), 6)

    if cancelled:
        rides.append([
            rid, random.choice(rider_ids), random.choice(driver_ids), requested,
            "", "", pickup_lat, pickup_lon, drop_lat, drop_lon,
            0, 0, 1.0, "cancelled", random.choice(CANCELLATION_REASONS),
        ])
        continue

    pickup = requested + timedelta(minutes=random.randint(1, 12))
    distance = round(random.uniform(0.8, 42.0), 2)
    dropoff = pickup + timedelta(minutes=int(distance * random.uniform(1.8, 3.2)) + 2)
    surge = random.choice([1.0, 1.0, 1.0, 1.2, 1.5, 1.8, 2.0])
    fare = round((2.75 + distance * 1.65 + random.uniform(0, 4)) * surge, 2)

    rides.append([
        rid, random.choice(rider_ids), random.choice(driver_ids), requested,
        pickup, dropoff, pickup_lat, pickup_lon, drop_lat, drop_lon,
        distance, fare, surge, "completed", "",
    ])
    completed_rides.append((rid, rides[-1][1], rides[-1][2], fare, dropoff))

write("rides.csv",
      ["ride_id", "rider_id", "driver_id", "requested_at", "pickup_time",
       "dropoff_time", "pickup_latitude", "pickup_longitude", "dropoff_latitude",
       "dropoff_longitude", "distance_km", "fare", "surge_multiplier",
       "status", "cancellation_reason"],
      rides)

# ------------------------------------------------------------- PAYMENTS
payments = []
for i, (rid, rider, _driver, fare, dropoff) in enumerate(completed_rides, start=1):
    payments.append([
        i, rid, rider, fare,
        random.choice(PAYMENT_METHODS),
        random.choice(PAYMENT_STATUSES),
        f"TXN-{i:08d}",
        dropoff + timedelta(seconds=random.randint(5, 300)),
    ])

write("payments.csv",
      ["payment_id", "ride_id", "user_id", "amount", "payment_method",
       "payment_status", "transaction_id", "payment_time"],
      payments)

# -------------------------------------------------------------- RATINGS
# Only about 70% of completed rides get rated.
ratings = []
i = 0
for rid, rider, driver, _fare, dropoff in completed_rides:
    if random.random() > 0.7:
        continue
    i += 1
    score = random.choices([5, 4, 3, 2, 1], weights=[55, 25, 10, 6, 4])[0]
    ratings.append([
        i, rid, rider, driver, score,
        random.choice(COMMENTS),
        dropoff + timedelta(minutes=random.randint(1, 600)),
    ])

write("ratings.csv",
      ["rating_id", "ride_id", "rider_id", "driver_id", "rating", "comment", "rated_at"],
      ratings)

print("Done. Now run: python feed_db.py")
