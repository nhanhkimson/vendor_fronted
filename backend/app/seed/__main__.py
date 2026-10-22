"""python -m app.seed  (truncates every table, then loads the demo data)"""

from app.seed.run import reset_database

if __name__ == "__main__":
    counts = reset_database()
    print("Seeded:", ", ".join(f"{k}={v}" for k, v in counts.items()))
