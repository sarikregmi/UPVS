
from web import create_app
from database import create_table, close_connection, insert_user, verify_user,create_login_table

app = create_app()
app.secret_key = "cn dncsndcdjlsnjkcbskbsk bskvbvb sadvbvnbknvbv sknvb sknvbknsvbkvb"
with app.app_context():
    create_table()
    create_login_table()
    if not verify_user(username="emc", password="emc", role="admin"):
        insert_user(username="emc", password="emc", role="admin")
app.teardown_appcontext(close_connection)

if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0")
