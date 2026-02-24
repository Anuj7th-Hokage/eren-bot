import sqlite3
import os

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS gifs (
            type TEXT,
            file_id TEXT,
            UNIQUE(type, file_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS authorized_users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id, first_name, last_name, username):
    """
    Saves a user record if their details have changed since the last known entry.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if the most recent entry for this user is exactly the same
    c.execute('''
        SELECT first_name, last_name, username 
        FROM users 
        WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (user_id,))
    
    row = c.fetchone()
    if row:
        db_first, db_last, db_user = row
        # If nothing changed, do not save a duplicate row
        if db_first == first_name and db_last == last_name and db_user == username:
            conn.close()
            return
            
    # Insert new or updated record
    c.execute('''
        INSERT INTO users (user_id, first_name, last_name, username)
        VALUES (?, ?, ?, ?)
    ''', (user_id, first_name, last_name, username))
    
    conn.commit()
    conn.close()

def get_user_history(user_id):
    """
    Returns a list of unique past names/usernames for a user (oldest to newest).
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT DISTINCT first_name, last_name, username 
        FROM users 
        WHERE user_id = ? 
        ORDER BY timestamp ASC
    ''', (user_id,))
    
    rows = c.fetchall()
    conn.close()
    
    history_str = []
    for r in rows:
        fn = r[0] if r[0] else ""
        ln = f" {r[1]}" if r[1] else ""
        un = f" (@{r[2]})" if r[2] else ""
        
        full_name = f"{fn}{ln}{un}".strip()
        if full_name and full_name not in history_str:
            history_str.append(full_name)
            
    return history_str

def save_gif(gif_type, file_id):
    """
    Saves a GIF file_id into the database under a specific category.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO gifs (type, file_id)
            VALUES (?, ?)
        ''', (gif_type.lower(), file_id))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # Avoid duplicate GIFs in the same category
        success = False
    finally:
        conn.close()
    return success

def get_random_gif(gif_type):
    """
    Returns a random file_id of a GIF for the given category, if any exist.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT file_id FROM gifs 
        WHERE type = ? 
        ORDER BY RANDOM() LIMIT 1
    ''', (gif_type.lower(),))
    
    row = c.fetchone()
    conn.close()
    
    return row[0] if row else None

def add_authorized_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO authorized_users (user_id) VALUES (?)', (user_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_authorized_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM authorized_users WHERE user_id = ?', (user_id,))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0

def get_all_authorized_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id FROM authorized_users')
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]
