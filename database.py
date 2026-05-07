from flask import g, current_app, session
import sqlite3
import werkzeug

DATABASE = "app.db"
login_db = "login.db"

#start of database functions
#make database connection and return it, if it doesn't exist create it and return it
#make qr database and login database separate to avoid confusion and potential security issues
#for qr database, store uid, data, and image url

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config.get("DATABASE", DATABASE))
    return db

def get_login_db():
    db = getattr(g, "_login_database", None)
    if db is None:
        db = g._login_database = sqlite3.connect(current_app.config.get("LOGIN_DATABASE", login_db))
    return db
#create table for qr codes and login users
def create_table():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS qr_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, uid TEXT, data TEXT, image_url TEXT,sold BOOLEAN,creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,username TEXT,product_details TEXT,sol_create_signature TEXT,sol_sold_signature TEXT)"
    )
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(qr_codes)").fetchall()]
    if "product_details" not in columns:
        cursor.execute("ALTER TABLE qr_codes ADD COLUMN product_details TEXT")
    if "sol_create_signature" not in columns:
        cursor.execute("ALTER TABLE qr_codes ADD COLUMN sol_create_signature TEXT")
    if "sol_sold_signature" not in columns:
        cursor.execute("ALTER TABLE qr_codes ADD COLUMN sol_sold_signature TEXT")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS qr_activity (id INTEGER PRIMARY KEY AUTOINCREMENT, uid TEXT, action TEXT, actor TEXT, role TEXT, sol_signature TEXT, notes TEXT, creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )

    # Remove malformed legacy rows and duplicate UIDs from old test data.
    cursor.execute("DELETE FROM qr_codes WHERE uid IS NULL OR uid = '' OR data IS NULL OR data = ''")
    cursor.execute("DELETE FROM qr_codes WHERE creation = 'test'")
    cursor.execute("DELETE FROM qr_codes WHERE id NOT IN (SELECT MIN(id) FROM qr_codes GROUP BY uid)")
    db.commit()

def create_login_table():
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT,role TEXT,creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    # Migrate older databases that still have the deprecated sold column.
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()]
    if "sold" in columns:
        cursor.execute("ALTER TABLE users RENAME TO users_old")
        cursor.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT,role TEXT,creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        cursor.execute(
            "INSERT INTO users (id, username, password, role, creation) SELECT id, username, password, role, creation FROM users_old WHERE id IN (SELECT MIN(id) FROM users_old GROUP BY username)"
        )
        cursor.execute("DROP TABLE users_old")
    cursor.execute("DELETE FROM users WHERE id NOT IN (SELECT MIN(id) FROM users GROUP BY username)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_unique ON users(username)")
    db.commit()
#qr logic functions
def insert_qr_code(creation=None, uid=None, data=None, image_url=None, sold=False, username=None, product_details=None, sol_create_signature=None, sol_sold_signature=None):
    db = get_db()
    cursor = db.cursor()
    if creation:
        cursor.execute(
            "INSERT INTO qr_codes (uid, data, image_url, sold, creation, username, product_details, sol_create_signature, sol_sold_signature) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, data, image_url, sold, creation, username, product_details, sol_create_signature, sol_sold_signature),
        )
    else:
        cursor.execute(
            "INSERT INTO qr_codes (uid, data, image_url, sold, username, product_details, sol_create_signature, sol_sold_signature) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, data, image_url, sold, username, product_details, sol_create_signature, sol_sold_signature),
        )

    db.commit()

def get_qr_code(uid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT data, image_url, product_details, sold, sol_create_signature, sol_sold_signature FROM qr_codes WHERE uid = ?",
        (uid,),
    )
    result = cursor.fetchone()
    return result if result else None

def mork_sold(uid, sol_signature=None):
    db = get_db()
    cursor = db.cursor()
    if sol_signature:
        cursor.execute(
            "UPDATE qr_codes SET sold = ?, sol_sold_signature = ? WHERE uid = ?",
            (True, sol_signature, uid),
        )
    else:
        cursor.execute("UPDATE qr_codes SET sold = ? WHERE uid = ?", (True, uid))
    db.commit()


def record_qr_activity(uid, action, actor=None, role=None, sol_signature=None, notes=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO qr_activity (uid, action, actor, role, sol_signature, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, action, actor, role, sol_signature, notes),
    )
    db.commit()


def is_signature_used(sol_signature, action=None):
    signature = (sol_signature or "").strip()
    if not signature:
        return False

    db = get_db()
    cursor = db.cursor()
    if action:
        cursor.execute(
            "SELECT 1 FROM qr_activity WHERE sol_signature = ? AND action = ? LIMIT 1",
            (signature, action),
        )
    else:
        cursor.execute(
            "SELECT 1 FROM qr_activity WHERE sol_signature = ? LIMIT 1",
            (signature,),
        )
    return cursor.fetchone() is not None


def get_qr_sol_entry(uid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT sol_create_signature, sol_sold_signature FROM qr_codes WHERE uid = ?",
        (uid,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    create_sig, sold_sig = row
    has_entry = bool(create_sig or sold_sig)
    return {
        "has_entry": has_entry,
        "create_signature": create_sig,
        "sold_signature": sold_sig,
    }


def get_qr_activity(uid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT action, actor, role, sol_signature, creation FROM qr_activity WHERE uid = ? ORDER BY id DESC",
        (uid,),
    )
    return cursor.fetchall()


def purge_all_qr_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM qr_activity")
    cursor.execute("DELETE FROM qr_codes")
    db.commit()


def get_unsold_qr_codes(username=None):
    db = get_db()
    cursor = db.cursor()
    if username:
        cursor.execute(
            "SELECT uid, data, image_url, creation, product_details FROM qr_codes WHERE (sold = 0 OR sold IS NULL) AND username = ? ORDER BY id DESC",
            (username,),
        )
    else:
        cursor.execute(
            "SELECT uid, data, image_url, creation, product_details FROM qr_codes WHERE sold = 0 OR sold IS NULL ORDER BY id DESC"
        )
    return cursor.fetchall()


# login database functions
def insert_user(username, password, role='0'):
    username = (username or "").strip()
    if not username:
        return False

    db = get_login_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT 1 FROM users WHERE lower(trim(username)) = lower(?)",
        (username,),
    )
    if cursor.fetchone():
        return False

    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False
  
def verify_user(username, password,role='0'):
    username = (username or "").strip()

    db = get_login_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT password FROM users WHERE lower(trim(username)) = lower(?) AND role = ?", (username, role)
    )
    result = cursor.fetchone()
    if not result:
        return False

    stored_password = result[0]
    return stored_password == password or werkzeug.security.check_password_hash(stored_password, password)
#function to store user cookie in session
def user_cookie_store(username, cook):
                session['user'] = username
                session['role'] = cook
def get_user_cookie():
    user = session.get('user')
    role = session.get('role')
    return user, role      


def get_all_users():
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute("SELECT username, role, creation FROM users ORDER BY id ASC")
    return cursor.fetchall()


def update_user_password(username, new_hashed_password):
    username = (username or "").strip()
    if not username:
        return False
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE lower(trim(username)) = lower(?)", (new_hashed_password, username))
    db.commit()
    return cursor.rowcount > 0


def delete_user(username):
    username = (username or "").strip()
    if not username:
        return False
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE lower(trim(username)) = lower(?)", (username,))
    db.commit()
    return cursor.rowcount > 0

#close database connection when app context is torn down

def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()
    login_db = getattr(g, "_login_database", None)
    if login_db is not None:
        login_db.close()
#cookie closser
def close_cookie(exception):
    session.pop('user', None)
    session.pop('role', None)