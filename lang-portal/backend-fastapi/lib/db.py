import sqlite3
import json
from pathlib import Path

class Database:
    def __init__(self, database='words.db'):
        self.database = database
        self.connection = None

    def connect(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.database)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_sql_file(self, filepath):
        """Execute SQL from a file"""
        with open(filepath, 'r') as f:
            sql = f.read()
        conn = self.connect()
        conn.executescript(sql)
        conn.commit()

    def load_json(self, filepath):
        """Load data from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)

    def setup_tables(self):
        """Create all tables from SQL files"""
        sql_dir = Path(__file__).parent.parent / 'sql' / 'setup'
        for sql_file in [
            'create_table_words.sql',
            'create_table_word_reviews.sql',
            'create_table_word_review_items.sql',
            'create_table_groups.sql',
            'create_table_word_groups.sql',
            'create_table_study_activities.sql',
            'create_table_study_sessions.sql'
        ]:
            self.execute_sql_file(sql_dir / sql_file)

    def import_study_activities(self, data_path):
        """Seed study activities from JSON"""
        activities = self.load_json(data_path)
        conn = self.connect()
        cursor = conn.cursor()
        for activity in activities:
            cursor.execute('''
                INSERT INTO study_activities (name, url, preview_url)
                VALUES (?, ?, ?)
            ''', (activity['name'], activity['url'], activity['preview_url']))
        conn.commit()

    def import_words(self, group_name, data_path):
        """Seed words and groups from JSON"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Create group
        cursor.execute('INSERT INTO groups (name) VALUES (?)', (group_name,))
        group_id = cursor.lastrowid
        
        # Insert words
        words = self.load_json(data_path)
        for word in words:
            cursor.execute('''
                INSERT INTO words (spanish, english, parts)
                VALUES (?, ?, ?)
            ''', (word['spanish'], word['english'], json.dumps(word['parts'])))
            
            word_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO word_groups (word_id, group_id)
                VALUES (?, ?)
            ''', (word_id, group_id))
        
        # Update word count
        cursor.execute('''
            UPDATE groups 
            SET words_count = (
                SELECT COUNT(*) FROM word_groups 
                WHERE group_id = ?
            ) 
            WHERE id = ?
        ''', (group_id, group_id))
        
        conn.commit()
        print(f"Added {len(words)} words to '{group_name}' group")

# Singleton instance
db = Database()