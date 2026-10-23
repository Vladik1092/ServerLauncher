import os
import minecraft_launcher_lib

# Основные настройки
SERVER_IP = "135.181.170.85"
SERVER_PORT = "25674"
MINECRAFT_VERSION = "1.19.2"

MODS_URL = "https://www.dropbox.com/scl/fi/cu85n2w0ei1htlcld1e5s/mods.zip?rlkey=te5a5zg80fhd94ez1s99pgkot&st=2qegk6at&dl=1"
RESOURCEPACK_URL = "https://drive.google.com/file/d/1NSehAinMArh2YvWfR0YTif8PSKaWKDQm/view?usp=drive_link"
SHADERPACK_URL = "https://drive.google.com/file/d/1_4Otj0OjlVeh2VG0oYImnxejs6e5tw4J/view?usp=drive_link"

MODPACK_VERSION = "1.0.9"
RESOURCEPACK_VERSION = "1.0.5"
SHADERPACK_VERSION = "1.0.10"

# Пути
minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
SETTINGS_FILE = os.path.join(minecraft_directory, "launcher_settings.json")
MODPACK_VERSION_FILE = "modpack_version.txt"
RESOURCEPACK_VERSION_FILE = "resourcepack_version.txt"
SHADERPACK_VERSION_FILE = "shaderpack_version.txt"

# Цвета
COLOR_BG        = "#1e1e1e"
COLOR_PANEL     = "#3c3c3c"
COLOR_PANEL_L   = "#6a6a6a"
COLOR_TEXT      = "#ffffff"
COLOR_TEXT_DIM  = "#a0a0a0"
COLOR_BTN       = "#7a7a7a"
COLOR_BTN_HOVER = "#8f8f8f"
COLOR_BTN_DIS   = "#4a4a4a"
COLOR_ACCENT    = "#4caf50"
COLOR_ERROR     = "#e74c3c"