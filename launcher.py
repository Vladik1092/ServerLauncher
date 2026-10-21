import minecraft_launcher_lib
import subprocess
import tkinter as tk
import threading
import os
import shutil
import hashlib
import uuid
import json
import psutil
import urllib.request
import io
import gdown
from clouddl import grab
import traceback

import urllib.request

def fix_forge_json(forge_id):
    """Автоматически исправляет JSON Forge для совместимости с библиотекой."""
    version_dir = os.path.join(minecraft_directory, "versions", forge_id)
    json_path = os.path.join(version_dir, f"{forge_id}.json")

    if not os.path.isfile(json_path):
        print(f"[forge-fix] Файл {json_path} не найден.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Проверяем, есть ли проблема (ключ "values" вместо "value")
        arguments = data.get("arguments", {})
        needs_fix = False

        for section in ["jvm", "game"]:
            if section in arguments:
                for item in arguments[section]:
                    if isinstance(item, dict) and "values" in item:
                        needs_fix = True
                        break

        if not needs_fix:
            print(f"[forge-fix] Файл {forge_id}.json уже в порядке.")
            return

        print(f"[forge-fix] Исправляем {forge_id}.json...")

        # Переписываем JVM аргументы
        arguments["jvm"] = [
            "-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump",
            "-Dos.name=Windows 10",
            "-Dos.version=10.0",
            "-Xss1M",
            "-Djava.library.path=${natives_directory}",
            "-Dminecraft.launcher.brand=${launcher_name}",
            "-Dminecraft.launcher.version=${launcher_version}",
            "-cp",
            "${classpath}",
            "-Djava.net.preferIPv6Addresses=system",
            "-DignoreList=bootstraplauncher,securejarhandler,asm-commons,asm-util,asm-analysis,asm-tree,asm,JarJarFileSystems,client-extra,fmlcore,javafmllanguage,lowcodelanguage,mclanguage,forge-,${version_name}.jar",
            "-DmergeModules=jna-5.12.1.jar,jna-platform-5.12.1.jar",
            "-DlibraryDirectory=${library_directory}",
            "-p",
            "${library_directory}/cpw/mods/bootstraplauncher/1.1.2/bootstraplauncher-1.1.2.jar${classpath_separator}${library_directory}/cpw/mods/securejarhandler/2.1.4/securejarhandler-2.1.4.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-commons/9.7.1/asm-commons-9.7.1.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-util/9.7.1/asm-util-9.7.1.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-analysis/9.7.1/asm-analysis-9.7.1.jar${classpath_separator}${library_directory}/org/ow2/asm/asm-tree/9.7.1/asm-tree-9.7.1.jar${classpath_separator}${library_directory}/org/ow2/asm/asm/9.7.1/asm-9.7.1.jar${classpath_separator}${library_directory}/net/minecraftforge/JarJarFileSystems/0.3.16/JarJarFileSystems-0.3.16.jar",
            "--add-modules",
            "ALL-MODULE-PATH",
            "--add-opens",
            "java.base/java.util.jar=cpw.mods.securejarhandler",
            "--add-opens",
            "java.base/java.lang.invoke=cpw.mods.securejarhandler",
            "--add-exports",
            "java.base/sun.security.util=cpw.mods.securejarhandler",
            "--add-exports",
            "jdk.naming.dns/com.sun.jndi.dns=java.naming"
        ]

        # Переписываем игровые аргументы
        arguments["game"] = [
            "--username", "${auth_player_name}",
            "--version", "${version_name}",
            "--gameDir", "${game_directory}",
            "--assetsDir", "${assets_root}",
            "--assetIndex", "${assets_index_name}",
            "--uuid", "${auth_uuid}",
            "--accessToken", "${auth_access_token}",
            "--clientId", "${clientid}",
            "--xuid", "${auth_xuid}",
            "--userType", "${user_type}",
            "--versionType", "${version_type}",
            "--launchTarget", "forgeclient",
            "--fml.forgeVersion", "43.5.1",  # Можно брать из forge_id
            "--fml.mcVersion", "1.19.2",
            "--fml.forgeGroup", "net.minecraftforge",
            "--fml.mcpVersion", "20220805.130853"
        ]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[forge-fix] Файл {forge_id}.json успешно исправлен.")

    except Exception as e:
        print(f"[forge-fix] Ошибка при исправлении JSON: {e}")

def get_dropbox_file_etag(url):
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=10) as response:
            etag = response.headers.get('ETag')
            if not etag:
                etag = response.headers.get('Last-Modified', '') + response.headers.get('Content-Length', '')
            return etag
    except Exception as e:
        print(f"[dropbox] Ошибка при проверке ETag: {e}")
        return None

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

RESOURCEPACK_URL = "https://drive.google.com/file/d/1NSehAinMArh2YvWfR0YTif8PSKaWKDQm/view?usp=drive_link"
SHADERPACK_URL = "https://drive.google.com/file/d/1_4Otj0OjlVeh2VG0oYImnxejs6e5tw4J/view?usp=drive_link"

# Версии для отслеживания обновлений
RESOURCEPACK_VERSION = "1.0.5"
SHADERPACK_VERSION = "1.0.10"
RESOURCEPACK_VERSION_FILE = "resourcepack_version.txt"
SHADERPACK_VERSION_FILE = "shaderpack_version.txt"


MODS_URL = "https://www.dropbox.com/scl/fi/cu85n2w0ei1htlcld1e5s/mods.zip?rlkey=te5a5zg80fhd94ez1s99pgkot&st=qyfr80y6&dl=1"
MODPACK_VERSION = "1.0.9"
MODPACK_VERSION_FILE = "modpack_version.txt"
SERVER_IP = "135.181.170.85"
SERVER_PORT = "25674"
MINECRAFT_VERSION = "1.19.2"

minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
SETTINGS_FILE = os.path.join(minecraft_directory, "launcher_settings.json")



COLOR_BG        = "#1e1e1e"
COLOR_PANEL     = "#3c3c3c"
COLOR_PANEL_D   = "#2a2a2a"
COLOR_PANEL_L   = "#6a6a6a"
COLOR_TEXT      = "#ffffff"
COLOR_TEXT_DIM  = "#a0a0a0"
COLOR_BTN       = "#7a7a7a"
COLOR_BTN_HOVER = "#8f8f8f"
COLOR_BTN_DIS   = "#4a4a4a"
COLOR_ACCENT    = "#4caf50"
COLOR_ERROR     = "#e74c3c"

ETAG_FILE = os.path.join(minecraft_directory, "mods_etag.txt")

def fix_nested_folder(folder_name):
    """Убирает ЛЮБУЮ вложенность и старые _dup-папки внутри .minecraft/<folder>/"""
    base_dir = os.path.join(minecraft_directory, folder_name)

    if not os.path.isdir(base_dir):
        return

    # удаляем все старые папки вида <folder>_dup*
    for item in os.listdir(base_dir):
        full = os.path.join(base_dir, item)
        if os.path.isdir(full) and item.startswith(folder_name + "_dup"):
            try:
                shutil.rmtree(full)
                print(f"[fix] удалена старая папка {item}")
            except Exception as e:
                print(f"[fix] не смог удалить {item}: {e}")

    # чиним вложенность в цикле
    safety = 0
    while safety < 10:  # защита от бесконечного цикла
        safety += 1
        nested = os.path.join(base_dir, folder_name)

        if not os.path.isdir(nested):
            break

        print(f"[fix] найден вложенный {folder_name}, выпрямляю...")

        for item in os.listdir(nested):
            src = os.path.join(nested, item)
            dst = os.path.join(base_dir, item)

            if os.path.exists(dst):
                # Если такой уже есть — удаляем дубликат из вложенной папки
                if os.path.isdir(src):
                    shutil.rmtree(src)
                else:
                    os.remove(src)
                continue

            shutil.move(src, dst)

        # Удаляем опустевшую обёртку
        try:
            os.rmdir(nested)
            print(f"[fix] удалена обёртка {nested}")
        except OSError as e:
            print(f"[fix] не смог удалить обёртку {nested}: {e}")
            break

def is_resourcepack_installed():
    """Проверяет, актуален ли ресурспак."""
    marker = os.path.join(minecraft_directory, RESOURCEPACK_VERSION_FILE)
    if not os.path.isfile(marker):
        return False
    try:
        with open(marker, "r", encoding="utf-8") as f:
            installed_version = f.read().strip()
        return installed_version == RESOURCEPACK_VERSION
    except Exception:
        return False


def is_shaderpack_installed():
    """Проверяет, актуален ли шейдер."""
    marker = os.path.join(minecraft_directory, SHADERPACK_VERSION_FILE)
    if not os.path.isfile(marker):
        return False
    try:
        with open(marker, "r", encoding="utf-8") as f:
            installed_version = f.read().strip()
        return installed_version == SHADERPACK_VERSION
    except Exception:
        return False


def install_resourcepack():
    """Скачивает ресурспак в папку resourcepacks."""
    update_status("Скачивание ресурспака...")

    resourcepacks_dir = os.path.join(minecraft_directory, "resourcepacks")
    os.makedirs(resourcepacks_dir, exist_ok=True)

    grab(RESOURCEPACK_URL, resourcepacks_dir + os.sep)

    # Чиним вложенность, если она появилась
    fix_nested_folder("resourcepacks")

    with open(os.path.join(minecraft_directory, RESOURCEPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(RESOURCEPACK_VERSION)

    update_status("Ресурспак установлен!")


def install_shaderpack():
    update_status("Скачивание шейдера...")
    print("[shader] старт установки")

    shaderpacks_dir = os.path.join(minecraft_directory, "shaderpacks")
    os.makedirs(shaderpacks_dir, exist_ok=True)
    print(f"[shader] папка готова: {shaderpacks_dir}")

    try:
        grab(SHADERPACK_URL, shaderpacks_dir + os.sep)
        print("[shader] grab завершён")
    except Exception as e:
        print(f"[shader] ОШИБКА в grab: {e}")
        raise

    try:
        fix_nested_folder("shaderpacks")
        print("[shader] fix завершён")
    except Exception as e:
        print(f"[shader] ОШИБКА в fix: {e}")

    with open(os.path.join(minecraft_directory, SHADERPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(SHADERPACK_VERSION)

    update_status("Шейдер установлен!")

def set_icon_from_url(root, url):
    """Скачивает иконку по URL и ставит её на окно и в панель задач."""
    try:
        #
        with urllib.request.urlopen(url, timeout=10) as response:
            raw_data = response.read()


        icon_img = Image.open(io.BytesIO(raw_data))
        icon_img = icon_img.resize((64, 64))
        icon_photo = ImageTk.PhotoImage(icon_img)


        root.wm_iconphoto(True, icon_photo)


        root._icon_ref = icon_photo

        return True
    except Exception as e:
        print(f"Не удалось установить иконку: {e}")
        return False

# Загрузка и сохранение настроек

def load_settings():
    default = {"nickname": "", "ram_gb": 4}
    if not os.path.isfile(SETTINGS_FILE):
        return default
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "nickname": str(data.get("nickname", default["nickname"])),
            "ram_gb": int(data.get("ram_gb", default["ram_gb"])),
        }
    except (json.JSONDecodeError, ValueError, KeyError):
        return default


def save_settings(nickname, ram_gb):
    data = {"nickname": nickname, "ram_gb": ram_gb}
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Не удалось сохранить настройки: {e}")


# Вспомогательный функции

def generate_offline_uuid(username):
    md5 = hashlib.md5(("OfflinePlayer:" + username).encode("utf-8")).hexdigest()
    offline_uuid = str(uuid.UUID(md5, version=3))
    return offline_uuid.replace("-", "")


def get_max_ram_gb():
    vm = psutil.virtual_memory()
    total_gb = vm.total / (1024 ** 3)
    reserve_gb = max(2, total_gb * 0.25)
    max_gb = max(1, int(total_gb - reserve_gb))
    return max_gb


def is_modpack_installed():
    marker = os.path.join(minecraft_directory, MODPACK_VERSION_FILE)
    if not os.path.isfile(marker):
        return False
    try:
        with open(marker, "r", encoding="utf-8") as f:
            installed_version = f.read().strip()
        return installed_version == MODPACK_VERSION
    except Exception:
        return False


def is_minecraft_installed(version=MINECRAFT_VERSION):
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        for v in installed_versions:
            if v["id"] == version:
                return True
        return False
    except Exception as e:
        print(f"Ошибка проверки версий: {e}")
        return False


def is_forge_installed(forge_id):
    """Проверяет, установлен ли уже конкретный forge-профиль."""
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        for v in installed_versions:
            if v["id"] == forge_id:
                return True
        return False
    except Exception:
        return False


# Установка

def install_minecraft(version=MINECRAFT_VERSION):
    def set_status(status: str):
        update_status(status)

    def set_progress(progress: int):
        if max_progress > 0:
            percent = int(progress / max_progress * 100)
            update_status(f"Загрузка Minecraft... {percent}%")

    def set_max_progress(max_p: int):
        nonlocal max_progress
        max_progress = max_p

    max_progress = 0
    callback = {"setStatus": set_status, "setProgress": set_progress, "setMax": set_max_progress}

    minecraft_launcher_lib.install.install_minecraft_version(
        versionid=version,
        minecraft_directory=minecraft_directory,
        callback=callback,
    )


def get_forge_id(vanilla_version=MINECRAFT_VERSION):
    forge_version = minecraft_launcher_lib.forge.find_forge_version(vanilla_version)
    if forge_version is None:
        raise Exception(f"Forge для версии {vanilla_version} не найден")
    return forge_version, minecraft_launcher_lib.forge.forge_to_installed_version(forge_version)


def install_forge(vanilla_version=MINECRAFT_VERSION):
    forge_version, installed_id = get_forge_id(vanilla_version)

    if is_forge_installed(installed_id):
        update_status(f"Forge уже установлен: {installed_id}")
        return installed_id

    if not minecraft_launcher_lib.forge.supports_automatic_install(forge_version):
        raise Exception(f"Forge {forge_version} не поддерживает автоматическую установку")

    def set_status(status: str):
        update_status(status)

    def set_progress(progress: int):
        if max_progress > 0:
            percent = int(progress / max_progress * 100)
            update_status(f"Установка Forge... {percent}%")

    def set_max_progress(max_p: int):
        nonlocal max_progress
        max_progress = max_p

    max_progress = 0
    callback = {"setStatus": set_status, "setProgress": set_progress, "setMax": set_max_progress}

    minecraft_launcher_lib.forge.install_forge_version(
        forge_version,
        minecraft_directory,
        callback=callback,
    )
    return installed_id

def is_mods_need_update():
    """Проверяет, нужно ли обновлять моды, сравнивая ETag."""
    etag_file = os.path.join(minecraft_directory, "mods_etag.txt")
    current_etag = get_dropbox_file_etag(MODS_URL)

    if not current_etag:
        print("[mods] Не удалось получить ETag. Будем качать на всякий случай.")
        return True

    if not os.path.isfile(etag_file):
        print("[mods] Файла с ETag нет. Качаем моды.")
        return True

    try:
        with open(etag_file, "r", encoding="utf-8") as f:
            saved_etag = f.read().strip()
    except Exception:
        return True

    if current_etag == saved_etag:
        print("[mods] ETag совпадает. Моды актуальны.")
        return False
    else:
        print(f"[mods] ETag изменился! Старый: {saved_etag}, Новый: {current_etag}")
        return True

def install_mods():
    update_status("Скачивание и распаковка модов...")

    mods_dir = os.path.join(minecraft_directory, "mods")

    # Очищаем старые моды перед установкой
    if os.path.isdir(mods_dir):
        try:
            shutil.rmtree(mods_dir)
            print("[mods] Старая папка mods удалена.")
        except Exception as e:
            print(f"[mods] Не удалось удалить старые моды: {e}")

    os.makedirs(mods_dir, exist_ok=True)

    # Качаем и распаковываем
    grab(MODS_URL, minecraft_directory + os.sep)

    #Сохраняем etag
    new_etag = get_dropbox_file_etag(MODS_URL)
    if new_etag:
        etag_file = os.path.join(minecraft_directory, "mods_etag.txt")
        with open(etag_file, "w", encoding="utf-8") as f:
            f.write(new_etag)
        print(f"[mods] ETag сохранён: {new_etag}")

    # Оставляем запись версии
    with open(os.path.join(minecraft_directory, MODPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(MODPACK_VERSION)

    update_status("Моды установлены!")

# Запуск

def launch_minecraft(version=MINECRAFT_VERSION, username="Player", ram_gb=4):
    offline_uuid = generate_offline_uuid(username)

    jvm_args = [
        f"-Xmx{ram_gb}G",
        f"-Xms{max(1, ram_gb // 2)}G",
    ]

    options = {
        "username": username,
        "uuid": offline_uuid,
        "token": "0",
        "gameDirectory": minecraft_directory,
        "server": SERVER_IP,
        "port": str(SERVER_PORT),
        "jvmArguments": jvm_args,
    }

    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
        version=version,
        minecraft_directory=minecraft_directory,
        options=options,
    )
    print("КОМАНДА ЗАПУСКА:")
    print(" ".join(minecraft_command))
    print("-" * 50)

    subprocess.Popen(minecraft_command)


# Логика игры

def play_thread():
    nickname = entry_nickname.get().strip()
    if not nickname:
        update_status("Введите никнейм!")
        return

    ram_gb = ram_var.get()
    save_settings(nickname, ram_gb)

    btn_play.config_state(tk.DISABLED)

    try:
        if is_minecraft_installed(MINECRAFT_VERSION):
            update_status(f"Minecraft {MINECRAFT_VERSION} уже установлен.")
        else:
            update_status(f"Minecraft {MINECRAFT_VERSION} не найден. Устанавливаем...")
            install_minecraft(MINECRAFT_VERSION)
            update_status("Minecraft установлен!")

        forge_id = install_forge(MINECRAFT_VERSION)
        update_status(f"Forge готов: {forge_id}")

        fix_forge_json(forge_id)

        if is_mods_need_update():
            install_mods()
        else:
            update_status("Моды актуальны (ETag совпадает).")

        if is_resourcepack_installed():
            update_status("Ресурспак актуален.")
        else:
            install_resourcepack()

        # --- ШЕЙДЕР ---
        if is_shaderpack_installed():
            update_status("Шейдер актуален.")
        else:
            install_shaderpack()

        update_status("Запуск игры...")
        launch_minecraft(version=forge_id, username=nickname, ram_gb=ram_gb)
        update_status(f"Игра запущена для {nickname}! (Если игра запустилась не сразу после этого сообщения, просто немного подождите)")

    except Exception as e:
        update_status(f"Ошибка: {e}")
        print(f"Ошибка: {e}")
        traceback.print_exc()
    finally:
        btn_play.config_state(tk.NORMAL)


def on_play_click():
    th = threading.Thread(target=play_thread, daemon=True)
    th.start()



def draw_mc_button(w, h, bg, border_dark="#2a2a2a", border_light="#9a9a9a"):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=bg, outline=border_dark, width=2)
    d.line([(1, 1), (w - 2, 1)], fill=border_light, width=1)
    d.line([(1, 1), (1, h - 2)], fill=border_light, width=1)
    return ImageTk.PhotoImage(img)


def make_mc_button(parent, text, command, width=200, height=44, font_size=14, bg=COLOR_BG):
    normal_img = draw_mc_button(width, height, COLOR_BTN)
    hover_img  = draw_mc_button(width, height, COLOR_BTN_HOVER)
    dis_img    = draw_mc_button(width, height, COLOR_BTN_DIS)

    btn = tk.Label(
        parent,
        text=text,
        image=normal_img,
        compound="center",
        fg=COLOR_TEXT,
        font=("Arial", font_size, "bold"),
        bg=bg,
        cursor="hand2",
        bd=0,
    )
    btn._img_normal = normal_img
    btn._img_hover  = hover_img
    btn._img_dis    = dis_img
    btn._enabled    = True
    btn._command    = command

    def on_enter(_):
        if btn._enabled:
            btn.config(image=hover_img)

    def on_leave(_):
        if btn._enabled:
            btn.config(image=normal_img)

    def on_click(_):
        if btn._enabled and btn._command:
            btn._command()

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<Button-1>", on_click)

    def set_state(state):
        if state == tk.DISABLED:
            btn._enabled = False
            btn.config(image=dis_img, cursor="")
        else:
            btn._enabled = True
            btn.config(image=normal_img, cursor="hand2")

    btn.config_state = set_state
    return btn


# Tkinter интерфейс

root = tk.Tk()
root.title("ИС-25-05 Launcher")
root.geometry("900x660")
root.resizable(False, False)
root.configure(bg=COLOR_BG)
ICON_URL = "https://img.icons8.ru/?size=100&id=TUH60vMtAmJ0&format=png&color=000000"  # прямая ссылка на PNG/JPG/ICO
set_icon_from_url(root, ICON_URL)

# Фоновое изображение, если есть
bg_image = None
if PIL_AVAILABLE and os.path.isfile("background.png"):
    try:
        bg_pil = Image.open("background.png").resize((900, 660))
        overlay = Image.new("RGBA", bg_pil.size, (0, 0, 0, 130))
        bg_pil = Image.alpha_composite(bg_pil.convert("RGBA"), overlay).convert("RGB")
        bg_image = ImageTk.PhotoImage(bg_pil)
        bg_label = tk.Label(root, image=bg_image, bd=0)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Не удалось загрузить фон: {e}")


def update_status(text):
    lb.config(text=text)
    root.update_idletasks()


# Главная панель
main_frame = tk.Frame(root, bg=COLOR_PANEL, bd=0)
main_frame.place(relx=0.5, rely=0.5, anchor="center", width=580, height=580)


tk.Frame(main_frame, bg=COLOR_PANEL_L, height=2).pack(fill="x", side="top")
tk.Frame(main_frame, bg=COLOR_PANEL_L, width=2).pack(fill="y", side="left")

inner = tk.Frame(main_frame, bg=COLOR_PANEL)
inner.pack(fill="both", expand=True, padx=26, pady=22)


tk.Label(
    inner, text="ZOMBIE IS-25-05",
    font=("Arial", 22, "bold"),
    fg=COLOR_ACCENT, bg=COLOR_PANEL,
).pack(pady=(0, 2))

tk.Label(
    inner, text="Launcher • 1.1",
    font=("Arial", 10),
    fg=COLOR_TEXT_DIM, bg=COLOR_PANEL,
).pack(pady=(0, 18))


saved = load_settings()


tk.Label(
    inner, text="Никнейм",
    font=("Arial", 11, "bold"),
    fg=COLOR_TEXT, bg=COLOR_PANEL, anchor="w",
).pack(fill="x")

entry_nickname = tk.Entry(
    inner, width=40, font=("Arial", 12),
    bg="#2b2b2b", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
    relief="flat", bd=0,
)
entry_nickname.insert(0, saved["nickname"])
entry_nickname.pack(fill="x", ipady=6, pady=(3, 14))


max_ram = get_max_ram_gb()
default_ram = min(saved["ram_gb"], max_ram)
default_ram = max(1, default_ram)

ram_header = tk.Frame(inner, bg=COLOR_PANEL)
ram_header.pack(fill="x")

tk.Label(
    ram_header, text="Оперативная память",
    font=("Arial", 11, "bold"),
    fg=COLOR_TEXT, bg=COLOR_PANEL,
).pack(side="left")

tk.Label(
    ram_header, text=f"(макс. {max_ram} ГБ)",
    font=("Arial", 9),
    fg=COLOR_TEXT_DIM, bg=COLOR_PANEL,
).pack(side="right")

ram_var = tk.IntVar(value=default_ram)
spin_ram = tk.Spinbox(
    inner, from_=1, to=max_ram, textvariable=ram_var, width=6,
    font=("Arial", 12), bg="#2b2b2b", fg=COLOR_TEXT,
    buttonbackground=COLOR_BTN, relief="flat", bd=0,
    insertbackground=COLOR_TEXT,
)
spin_ram.pack(anchor="w", pady=(3, 14), ipady=4)


tk.Label(
    inner,
    text=f"Папка игры: {minecraft_directory}",
    font=("Arial", 8),
    fg=COLOR_TEXT_DIM, bg=COLOR_PANEL,
    wraplength=520, justify="left",
).pack(fill="x", pady=(0, 10))


status_frame = tk.Frame(inner, bg="#1a1a1a", bd=0)
status_frame.pack(fill="both", expand=True, pady=(0, 14))

lb = tk.Label(
    status_frame,
    text="Готов к запуску.",
    fg="#8be9fd", bg="#1a1a1a",
    font=("Consolas", 9),
    anchor="w", justify="left",
    wraplength=520,
)
lb.pack(fill="x", padx=12, pady=10)


if PIL_AVAILABLE:
    btn_play = make_mc_button(
        inner, "ИГРАТЬ",
        command=on_play_click,
        width=520, height=52, font_size=18,
        bg=COLOR_PANEL,
    )
else:

    btn_play = tk.Button(
        inner, text="ИГРАТЬ", command=on_play_click,
        width=40, height=3, font=("Arial", 16, "bold"),
    )
    def _set_state(state):
        btn_play.config(state=state)
    btn_play.config_state = _set_state

btn_play.pack(pady=(2, 0))

tk.Label(
    inner,
    text=f"Лаунчер не ставит текстурпаки и шейдеры по умолчанию, это сделано в угоду оптимизации на слабых устройствах.\n"
         f"Если вы уверены, что ваш компьютер выдержит текстурпаки и шейдеры, то смело включайте их.",
    font=("Arial", 12),
    fg=COLOR_TEXT_DIM, bg=COLOR_PANEL,
    wraplength=520, justify="left",
).pack(fill="x", pady=(0, 10))

def on_closing():
    save_settings(entry_nickname.get().strip(), ram_var.get())
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()