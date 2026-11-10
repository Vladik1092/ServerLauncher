import hashlib
import os
import shutil
import minecraft_launcher_lib
from clouddl import grab
import urllib.request
import zipfile

from utils import is_mods_need_update

# Импортируем настройки и вспомогательные функции
from settings import (
    minecraft_directory, MODS_URL, MODPACK_VERSION, MODPACK_VERSION_FILE,
    RESOURCEPACK_URL, RESOURCEPACK_VERSION, RESOURCEPACK_VERSION_FILE,
    SHADERPACK_URL, SHADERPACK_VERSION, SHADERPACK_VERSION_FILE,
    MINECRAFT_VERSION, REQUIRED_MODS
)
from utils import fix_nested_folder, save_mods_etag


# Проверки установленного клиента

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
    try:
        installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        for v in installed_versions:
            if v["id"] == forge_id:
                return True
        return False
    except Exception:
        return False


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


def is_resourcepack_installed():
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
    marker = os.path.join(minecraft_directory, SHADERPACK_VERSION_FILE)
    if not os.path.isfile(marker):
        return False
    try:
        with open(marker, "r", encoding="utf-8") as f:
            installed_version = f.read().strip()
        return installed_version == SHADERPACK_VERSION
    except Exception:
        return False


# Установка

def install_minecraft(update_status, version=MINECRAFT_VERSION):
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


def install_forge(update_status, vanilla_version=MINECRAFT_VERSION):
    forge_version = minecraft_launcher_lib.forge.find_forge_version(vanilla_version)
    if forge_version is None:
        raise Exception(f"Forge для версии {vanilla_version} не найден")

    installed_id = minecraft_launcher_lib.forge.forge_to_installed_version(forge_version)

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

def get_file_hash(filepath):
    """Считает SHA-256 хеш файла."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def install_mods(update_status):
    mods_dir = os.path.join(minecraft_directory, "mods")
    backup_dir = os.path.join(minecraft_directory, "mods_backup")
    temp_dir = os.path.join(minecraft_directory, "mods_temp")
    zip_path = os.path.join(minecraft_directory, "mods_temp.zip")

    # 1. Запоминаем текущие моды
    current_mods = set()
    if os.path.isdir(mods_dir):
        current_mods = {f for f in os.listdir(mods_dir) if f.endswith('.jar')}

    # 2. Находим моды ИГРОКА (те, которых нет в REQUIRED_MODS)
    player_mods = current_mods - REQUIRED_MODS
    print(f"[DEBUG] player_mods: {player_mods}")

    # 3. Создаем бэкап модов игрока (ЕСЛИ ЕСТЬ)
    if player_mods:
        print(f"[DEBUG] Создаю бэкап в {backup_dir}")
        update_status(f"Сохранение модов игрока ({len(player_mods)} шт.)...")
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
        for mod in player_mods:
            src = os.path.join(mods_dir, mod)
            dst = os.path.join(backup_dir, mod)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
    else:
        print(f"[DEBUG] Модов игрока нет.")

    # 4. Проверяем, нужно ли обновление
    if not is_mods_need_update(MODS_URL):
        update_status("Моды актуальны.")
        return True

    # 5. Скачиваем архив
    update_status("Скачивание модов...")
    try:
        urllib.request.urlretrieve(MODS_URL, zip_path)
    except Exception as e:
        update_status(f"Ошибка скачивания: {e}")
        if os.path.isfile(zip_path):
            os.remove(zip_path)
        return False

    # 6. Распаковка
    update_status("Распаковка модов...")
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    except Exception as e:
        update_status(f"Ошибка распаковки: {e}")
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.isfile(zip_path):
            os.remove(zip_path)
        return False

    # 7. Исправляем вложенность
    nested_mods = os.path.join(temp_dir, "mods")
    if os.path.isdir(nested_mods):
        for item in os.listdir(nested_mods):
            src = os.path.join(nested_mods, item)
            dst = os.path.join(temp_dir, item)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            shutil.move(src, dst)
        shutil.rmtree(nested_mods)

    # 8. Возвращаем моды игрока в mods_temp/
    if player_mods:
        for mod in player_mods:
            src = os.path.join(backup_dir, mod)
            dst = os.path.join(temp_dir, mod)
            if os.path.isfile(src):
                shutil.copy2(src, dst)

    # 9. Заменяем mods на mods_temp
    if os.path.isdir(mods_dir):
        shutil.rmtree(mods_dir)
    os.rename(temp_dir, mods_dir)

    # 10. Удаляем zip
    if os.path.isfile(zip_path):
        os.remove(zip_path)

    # 11. ETag и версия
    save_mods_etag(MODS_URL)
    with open(os.path.join(minecraft_directory, MODPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(MODPACK_VERSION)

    update_status(f"Моды обновлены. Сохранено модов игрока: {len(player_mods)}")
    return True

def install_resourcepack(update_status):
    update_status("Скачивание ресурспака...")

    resourcepacks_dir = os.path.join(minecraft_directory, "resourcepacks")
    os.makedirs(resourcepacks_dir, exist_ok=True)

    grab(RESOURCEPACK_URL, resourcepacks_dir + os.sep)

    fix_nested_folder("resourcepacks")

    with open(os.path.join(minecraft_directory, RESOURCEPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(RESOURCEPACK_VERSION)

    update_status("Ресурспак установлен!")


def install_shaderpack(update_status):
    update_status("Скачивание шейдера...")
    print("[shader] старт установки")

    shaderpacks_dir = os.path.join(minecraft_directory, "shaderpacks")
    os.makedirs(shaderpacks_dir, exist_ok=True)

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