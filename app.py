
import os
from web import create_app
from database import create_table, close_connection, insert_user, verify_user,create_login_table

app = create_app()
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))
app.config['SESSION_COOKIE_SECURE'] = not os.environ.get('DEBUG')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

with app.app_context():
    create_table()
    create_login_table()
    if not verify_user(username="emc", password="emc", role="admin"):
        insert_user(username="emc", password="emc", role="admin")
app.teardown_appcontext(close_connection)

if __name__ == "__main__":
	debug_mode = os.environ.get('DEBUG') == 'True'
	app.run(debug=debug_mode, host="0.0.0.0")
