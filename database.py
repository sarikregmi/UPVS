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
        "CREATE TABLE IF NOT EXISTS qr_codes (id INTEGER PRIMARY KEY AUTOINCREMENT, uid TEXT, data TEXT, image_url TEXT,sold BOOLEAN,creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,username TEXT)"
    )
    db.commit()

def create_login_table():
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT,role TEXT,sold BOOLEAN,creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    db.commit()
#qr logic functions
def insert_qr_code(creation, uid=None, data=None, image_url=None, sold=False, username=None,solcre=None,solsold=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(     
        "INSERT INTO qr_codes (uid, data, image_url, sold, creation, username) VALUES (?, ?, ?, ?, ?, ?)", (uid, data, image_url, sold, creation, username)
    )

    db.commit()

def get_qr_code(uid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT data, image_url FROM qr_codes WHERE uid = ?", (uid,))
    result = cursor.fetchone()
    return result if result else None

def mork_sold(uid):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE qr_codes SET sold = ? WHERE uid = ?", (True, uid))
    db.commit()


# login database functions
def insert_user(username, password, role='0'):
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role)
    )
    db.commit()
  
def verify_user(username, password,role='0'):
    db = get_login_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT password FROM users WHERE username = ? AND role = ?", (username, role)
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