import qrcode
import uuid
import os
from database import insert_qr_code
#cheak if qr folder exist if not create it
check= os.listdir(".")
if "qr" not in check:
    os.mkdir("qr")
# spicial id for each qr code

#rule for qr code
qr = qrcode.QRCode(
    version=2,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=1,
)

# This function generates a QR code from the provided data and saves it as an image file.
def generate_qr(i_d, filename=None):
    uid='ui' + str(uuid.uuid4())
    data= f"http://192.168.18.112:5000/ver?q={uid}"
    if not filename:
        filename = f"{i_d}qr.png"
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    img.save("qr/" + filename)
    trulocation = "qr/" + filename
    insert_qr_code("test", uid=uid, data=data, image_url=trulocation)
    return trulocation, data