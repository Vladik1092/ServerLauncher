import os
import shutil
import urllib.request
import zipfile
from settings import (
    minecraft_directory, MODS_URL, MODPACK_VERSION, MODPACK_VERSION_FILE,
    REQUIRED_MODS, MINECRAFT_VERSION
)
from utils import is_mods_need_update, save_mods_etag

def is_minecraft_installed(version=MINECRAFT_VERSION):
    try:
        import minecraft_launcher_lib
        installed = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        for v in installed:
            if v["id"] == version:
                return True
        return False
    except Exception as e:
        print(f"Ошибка проверки версий: {e}")
        return False

def is_forge_installed(forge_id):
    try:
        import minecraft_launcher_lib
        installed = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        for v in installed:
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
    from settings import RESOURCEPACK_VERSION, RESOURCEPACK_VERSION_FILE
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
    from settings import SHADERPACK_VERSION, SHADERPACK_VERSION_FILE
    marker = os.path.join(minecraft_directory, SHADERPACK_VERSION_FILE)
    if not os.path.isfile(marker):
        return False
    try:
        with open(marker, "r", encoding="utf-8") as f:
            installed_version = f.read().strip()
        return installed_version == SHADERPACK_VERSION
    except Exception:
        return False

def install_minecraft(update_status, version=MINECRAFT_VERSION):
    import minecraft_launcher_lib

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
    import minecraft_launcher_lib

    forge_version = minecraft_launcher_lib.forge.find_forge_version(vanilla_version)
    if forge_version is None:
        raise Exception(f"Фордж для версии {vanilla_version} не найден")

    installed_id = minecraft_launcher_lib.forge.forge_to_installed_version(forge_version)
    if is_forge_installed(installed_id):
        update_status(f"Фордж уже установлен: {installed_id}")
        return installed_id

    if not minecraft_launcher_lib.forge.supports_automatic_install(forge_version):
        raise Exception(f"Фордж {forge_version} не поддерживает автоматическую установку")

    def set_status(status: str):
        update_status(status)

    def set_progress(progress: int):
        if max_progress > 0:
            percent = int(progress / max_progress * 100)
            update_status(f"Установка Фордж... {percent}%")

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
    mods_dir = os.path.join(minecraft_directory, "mods")
    backup_dir = os.path.join(minecraft_directory, "mods_backup")
    temp_dir = os.path.join(minecraft_directory, "mods_temp")
    zip_path = os.path.join(minecraft_directory, "mods_temp.zip")

    # 1. Запоминаем текущие моды
    current_mods = set()
    if os.path.isdir(mods_dir):
        current_mods = {f for f in os.listdir(mods_dir) if f.endswith('.jar')}
    print(f"[DEBUG] current_mods: {current_mods}")

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
        update_status(f"Моды игрока сохранены в mods_backup/. Они НЕ включены (чтобы не было конфликтов).")
    else:
        print(f"[DEBUG] Модов игрока нет.")

    # 4. Проверяем, нужно ли обновление
    if not is_mods_need_update(MODS_URL):
        update_status("Моды актуальны.")
        # Даже если не нужно обновление, НО есть моды игрока — удаляем их из mods, чтобы не было конфликтов
        if player_mods:
            for mod in player_mods:
                file_path = os.path.join(mods_dir, mod)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            update_status("Моды игрока отключены (перемещены в mods_backup/).")
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
            bad_file = zip_ref.testzip()
            if bad_file is not None:
                raise Exception(f"Поврежденный файл: {bad_file}")
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

    # 8. Удаляем старую папку mods (и моды игрока в ней, они уже в бэкапе)
    if os.path.isdir(mods_dir):
        shutil.rmtree(mods_dir)

    # 9. Переименовываем temp в mods
    os.rename(temp_dir, mods_dir)

    # 10. Удаляем zip
    if os.path.isfile(zip_path):
        os.remove(zip_path)

    # 11. ETag и версия
    save_mods_etag(MODS_URL)
    with open(os.path.join(minecraft_directory, MODPACK_VERSION_FILE), "w", encoding="utf-8") as f:
        f.write(MODPACK_VERSION)

    # 12. Сообщение
    if player_mods:
        update_status(f"Моды обновлены. Моды игрока ({len(player_mods)} шт.) в mods_backup/ (отключены).")
    else:
        update_status("Моды обновлены.")
    return True

def install_resourcepack(update_status):
    from settings import RESOURCEPACK_URL, RESOURCEPACK_VERSION, RESOURCEPACK_VERSION_FILE
    from clouddl import grab
    from utils import fix_nested_folder

    resourcepacks_dir = os.path.join(minecraft_directory, "resourcepacks")
    os.makedirs(resourcepacks_dir, exist_ok=True)

    update_status("Скачивание ресурспака...")
    grab(RESOURCEPACK_URL, os.path.join(resourcepacks_dir, "server_pack.zip"))

    fix_nested_folder("resourcepacks")

    marker = os.path.join(minecraft_directory, RESOURCEPACK_VERSION_FILE)
    with open(marker, "w", encoding="utf-8") as f:
        f.write(RESOURCEPACK_VERSION)

    update_status("Ресурспак установлен.")

def install_shaderpack(update_status):
    from settings import SHADERPACK_URL, SHADERPACK_VERSION, SHADERPACK_VERSION_FILE
    from clouddl import grab
    from utils import fix_nested_folder

    shaderpacks_dir = os.path.join(minecraft_directory, "shaderpacks")
    os.makedirs(shaderpacks_dir, exist_ok=True)

    update_status("Скачивание шейдера...")
    grab(SHADERPACK_URL, os.path.join(shaderpacks_dir, "server_shader.zip"))

    fix_nested_folder("shaderpacks")

    marker = os.path.join(minecraft_directory, SHADERPACK_VERSION_FILE)
    with open(marker, "w", encoding="utf-8") as f:
        f.write(SHADERPACK_VERSION)

    update_status("Шейдер установлен.")