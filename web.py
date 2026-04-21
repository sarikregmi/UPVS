from flask import Flask, app, redirect, redirect, render_template, request, send_from_directory
import time
import uuid
import werkzeug
from int import generate_qr
from database import get_db, create_table, insert_qr_code, get_qr_code, close_connection, insert_user, verify_user, user_cookie_store
from database import get_user_cookie, close_cookie,mork_sold
def create_app(img_url="qr/temp.png"):

    initial_img_url = img_url

    app = Flask(__name__, template_folder="static")

    @app.route("/qr/<path:filename>")
    def qr_image(filename):
        return send_from_directory("qr", filename)

    @app.route("/")
    def hello_world():
        return render_template("index.html")
    @app.route("/crt", methods=["GET", "POST"])
    def create_qr():
        action = request.form.get('action')
        form_id =str(uuid.uuid4())
        current_img_url = initial_img_url
        qr_value = None
        cache_bust = int(time.time() * 1000)

        if action == "generate" and form_id:
            current_img_url, qr_value = generate_qr(form_id)
            
        if login:
            return render_template(
                "crt.html",
                img_url=current_img_url,
                i_d=form_id,
                data=qr_value,
            cache_bust=cache_bust,
        )
        else:
            return render_template("failor.html")
    @app.route("/ver")
    def verify_qr():
        qr_value = request.args.get("q")
        if get_user_cookie()[1] == 'cem':
            if qr_value:
                return redirect(f"/seller?q={qr_value}")
            return redirect("/seller")
        result = get_qr_code(qr_value)
        if result:
            finding='found'
            data, image_url = result
            return render_template("ver.html", data=data, image_url=image_url, finding=finding)
        finding='not found'
        data=None
        image_url='qr/fake.png'
        return render_template("ver.html", data=data, image_url=image_url, finding=finding)
    @app.route("/login", methods=["GET", "POST"])

    def login():
        if get_user_cookie()[0]:
            if get_user_cookie()[1] == 'emc':
                return redirect("/admin")
            elif get_user_cookie()[1] == 'mec':
                db = get_db()
                existing_user = db.execute(
                    "SELECT 1 FROM users WHERE username = ?",
                    (username,),
                ).fetchone()

                if existing_user:
                    return render_template("admin.html", error="Username already exists")
                return render_template("crt.html")
            elif get_user_cookie()[1] == 'cem':
                return redirect("/seller")
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if verify_user(username, password,role='0'):
                return render_template("crt.html")
            elif verify_user(username, password,role='mf'):
                login=True
                user_cookie_store(username, 'mec')
                return render_template("crt.html")
            elif verify_user(username, password,role='admin') :
                login='adtrue'
                user_cookie_store(username, 'emc')  
                return redirect("/admin")
            elif verify_user(username, password,role='seller') :
                login='seltrue'
                user_cookie_store(username, 'cem')
                return redirect("/seller")
            else:
                return render_template("login.html", error="Invalid credentials")
            
        return render_template("login.html")
    @app.route("/admin", methods=["GET", "POST"])
    def user_maker():
        if get_user_cookie()[1] != 'emc':
            return redirect("/login")

        if request.method == "GET":
            return render_template("admin.html")

        username = request.form.get("username")
        password = request.form.get("password")
        if request.form.get("role") == 'emc':
            role = 'admin'
        elif request.form.get("role") == 'mec':
            role = 'mf'
        elif request.form.get("role") == 'cem':
            role = 'seller'
        else:
            role = '0'

        if not username or not password:
            return render_template("admin.html", error="Username and password are required")

        hashed_password = werkzeug.security.generate_password_hash(password)
        insert_user(username, hashed_password, role)
        return render_template("admin.html")
    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        close_cookie(None)
        return redirect("/login")
    @app.route("/seller", methods=["GET", "POST"])
    def seller():
        qr_value = request.values.get("q")

        if get_user_cookie()[1] != 'cem':
            if qr_value:
                return redirect(f"/ver?q={qr_value}")
            return redirect("/ver")

        if request.method == "POST" and qr_value:
            mork_sold(qr_value)

        result = get_qr_code(qr_value) if qr_value else None
        if result:
            data, image_url = result
            return render_template("seller.html", data=data, image_url=image_url, q=qr_value)

        data = None
        image_url = 'qr/fake.png'
        return render_template("seller.html", data=data, image_url=image_url, q=qr_value)
    return app