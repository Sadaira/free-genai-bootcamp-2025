from scripts.migrate import run_migrations
from scripts.seed import seed_data

def init_db():
    print("Initializing database...")
    run_migrations()
    seed_data()
    print("Database ready!")

if __name__ == "__main__":
    init_db()