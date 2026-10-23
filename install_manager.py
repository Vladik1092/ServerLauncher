import os
import shutil
import minecraft_launcher_lib
from clouddl import grab

# Импортируем настройки и вспомогательные функции
from settings import (
    minecraft_directory, MODS_URL, MODPACK_VERSION, MODPACK_VERSION_FILE,
    RESOURCEPACK_URL, RESOURCEPACK_VERSION, RESOURCEPACK_VERSION_FILE,
    SHADERPACK_URL, SHADERPACK_VERSION, SHADERPACK_VERSION_FILE,
    MINECRAFT_VERSION
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
        version=version,
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


def install_mods(update_status):
    update_status("Скачивание и распаковка модов...")

    mods_dir = os.path.join(minecraft_directory, "mods")

    # Очищаем старые моды перед установкой
    if os.path.isdir(mods_dir):
        try:
            shutil.rmtree(mods_dir)
            print("[mods] Старая папка mods удалена.")
        except Exception as e:
            print(f"[mods] Не удалось удалить старые моды: {e}")
            raise e

    os.makedirs(mods_dir, exist_ok=True)

    # Качаем и распаковываем
    grab(MODS_URL, minecraft_directory + os.sep)

    # Чиним вложенность на всякий случай
    fix_nested_folder("mods")

    # Сохраняем ETag и версию
    save_mods_etag(MODS_URL)

    with open(os.path.join(minecraft_directory, MODPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(MODPACK_VERSION)

    update_status("Моды установлены!")


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