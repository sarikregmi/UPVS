from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
import os
import time
import re
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
        get_all_users,
        update_user_password,
        delete_user,
    mork_sold,
    purge_all_qr_data,
    record_qr_activity,
    user_cookie_store,
    verify_user,
)

PLATFORM_WALLET = os.environ.get("PLATFORM_WALLET", "BiGkF9DSBtYQhkeFMbe5xfkLPz2v9xvPYhVghiX9YtpT")
CREATE_FEE_SOL = 0.05
SOLD_FEE_SOL = 0.01


def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain digit"
    return True, "OK"



def get_public_base_url():
    configured = (os.environ.get("PUBLIC_BASE_URL") or "").strip()
    if configured:
        return configured.rstrip("/")

    host_url = (request.host_url or "").rstrip("/")
    return host_url


def get_rpc_endpoints():
    configured = (os.environ.get("SOLANA_RPC_URL") or "").strip()
    fallbacks = [
        value.strip()
        for value in (os.environ.get("SOLANA_RPC_FALLBACKS") or "").split(",")
        if value.strip()
    ]

    defaults = [
        "https://api.devnet.solana.com",
        "https://solana-devnet.g.alchemy.com/v2/demo",
        "https://rpc.ankr.com/solana_devnet",
        "https://api.mainnet-beta.solana.com",
    ]

    endpoints = []
    if configured:
        endpoints.append(configured)
    endpoints.extend(fallbacks)
    endpoints.extend(defaults)

    unique_endpoints = []
    for endpoint in endpoints:
        if endpoint not in unique_endpoints:
            unique_endpoints.append(endpoint)
    return unique_endpoints


def get_solana_explorer_cluster():
    primary_endpoint = (get_rpc_endpoints()[0] if get_rpc_endpoints() else "").lower()
    if "devnet" in primary_endpoint:
        return "devnet"
    if "testnet" in primary_endpoint:
        return "testnet"
    return "mainnet-beta"


ALLOWED_ROLES = {'admin', 'mf', 'seller', '0'}
ALLOWED_ROLES_MAPPING = {'emc': 'admin', 'mec': 'mf', 'cem': 'seller'}

def create_app(img_url="qr/temp.png"):

    initial_img_url = img_url

    app = Flask(__name__, template_folder="templates", static_folder="static")
    limiter = Limiter(app=app, key_func=get_remote_address)
    csrf = CSRFProtect(app)

    @app.context_processor
    def inject_app_config():
        return {
            "rpc_endpoints": get_rpc_endpoints(),
            "solana_explorer_cluster": get_solana_explorer_cluster(),
        }

    @app.route("/qr/<filename>")
    @csrf.exempt
    def qr_image(filename):
        safe_filename = secure_filename(filename)
        if not safe_filename or safe_filename != filename:
            return "Invalid filename", 400
        return send_from_directory("qr", safe_filename)

    @app.route("/")
    @csrf.exempt
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

    @csrf.exempt
    @app.route("/ver")
    def verify_qr():
        actor, role = get_user_cookie()
        if not actor:
            return redirect("/login")

        qr_value = request.args.get("q")
        if role == 'cem':
            if qr_value:
                return redirect(f"/seller?q={qr_value}")
            return redirect("/seller")

        role_map = {"mec": "mf", "cem": "seller", "emc": "admin"}
        result = get_qr_code(qr_value)
        sol_entry = get_qr_sol_entry(qr_value) if qr_value else None
        activity = get_qr_activity(qr_value) if qr_value else []
        visible_activity = [row for row in activity if row[0] != "verify"]

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
                activity=visible_activity,
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
            activity=visible_activity,
            uid=qr_value,
        )

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
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
                if not user_cookie_store(username, 'mec'):
                    return render_template("login.html", error="Invalid role")
                return redirect("/crt")
            elif verify_user(username, password, role='mf'):
                if not user_cookie_store(username, 'mec'):
                    return render_template("login.html", error="Invalid role")
                return redirect("/crt")
            elif verify_user(username, password, role='admin'):
                if not user_cookie_store(username, 'emc'):
                    return render_template("login.html", error="Invalid role")
                return redirect("/admin")
            elif verify_user(username, password, role='seller'):
                if not user_cookie_store(username, 'cem'):
                    return render_template("login.html", error="Invalid role")
                return redirect("/seller")
            else:
                return render_template("login.html", error="Invalid credentials")

        return render_template("login.html")
    @app.route("/admin", methods=["GET", "POST"])
    def user_maker():
        if get_user_cookie()[1] != 'emc':
            return redirect("/login")
        if request.method == "GET":
            users = get_all_users()
            return render_template("admin.html", users=users)

        action = (request.form.get("action") or "create").strip()

        if action == "create":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            form_role = request.form.get("role") or ""
            role = ALLOWED_ROLES_MAPPING.get(form_role, '0')
            if role not in ALLOWED_ROLES:
                users = get_all_users()
                return render_template("admin.html", users=users, error="Invalid role")

            if not username or not password:
                users = get_all_users()
                return render_template("admin.html", users=users, error="Username and password are required")

            is_valid, msg = validate_password_strength(password)
            if not is_valid:
                users = get_all_users()
                return render_template("admin.html", users=users, error=msg)

            hashed_password = werkzeug.security.generate_password_hash(password)
            created = insert_user(username, hashed_password, role)
            users = get_all_users()
            if not created:
                return render_template("admin.html", users=users, error="Username already exists")
            return render_template("admin.html", users=users, message="User created")

        if action == "change_password":
            target = (request.form.get("target_username") or "").strip()
            new_password = request.form.get("new_password") or ""
            if not target or not new_password:
                users = get_all_users()
                return render_template("admin.html", users=users, error="Username and new password are required")

            is_valid, msg = validate_password_strength(new_password)
            if not is_valid:
                users = get_all_users()
                return render_template("admin.html", users=users, error=msg)

            hashed = werkzeug.security.generate_password_hash(new_password)
            ok = update_user_password(target, hashed)
            users = get_all_users()
            if not ok:
                return render_template("admin.html", users=users, error="Failed to update password")
            return render_template("admin.html", users=users, message=f"Password updated for {target}")

        if action == "delete_user":
            target = (request.form.get("target_username") or "").strip()
            if not target:
                users = get_all_users()
                return render_template("admin.html", users=users, error="Username required to delete")
            ok = delete_user(target)
            users = get_all_users()
            if not ok:
                return render_template("admin.html", users=users, error="Failed to delete user (not found)")
            return render_template("admin.html", users=users, message=f"Deleted user {target}")

        users = get_all_users()
        return render_template("admin.html", users=users)
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
    @limiter.limit("30 per minute")
    def record_sol_entry():
        actor, role = get_user_cookie()
        if not actor:
            return jsonify({"error": "Unauthorized"}), 401

        uid = (request.json or {}).get("uid") if request.is_json else request.form.get("uid")
        action = (request.json or {}).get("action") if request.is_json else request.form.get("action")
        signature = (request.json or {}).get("signature") if request.is_json else request.form.get("signature")

        uid = (uid or "").strip()
        action = (action or "").strip().lower()
        signature = (signature or "").strip()

        if not uid or action not in {"create", "sold", "verify"}:
            return jsonify({"error": "uid and valid action are required"}), 400

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