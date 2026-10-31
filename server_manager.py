import os
import nbtlib
from nbtlib.tag import *
from settings import minecraft_directory

def ensure_server_in_list(server_ip, server_port, server_name="ZOMBIE SGK"):
    """Добавляет сервер в servers.dat, если его там нет."""
    servers_file = os.path.join(minecraft_directory, "servers.dat")


    if not os.path.exists(servers_file):
        data = nbtlib.File({"servers": List[Compound]([])})
    else:
        try:
            data = nbtlib.load(servers_file)
        except Exception as e:
            print(f"[server] Не удалось прочитать servers.dat: {e}")
            data = nbtlib.File({"servers": List[Compound]([])})

    # Проверяем, есть ли уже наш сервер
    server_exists = False
    for server in data["servers"]:
        if str(server["ip"]) == f"{server_ip}":
            server_exists = True
            break

    if not server_exists:
        # Создаем новую запись
        new_server = Compound({
            "name": String(server_name),
            "ip": String(f"{server_ip}"),
            "icon": String(""),
            "acceptTextures": Byte(1)
        })
        data["servers"].append(new_server)

        # Сохраняем
        try:
            data.save(servers_file)
            print(f"[server] Сервер {server_name} добавлен в список.")
        except Exception as e:
            print(f"[server] Ошибка при сохранении servers.dat: {e}")
    else:
        print(f"[server] Сервер уже есть в списке.")