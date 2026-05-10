
import os
from dotenv import load_dotenv
from web import create_app
from database import create_table, close_connection, insert_user, verify_user, create_login_table
import werkzeug.security

load_dotenv()

app = create_app()
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

with app.app_context():
    create_table()
    create_login_table()
    admin_pass = os.environ.get('ADMIN_PASSWORD', os.urandom(16).hex())
    admin_hash = werkzeug.security.generate_password_hash(admin_pass)
    if not verify_user(username="emc", password=admin_pass, role="admin"):
        insert_user(username="emc", password=admin_hash, role="admin")
        print(f"Admin user created. Password: {admin_pass} (set via ADMIN_PASSWORD env var)")
app.teardown_appcontext(close_connection)

if __name__ == "__main__":
	debug_mode = os.environ.get('DEBUG') == 'True'
	app.run(debug=debug_mode, host="0.0.0.0")
