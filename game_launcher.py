import os
import subprocess
import minecraft_launcher_lib
from settings import minecraft_directory, SERVER_IP, SERVER_PORT
from utils import generate_offline_uuid


def launch_minecraft(version, username, ram_gb):
    offline_uuid = generate_offline_uuid(username)



    jvm_args = [
        f"-Xmx{ram_gb}G",
        f"-Xms{max(1, ram_gb // 2)}G",
        f"-Duser.dir={minecraft_directory}",
    ]

    java_path = os.path.join(
        minecraft_directory,
        "runtime", "java-runtime-gamma", "windows", "java-runtime-gamma", "bin", "javaw.exe"
    )

    if not os.path.exists(java_path):
        java_path = "javaw"  # Запасной вариант (поиск в системе)

    options = {
        "username": username,
        "uuid": offline_uuid,
        "token": "0",
        "server": SERVER_IP,
        "port": str(SERVER_PORT),
        "jvmArguments": jvm_args,
        "defaultExecutablePath": java_path,
    }

    try:
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
            version=version,
            minecraft_directory=minecraft_directory,
            options=options,
        )

        print("КОМАНДА ЗАПУСКА:")
        print(" ".join(minecraft_command))
        print("-" * 50)


        subprocess.Popen(minecraft_command)

    except Exception as e:
        print(f"ОШИБКА ПРИ ЗАПУСКЕ: {e}")
        raise e