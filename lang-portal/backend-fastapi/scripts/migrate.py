from lib.db import db

def run_migrations():
    print("Running database migrations...")
    try:
        db.setup_tables()
        print("Schema created successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    run_migrations()