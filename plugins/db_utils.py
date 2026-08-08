import os
import json
import random
from datetime import datetime

# DB path in home directory
DB_PATH = os.path.expanduser("~/.config/erenbot/users.json")

# In-memory storage
db = {
    "users": {},            # user_id (str) -> list of dicts {first_name, last_name, username, timestamp}
    "gifs": {},             # type -> list of file_ids
    "authorized_users": [], # list of user_ids (int)
    "tracked_users": [],    # list of dicts {user_id, chat_id}
    "vv_cache": {},         # "chat_id:msg_id" -> saved message id in Saved Messages
}

def load_db():
    global db
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r') as f:
                loaded = json.load(f)
                db.update(loaded)
        except Exception:
            pass
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        save_db()

def save_db():
    global db
    try:
        with open(DB_PATH, 'w') as f:
            json.dump(db, f, indent=4)
    except Exception:
        pass

def init_db():
    load_db()

def save_user(user_id, first_name, last_name, username):
    uid_str = str(user_id)
    if uid_str not in db["users"]:
        db["users"][uid_str] = []
    
    history = db["users"][uid_str]
    if history:
        last_entry = history[-1]
        if last_entry.get("first_name") == first_name and \
           last_entry.get("last_name") == last_name and \
           last_entry.get("username") == username:
            return # Nothing changed
            
    history.append({
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "timestamp": datetime.now().isoformat()
    })
    save_db()

def get_user_history(user_id):
    uid_str = str(user_id)
    history_list = db["users"].get(uid_str, [])
    
    history_str = []
    for r in history_list:
        fn = r.get("first_name") or ""
        ln = f" {r.get('last_name')}" if r.get('last_name') else ""
        un = f" (@{r.get('username')})" if r.get('username') else ""
        
        full_name = f"{fn}{ln}{un}".strip()
        if full_name and full_name not in history_str:
            history_str.append(full_name)
            
    return history_str

def save_gif(gif_type, file_id):
    gtype = gif_type.lower()
    if gtype not in db["gifs"]:
        db["gifs"][gtype] = []
        
    if file_id not in db["gifs"][gtype]:
        db["gifs"][gtype].append(file_id)
        save_db()
        return True
    return False

def get_random_gif(gif_type):
    gtype = gif_type.lower()
    gifs = db["gifs"].get(gtype, [])
    if gifs:
        return random.choice(gifs)
    return None

def add_authorized_user(user_id):
    if user_id not in db["authorized_users"]:
        db["authorized_users"].append(user_id)
        save_db()
        return True
    return False

def remove_authorized_user(user_id):
    if user_id in db["authorized_users"]:
        db["authorized_users"].remove(user_id)
        save_db()
        return True
    return False

def get_all_authorized_users():
    return db["authorized_users"]

def add_tracked_user(user_id, chat_id):
    for t in db["tracked_users"]:
        if t["user_id"] == user_id and t["chat_id"] == chat_id:
            return False
            
    db["tracked_users"].append({"user_id": user_id, "chat_id": chat_id})
    save_db()
    return True

def remove_tracked_user(user_id, chat_id):
    initial_len = len(db["tracked_users"])
    db["tracked_users"] = [t for t in db["tracked_users"] if not (t["user_id"] == user_id and t["chat_id"] == chat_id)]
    if len(db["tracked_users"]) < initial_len:
        save_db()
        return True
    return False

def get_all_tracked_users():
    return [(t["user_id"], t["chat_id"]) for t in db["tracked_users"]]

def save_vv_cache(chat_id, msg_id, saved_msg_id):
    db.setdefault("vv_cache", {})
    db["vv_cache"][f"{chat_id}:{msg_id}"] = saved_msg_id
    save_db()

def get_vv_cache(chat_id, msg_id):
    return db.get("vv_cache", {}).get(f"{chat_id}:{msg_id}")
