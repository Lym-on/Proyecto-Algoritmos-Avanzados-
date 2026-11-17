import socket

import qrcode

from datos import LOTES


def ip_local():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))     # no envía nada, solo detecta tu IP del WiFi
        return s.getsockname()[0]
    finally:
        s.close()


ip = ip_local()
for codigo in LOTES:
    url = f"http://{ip}:5000/lote/{codigo}"
    qrcode.make(url).save(f"qr/{codigo}.png")
    print("QR creado:", url)
