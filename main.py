from ui import create_window
import certifi
import os

os.environ['SSL_CERT_FILE'] = certifi.where()

if __name__ == "__main__":
    create_window()