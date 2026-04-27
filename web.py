from flask import Flask, jsonify, redirect, render_template, request, send_from_directory
import os
import time
import uuid
import werkzeug
from int import generate_qr
from database import (
    close_cookie,
    get_qr_activity,
    get_qr_code,
    get_qr_sol_entry,
    get_unsold_qr_codes,
    get_user_cookie,
    insert_user,
    mork_sold,
    purge_all_qr_data,
    record_qr_activity,
    user_cookie_store,
    verify_user,
)

PLATFORM_WALLET = "BiGkF9DSBtYQhkeFMbe5xfkLPz2v9xvPYhVghiX9YtpT"
CREATE_FEE_SOL = 0.05
SOLD_FEE_SOL = 0.01


def get_public_base_url():
    configured = (os.environ.get("PUBLIC_BASE_URL") or "").strip()
    if configured:
        return configured.rstrip("/")

    host_url = (request.host_url or "").rstrip("/")
    return host_url


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
        if get_user_cookie()[1] != 'mec':
            return redirect("/login")

        current_user = get_user_cookie()[0]
        action = request.form.get('action')
        form_id =str(uuid.uuid4())
        current_img_url = initial_img_url
        qr_value = None
        product_details = ""
        sol_signature = ""
        quantity = 1
        generated_qrs = []
        error = None
        cache_bust = int(time.time() * 1000)

        if action == "generate" and form_id:
            product_details = (request.form.get("data") or "").strip()
            quantity_raw = (request.form.get("quantity") or "1").strip()
            sol_signature = (request.form.get("sol_signature") or "").strip()

            if not product_details:
                error = "Product details are required"
            else:
                try:
                    quantity = int(quantity_raw)
                except ValueError:
                    quantity = 1

                if quantity < 1:
                    quantity = 1
                if quantity > 100:
                    quantity = 100

                base_url = get_public_base_url()
                for index in range(quantity):
                    item_id = f"{form_id}-{index + 1}"
                    generated = generate_qr(
                        item_id,
                        username=current_user,
                        product_details=product_details,
                        sol_create_signature=(sol_signature or None),
                        base_url=base_url,
                    )
                    record_qr_activity(
                        generated["uid"],
                        "create",
                        actor=current_user,
                        role="mf",
                        sol_signature=(sol_signature or None),
                        notes=product_details,
                    )
                    generated_qrs.append(generated)

                if generated_qrs:
                    current_img_url = generated_qrs[0]["image_url"]
                    qr_value = generated_qrs[0]["verify_url"]

        unsold_codes = get_unsold_qr_codes(current_user)

        return render_template(
            "crt.html",
            img_url=current_img_url,
            i_d=form_id,
            data=qr_value,
            cache_bust=cache_bust,
            unsold_codes=unsold_codes,
            generated_qrs=generated_qrs,
            product_details=product_details,
            sol_signature="",
            quantity=quantity,
            error=error,
            platform_wallet=PLATFORM_WALLET,
            create_fee_sol=CREATE_FEE_SOL,
        )

    @app.route("/ver")
    def verify_qr():
        qr_value = request.args.get("q")
        if get_user_cookie()[1] == 'cem':
            if qr_value:
                return redirect(f"/seller?q={qr_value}")
            return redirect("/seller")

        role_map = {"mec": "mf", "cem": "seller", "emc": "admin"}
        actor, role = get_user_cookie()

        result = get_qr_code(qr_value)
        sol_entry = get_qr_sol_entry(qr_value) if qr_value else None
        activity = get_qr_activity(qr_value) if qr_value else []

        if result:
            finding='found'
            data, image_url, product_details, sold, sol_create_signature, sol_sold_signature = result
            if qr_value:
                record_qr_activity(
                    qr_value,
                    "verify",
                    actor=actor,
                    role=role_map.get(role),
                    notes="Verification screen opened",
                )
            return render_template(
                "ver.html",
                data=data,
                image_url=image_url,
                product_details=product_details,
                finding=finding,
                sold=sold,
                sol_entry=sol_entry,
                activity=activity,
                uid=qr_value,
            )
        finding='not found'
        data=None
        product_details=None
        image_url='qr/fake.png'
        return render_template(
            "ver.html",
            data=data,
            image_url=image_url,
            product_details=product_details,
            finding=finding,
            sold=False,
            sol_entry=sol_entry,
            activity=activity,
            uid=qr_value,
        )

    @app.route("/login", methods=["GET", "POST"])

    def login():
        if get_user_cookie()[0]:
            if get_user_cookie()[1] == 'emc':
                return redirect("/admin")
            elif get_user_cookie()[1] == 'mec':
                return redirect("/crt")
            elif get_user_cookie()[1] == 'cem':
                return redirect("/seller")
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = (request.form.get("password") or "")
            if verify_user(username, password, role='0'):
                user_cookie_store(username, 'mec')
                return redirect("/crt")
            elif verify_user(username, password, role='mf'):
                user_cookie_store(username, 'mec')
                return redirect("/crt")
            elif verify_user(username, password, role='admin'):
                user_cookie_store(username, 'emc')  
                return redirect("/admin")
            elif verify_user(username, password, role='seller'):
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

        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
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
        created = insert_user(username, hashed_password, role)
        if not created:
            return render_template("admin.html", error="Username already exists")
        return render_template("admin.html")
    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        close_cookie(None)
        return redirect("/login")
    @app.route("/seller", methods=["GET", "POST"])
    def seller():
        qr_value = request.values.get("q")
        seller_error = None

        if get_user_cookie()[1] != 'cem':
            if qr_value:
                return redirect(f"/ver?q={qr_value}")
            return redirect("/ver")

        current_user = get_user_cookie()[0]

        if request.method == "POST" and qr_value:
            sol_signature = (request.form.get("sol_signature") or "").strip()
            existing = get_qr_code(qr_value)
            already_sold = bool(existing and existing[3])
            if already_sold:
                seller_error = "This QR is already sold."
            else:
                mork_sold(qr_value, sol_signature=(sol_signature or None))
                record_qr_activity(
                    qr_value,
                    "sold",
                    actor=current_user,
                    role="seller",
                    sol_signature=(sol_signature or None),
                    notes="Marked as sold",
                )

        result = get_qr_code(qr_value) if qr_value else None
        sol_entry = get_qr_sol_entry(qr_value) if qr_value else None
        activity = get_qr_activity(qr_value) if qr_value else []
        if result:
            data, image_url, product_details, sold, sol_create_signature, sol_sold_signature = result
            return render_template(
                "seller.html",
                data=data,
                image_url=image_url,
                product_details=product_details,
                sold=sold,
                sol_entry=sol_entry,
                activity=activity,
                q=qr_value,
                seller_error=seller_error,
                platform_wallet=PLATFORM_WALLET,
                sold_fee_sol=SOLD_FEE_SOL,
            )

        data = None
        product_details = None
        image_url = 'qr/fake.png'
        return render_template(
            "seller.html",
            data=data,
            image_url=image_url,
            product_details=product_details,
            sold=False,
            sol_entry=sol_entry,
            activity=activity,
            q=qr_value,
            seller_error=seller_error,
            platform_wallet=PLATFORM_WALLET,
            sold_fee_sol=SOLD_FEE_SOL,
        )

    @app.route("/api/sol-entry", methods=["POST"])
    def record_sol_entry():
        uid = (request.json or {}).get("uid") if request.is_json else request.form.get("uid")
        action = (request.json or {}).get("action") if request.is_json else request.form.get("action")
        signature = (request.json or {}).get("signature") if request.is_json else request.form.get("signature")

        uid = (uid or "").strip()
        action = (action or "").strip().lower()
        signature = (signature or "").strip()

        if not uid or action not in {"create", "sold", "verify"}:
            return jsonify({"error": "uid and valid action are required"}), 400

        actor, role = get_user_cookie()
        role_map = {"mec": "mf", "cem": "seller", "emc": "admin"}
        record_qr_activity(
            uid,
            action,
            actor=actor,
            role=role_map.get(role),
            sol_signature=(signature or None),
            notes="Recorded from API",
        )
        return jsonify({"ok": True})

    return app