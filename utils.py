import os
import json
import hashlib
import uuid
import psutil
import urllib.request
import platform
import shutil

# Импортируем пути и константы из файла настроек
from settings import minecraft_directory, SETTINGS_FILE

# Настройки

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

# Системные функции

def generate_offline_uuid(username):
    """Генерирует UUID для оффлайн-режима."""
    md5 = hashlib.md5(("OfflinePlayer:" + username).encode("utf-8")).hexdigest()
    offline_uuid = str(uuid.UUID(md5, version=3))
    return offline_uuid.replace("-", "")


def get_max_ram_gb():
    """Вычисляет максимально доступное ОЗУ (оставляя 25% системе)."""
    vm = psutil.virtual_memory()
    total_gb = vm.total / (1024 ** 3)
    reserve_gb = max(2, total_gb * 0.25)
    max_gb = max(1, int(total_gb - reserve_gb))
    return max_gb


def get_java_path():
    """Определяет команду для запуска Java в зависимости от ОС."""
    system = platform.system()
    if system == "Windows":
        return "javaw"  # Windows обычно ищет javaw в PATH
    elif system == "Linux":
        return "java"  # Linux
    elif system == "Darwin":  # macOS
        return "/usr/bin/java"
    return "java"  # Fallback

# Работа с папками

def fix_nested_folder(folder_name):
    """Убирает ЛЮБУЮ вложенность и старые _dup-папки внутри .minecraft/<folder>/"""
    base_dir = os.path.join(minecraft_directory, folder_name)

    if not os.path.isdir(base_dir):
        return

    # Шаг 1: удаляем все старые папки вида <folder>_dup*
    for item in os.listdir(base_dir):
        full = os.path.join(base_dir, item)
        if os.path.isdir(full) and item.startswith(folder_name + "_dup"):
            try:
                shutil.rmtree(full)
                print(f"[fix] удалена старая папка {item}")
            except Exception as e:
                print(f"[fix] не смог удалить {item}: {e}")

    # Шаг 2: чиним вложенность в цикле
    safety = 0
    while safety < 10:
        safety += 1
        nested = os.path.join(base_dir, folder_name)

        if not os.path.isdir(nested):
            break

        print(f"[fix] найден вложенный {folder_name}, выпрямляю...")

        for item in os.listdir(nested):
            src = os.path.join(nested, item)
            dst = os.path.join(base_dir, item)

            if os.path.exists(dst):

                if os.path.isdir(src):
                    shutil.rmtree(src)
                else:
                    os.remove(src)
                continue

            shutil.move(src, dst)


        try:
            os.rmdir(nested)
            print(f"[fix] удалена обёртка {nested}")
        except OSError as e:
            print(f"[fix] не смог удалить обёртку {nested}: {e}")
            break

# СЕТЕВЫЕ ФУНКЦИИ (Dropbox / ETag)

def get_dropbox_file_etag(url):
    """Получает ETag файла из Dropbox без его скачивания."""
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


def is_mods_need_update(mods_url):
    """Проверяет, нужно ли обновлять моды, сравнивая ETag."""
    etag_file = os.path.join(minecraft_directory, "mods_etag.txt")
    current_etag = get_dropbox_file_etag(mods_url)

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


def save_mods_etag(mods_url):
    """Сохраняет текущий ETag модов в файл."""
    etag_file = os.path.join(minecraft_directory, "mods_etag.txt")
    new_etag = get_dropbox_file_etag(mods_url)
    if new_etag:
        with open(etag_file, "w", encoding="utf-8") as f:
            f.write(new_etag)
        print(f"[mods] ETag сохранён: {new_etag}")