import os
import minecraft_launcher_lib

# Основные настройки
SERVER_IP = "zombieland.gomc.fun"
SERVER_PORT = "25674"
MINECRAFT_VERSION = "1.19.2"

MODS_URL = "https://www.dropbox.com/scl/fi/cu85n2w0ei1htlcld1e5s/mods.zip?rlkey=te5a5zg80fhd94ez1s99pgkot&st=2qegk6at&dl=1"
RESOURCEPACK_URL = "https://drive.google.com/uc?export=download&id=1NSehAinMArh2YvWfR0YTif8PSKaWKDQm"
SHADERPACK_URL = "https://drive.google.com/uc?export=download&id=1_4Otj0OjlVeh2VG0oYImnxejs6e5tw4J"

MODPACK_VERSION = "1.0.9"
RESOURCEPACK_VERSION = "1.0.6"
SHADERPACK_VERSION = "1.0.11"

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

REQUIRED_MODS = {
    "adaptive_performance_tweaks_1.19.2-11.6.1.jar",
    "adaptive_performance_tweaks_core_1.19.2-11.6.1.jar",
    "adaptive_performance_tweaks_gamerules_1.19.2-11.6.1.jar",
    "adaptive_performance_tweaks_items_1.19.2-11.6.1.jar",
    "adaptive_performance_tweaks_player_1.19.2-11.6.1.jar",
    "adaptive_performance_tweaks_spawn_1.19.2-11.6.1.jar",
    "blur-forge-3.1.1-mc1.19.2.jar",
    "cfm-7.0.0-pre35-1.19.2.jar",
    "coroutil-forge-1.19.2-1.3.6.jar",
    "easy_npc_config_ui-forge-1.19.2-6.0.3.jar",
    "easy_npc-forge-1.19.2-6.0.3.jar",
    "ferritecore-5.0.3-forge.jar",
    "geckolib-forge-1.19-3.1.40.jar",
    "gravestone-forge-1.19.2-1.0.24.jar",
    "Immersive Vehicles-1.19.2-24.0.0.jar",
    "incontrol-1.19-7.1.18.jar",
    "Infectious-forge-1.19.2-1.7.jar",
    "jei-1.19.2-forge-11.68.0.1086.jar",
    "journeymap-1.19.2-5.9.8-forge.jar",
    "mcw-doors-1.1.5-mc1.19.2forge.jar",
    "mcw-mcwfences-1.2.1-mc1.19.2forge.jar",
    "mcw-mcwstairs-1.0.2-mc1.19.2forge.jar",
    "mcw-mcwwindows-2.4.2-mc1.19.2forge.jar",
    "modernfix-forge-5.18.1+mc1.19.2.jar",
    "MTS Official Pack-1.19.2-V29.jar",
    "OAmP-1.19.2-V3.jar",
    "oculus-mc1.19.2-1.6.9a.jar",
    "ParCool-1.19.2-3.4.3.3.jar",
    "rubidium-mc1.19.2-0.6.2c.jar",
    "skin_changer-1.19-0.5.3.jar",
    "sophisticatedbackpacks-1.19.2-3.20.2.1035.jar",
    "sophisticatedcore-1.19.2-0.6.4.730.jar",
    "tacz-1.19.2-1.1.4-hotfix-all.jar",
    "tacz-clonefix-1.19.2-1.0.0.jar",
    "ToughAsNails-1.19-8.0.0.78.jar",
    "voicechat-forge-1.19.2-2.6.24.jar",
    "worldedit-mod-7.2.12.jar",
    "zombieawareness-1.19.2-1.12.3.jar",
}

