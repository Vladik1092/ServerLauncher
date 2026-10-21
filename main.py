import minecraft_launcher_lib
import subprocess
import sys

# Указываем папку с Майнкрафтом (по умолчанию берется стандартная)
minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()

# Получаем самую свежую версию релизного клиента
latest_version = minecraft_launcher_lib.utils.get_latest_version()["release"]

print(f"Проверка и установка версии {latest_version}...")

# Устанавливаем файлы игры (библиотеки, ресурсы, сам клиент)
minecraft_launcher_lib.install.install_minecraft_version(
    version=latest_version,
    minecraft_directory=minecraft_directory
)

# Настройки пользователя (для офлайн-режима)
options = {
    "username": "PlayerName",
    "uuid": "",  # Библиотека сгенерирует UUID сама, если оставить пустым
    "token": ""
}

# Получаем готовые аргументы командной строки для запуска игры
command = minecraft_launcher_lib.command.get_minecraft_command(
    version=latest_version,
    minecraft_directory=minecraft_directory,
    options=options
)

# Запускаем Minecraft
print("Запуск игры...")
subprocess.call(command)