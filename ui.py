import os
import sys
import threading
import urllib.request
import io
import tkinter as tk
from tkinter import messagebox

try:
    from PIL import Image, ImageTk, ImageDraw

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from settings import (
    minecraft_directory, MINECRAFT_VERSION, MODS_URL,
    COLOR_BG, COLOR_PANEL, COLOR_PANEL_L, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_BTN, COLOR_BTN_HOVER, COLOR_BTN_DIS, COLOR_ACCENT
)
from utils import (
    load_settings, save_settings, get_max_ram_gb,
    is_mods_need_update
)
from install_manager import (
    is_minecraft_installed, is_forge_installed, is_modpack_installed,
    is_resourcepack_installed, is_shaderpack_installed,
    install_minecraft, install_forge, install_mods,
    install_resourcepack, install_shaderpack
)
from game_launcher import launch_minecraft

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ИНТЕРФЕЙСА ---
root = None
entry_nickname = None
ram_var = None
lb = None
btn_play = None
bg_label = None


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ИНТЕРФЕЙСА ---


def update_status(text):
    if lb:
        lb.config(text=text)
        if root:
            root.update_idletasks()


def set_icon_from_url(window, url):
    """Скачивает иконку по URL и ставит её на окно."""
    if not PIL_AVAILABLE:
        return False
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            raw_data = response.read()
        icon_img = Image.open(io.BytesIO(raw_data))
        icon_img = icon_img.resize((64, 64))
        icon_photo = ImageTk.PhotoImage(icon_img)
        window.wm_iconphoto(True, icon_photo)
        window._icon_ref = icon_photo
        return True
    except Exception as e:
        print(f"Не удалось установить иконку: {e}")
        return False


# --- КАСТОМНЫЕ ЭЛЕМЕНТЫ (Кнопки) ---

def draw_mc_button(w, h, bg, border_dark="#2a2a2a", border_light="#9a9a9a"):
    if not PIL_AVAILABLE:
        return None
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=bg, outline=border_dark, width=2)
    d.line([(1, 1), (w - 2, 1)], fill=border_light, width=1)
    d.line([(1, 1), (1, h - 2)], fill=border_light, width=1)
    return ImageTk.PhotoImage(img)


def make_mc_button(parent, text, command, width=200, height=44, font_size=14, bg=COLOR_BG):
    if not PIL_AVAILABLE:
        # Обычная кнопка, если нет Pillow
        btn = tk.Button(parent, text=text, command=command, font=("Arial", font_size, "bold"))

        def set_state(state):
            btn.config(state=state)

        btn.config_state = set_state
        return btn

    normal_img = draw_mc_button(width, height, COLOR_BTN)
    hover_img = draw_mc_button(width, height, COLOR_BTN_HOVER)
    dis_img = draw_mc_button(width, height, COLOR_BTN_DIS)

    btn = tk.Label(
        parent, text=text, image=normal_img, compound="center",
        fg=COLOR_TEXT, font=("Arial", font_size, "bold"),
        bg=bg, cursor="hand2", bd=0
    )
    btn._img_normal = normal_img
    btn._img_hover = hover_img
    btn._img_dis = dis_img
    btn._enabled = True
    btn._command = command

    def on_enter(_):
        if btn._enabled: btn.config(image=hover_img)

    def on_leave(_):
        if btn._enabled: btn.config(image=normal_img)

    def on_click(_):
        if btn._enabled and btn._command: btn._command()

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


# --- ЛОГИКА ИГРЫ ---

def play_thread():
    global btn_play
    nickname = entry_nickname.get().strip()
    if not nickname:
        update_status("Введите никнейм!")
        return

    ram_gb = ram_var.get()
    save_settings(nickname, ram_gb)

    if btn_play: btn_play.config_state(tk.DISABLED)

    try:
        # 1. Minecraft
        if is_minecraft_installed(MINECRAFT_VERSION):
            update_status(f"Minecraft {MINECRAFT_VERSION} уже установлен.")
        else:
            update_status(f"Minecraft {MINECRAFT_VERSION} не найден. Устанавливаем...")
            install_minecraft(update_status, MINECRAFT_VERSION)
            update_status("Minecraft установлен!")

        # 2. Forge
        forge_id = install_forge(update_status, MINECRAFT_VERSION)
        update_status(f"Forge готов: {forge_id}")

        install_mods(update_status)

        # 4. Ресурспак
        if is_resourcepack_installed():
            update_status("Ресурспак актуален.")
        else:
            install_resourcepack(update_status)

        # 5. Шейдер
        if is_shaderpack_installed():
            update_status("Шейдер актуален.")
        else:
            install_shaderpack(update_status)

        # 6. Запуск
        update_status("Запуск игры...")
        launch_minecraft(version=forge_id, username=nickname, ram_gb=ram_gb)
        update_status(f"Игра запущена для {nickname}! (Если игра запустилась не сразу, подождите)")

    except Exception as e:
        update_status(f"Ошибка: {e}")
        print(f"Ошибка: {e}")
    finally:
        if btn_play: btn_play.config_state(tk.NORMAL)


def on_play_click():
    th = threading.Thread(target=play_thread, daemon=True)
    th.start()


# --- СОЗДАНИЕ ОКНА ---

def create_window():
    global root, entry_nickname, ram_var, lb, btn_play

    root = tk.Tk()
    root.title("ИС-25-05 Launcher")
    root.geometry("900x660")
    root.minsize(700, 500)
    root.resizable(True, True)
    root.configure(bg=COLOR_BG)

    ICON_URL = "https://img.icons8.ru/?size=100&id=TUH60vMtAmJ0&format=png&color=000000"
    set_icon_from_url(root, ICON_URL)

    # --- ФОН ---
    original_bg = None

    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    bg_path = resource_path("background.png")
    if PIL_AVAILABLE and os.path.isfile(bg_path):
        original_bg = Image.open(bg_path).convert("RGBA")

    bg_label = tk.Label(root, bd=0)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    resize_timer = None

    def do_resize():
        nonlocal resize_timer
        resize_timer = None
        if original_bg is None:
            return
        try:
            w = root.winfo_width()
            h = root.winfo_height()
            bg_resized = original_bg.resize((w, h), Image.Resampling.BILINEAR)
            overlay = Image.new("RGBA", bg_resized.size, (0, 0, 0, 130))
            bg_final = Image.alpha_composite(bg_resized, overlay).convert("RGB")
            new_photo = ImageTk.PhotoImage(bg_final)
            bg_label.config(image=new_photo)
            bg_label.image = new_photo
        except Exception as e:
            print(f"Ошибка ресайза фона: {e}")

    def on_resize(event):
        nonlocal resize_timer
        if resize_timer is not None:
            root.after_cancel(resize_timer)
        resize_timer = root.after(150, do_resize)

    root.bind("<Configure>", on_resize)
    root.after(100, do_resize)

    # --- ГЛАВНАЯ ПАНЕЛЬ (обычный Frame) ---
    main_frame = tk.Frame(root, bg=COLOR_PANEL, bd=0)
    main_frame.place(relx=0.5, rely=0.5, anchor="center", width=580, height=580)

    tk.Frame(main_frame, bg=COLOR_PANEL_L, height=2).pack(fill="x", side="top")
    tk.Frame(main_frame, bg=COLOR_PANEL_L, width=2).pack(fill="y", side="left")

    inner = tk.Frame(main_frame, bg=COLOR_PANEL)
    inner.pack(fill="both", expand=True, padx=26, pady=22)

    # Заголовок
    tk.Label(inner, text="ZOMBIE IS-25-05", font=("Arial", 22, "bold"), fg=COLOR_ACCENT, bg=COLOR_PANEL).pack(pady=(0, 2))
    tk.Label(inner, text="Launcher • 1.2", font=("Arial", 10), fg=COLOR_TEXT_DIM, bg=COLOR_PANEL).pack(pady=(0, 18))

    saved = load_settings()

    # Никнейм
    tk.Label(inner, text="Никнейм", font=("Arial", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_PANEL, anchor="w").pack(fill="x")
    entry_nickname = tk.Entry(inner, font=("Arial", 12), bg="#2b2b2b", fg=COLOR_TEXT,
                              insertbackground=COLOR_TEXT, relief="flat", bd=0)
    entry_nickname.insert(0, saved["nickname"])
    entry_nickname.pack(fill="x", ipady=6, pady=(3, 14))

    # ОЗУ
    max_ram = get_max_ram_gb()
    default_ram = min(saved["ram_gb"], max_ram)
    default_ram = max(1, default_ram)

    ram_header = tk.Frame(inner, bg=COLOR_PANEL)
    ram_header.pack(fill="x")
    tk.Label(ram_header, text="Оперативная память", font=("Arial", 11, "bold"), fg=COLOR_TEXT, bg=COLOR_PANEL).pack(side="left")
    tk.Label(ram_header, text=f"(макс. {max_ram} ГБ)", font=("Arial", 9), fg=COLOR_TEXT_DIM, bg=COLOR_PANEL).pack(side="right")

    ram_var = tk.IntVar(value=default_ram)
    spin_ram = tk.Spinbox(inner, from_=1, to=max_ram, textvariable=ram_var, font=("Arial", 12), bg="#2b2b2b",
                          fg=COLOR_TEXT, buttonbackground=COLOR_BTN, relief="flat", bd=0, insertbackground=COLOR_TEXT)
    spin_ram.pack(anchor="w", pady=(3, 14), ipady=4)

    # Директория
    tk.Label(inner, text=f"Папка игры: {minecraft_directory}", font=("Arial", 8), fg=COLOR_TEXT_DIM, bg=COLOR_PANEL,
             wraplength=520, justify="left").pack(fill="x", pady=(0, 10))

    # Статус
    status_frame = tk.Frame(inner, bg="#1a1a1a", bd=0)
    status_frame.pack(fill="both", expand=True, pady=(0, 14))

    lb = tk.Label(status_frame, text="Готов к запуску.", fg="#8be9fd", bg="#1a1a1a", font=("Consolas", 9), anchor="w",
                  justify="left", wraplength=520)
    lb.pack(fill="x", padx=12, pady=10)

    # Кнопка Играть
    btn_play = make_mc_button(inner, "ИГРАТЬ", command=on_play_click, width=520, height=52, font_size=18,
                              bg=COLOR_PANEL)
    btn_play.pack(pady=(2, 0), fill="x")

    # Подпись снизу
    tk.Label(
        inner,
        text="Лаунчер не ставит текстурпаки и шейдеры по умолчанию, это сделано в угоду оптимизации на слабых устройствах.\n"
             "Если вы уверены, что ваш компьютер выдержит текстурпаки и шейдеры, то смело включайте их.",
        font=("Arial", 12), fg=COLOR_TEXT_DIM, bg=COLOR_PANEL, wraplength=520, justify="left"
    ).pack(fill="x", pady=(0, 10))

    def on_closing():
        save_settings(entry_nickname.get().strip(), ram_var.get())
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()