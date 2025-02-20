from lib.db import db

def seed_data():
    print("Seeding initial data...")
    try:
        db.import_words(
            group_name='Core Verbs',
            data_path='seed/data_verbs.json'
        )
        db.import_words(
            group_name='Core Adjectives',
            data_path='seed/data_adjectives.json'
        )
        db.import_study_activities('seed/study_activities.json')
        print("Data seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()