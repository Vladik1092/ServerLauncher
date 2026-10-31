from ui import create_window
import certifi
import os
import sys

if getattr(sys, 'frozen', False):
    # Внутри .exe ищем сертификат во временной папке
    base_path = sys._MEIPASS
    cacert_path = os.path.join(base_path, 'certifi', 'cacert.pem')
    if os.path.exists(cacert_path):
        os.environ['SSL_CERT_FILE'] = cacert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cacert_path
else:
    # При запуске из Python
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
if __name__ == "__main__":
    create_window()