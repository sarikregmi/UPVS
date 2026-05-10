import qrcode
import uuid
import os
from werkzeug.utils import secure_filename
from database import insert_qr_code

check= os.listdir(".")
if "qr" not in check:
    os.mkdir("qr")

def _normalize_base_url(base_url):
    value = (base_url or "").strip()
    if not value:
        return None
    return value.rstrip("/")

def generate_qr(i_d, filename=None, username=None, product_details=None, sol_create_signature=None, base_url=None):
    uid='ui' + str(uuid.uuid4())
    normalized_base_url = _normalize_base_url(base_url)
    if not normalized_base_url:
        normalized_base_url = "http://localhost:5000"
    data= f"{normalized_base_url}/ver?q={uid}"
    if not filename:
        filename = f"{i_d}qr.png"
    filename = secure_filename(filename)
    if not filename or '/' in filename or '\\' in filename or '..' in filename:
        filename = f"{uuid.uuid4()}.png"

    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    img.save("qr/" + filename)
    trulocation = "qr/" + filename
    insert_qr_code(
        uid=uid,
        data=data,
        image_url=trulocation,
        username=username,
        product_details=product_details,
        sol_create_signature=sol_create_signature,
    )
    return {
        "uid": uid,
        "verify_url": data,
        "image_url": trulocation,
        "product_details": product_details,
    }