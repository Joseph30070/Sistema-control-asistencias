import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, Image
import os
import subprocess
import sys

USUARIO_CORRECTO = "beatcell"
CONTRASENA_CORRECTA = "123456"

# =========================
# FUNCIÓN PARA OBTENER RECURSOS EN PYINSTALLER
# =========================
def resource_path(relative_path):
    """Obtiene el path absoluto del archivo, compatible con PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)

    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path,relative_path)

# =========================
# FUNCIÓN PARA ABRIR MAIN
# =========================
def abrir_main():
    ventana.destroy()
    import main
    main.mostrar_menu_principal()

# =========================
# FUNCIÓN DEL BOTÓN LOGIN
# =========================
def intentar_login():
    usuario = entry_usuario.get().strip()
    contrasena = entry_contrasena.get().strip()

    lbl_error.config(text="")  # limpiar error

    if usuario != USUARIO_CORRECTO and contrasena != CONTRASENA_CORRECTA:
        lbl_error.config(text="Usuario y contraseña incorrectos")
        return
    if usuario != USUARIO_CORRECTO:
        lbl_error.config(text="Usuario incorrecto")
        return
    if contrasena != CONTRASENA_CORRECTA:
        lbl_error.config(text="Contraseña incorrecta")
        return

    abrir_main()

# =========================
# FUNCIÓN PARA MOSTRAR/Ocultar CONTRASEÑA
# =========================
def toggle_password():
    global mostrar
    if mostrar:
        entry_contrasena.config(show="*")
        btn_ojo.config(image=img_ojo_cerrado)
        mostrar = False
    else:
        entry_contrasena.config(show="")
        btn_ojo.config(image=img_ojo_abierto)
        mostrar = True

# =========================
# VENTANA LOGIN
# =========================
ventana = tk.Tk()
ventana.title("Login - Sistema de Asistencias")
ventana.geometry("420x420")
ventana.resizable(False, False)
ventana.configure(bg="#f5f6fa")


# Título
titulo = tk.Label(
    ventana,
    text="Bienvenido",
    font=("Segoe UI", 22, "bold"),
    bg="#f5f6fa",
    fg="#273c75"
)
titulo.pack(pady=30)

# Marco principal
frame = tk.Frame(ventana, bg="white", bd=2, relief="groove", padx=20, pady=20)
frame.pack(pady=10)

# Usuario
tk.Label(frame, text="Usuario", bg="white", fg="#273c75", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w")
entry_usuario = ttk.Entry(frame, font=("Segoe UI", 12))
entry_usuario.grid(row=1, column=0, pady=10, ipadx=40)

# Contraseña
tk.Label(frame, text="Contraseña", bg="white", fg="#273c75", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w")

entry_contrasena = ttk.Entry(frame, show="*", font=("Segoe UI", 12))
entry_contrasena.grid(row=3, column=0, pady=10, ipadx=40)

# ÍCONOS OJO (cargados con resource_path)
mostrar = False

img_ojo_cerrado = ImageTk.PhotoImage(Image.open(resource_path("ojo_cerrado.png")).resize((25, 25)))
img_ojo_abierto = ImageTk.PhotoImage(Image.open(resource_path("ojo_abierto.png")).resize((25, 25)))

btn_ojo = tk.Button(frame, image=img_ojo_cerrado, bg="white", bd=0, command=toggle_password)
btn_ojo.grid(row=3, column=1, padx=5)

# Etiqueta error
lbl_error = tk.Label(frame, text="", fg="red", bg="white", font=("Segoe UI", 10, "bold"))
lbl_error.grid(row=4, column=0, columnspan=2, pady=5)

# Botón ingresar
btn_ingresar = ttk.Button(
    frame,
    text="Ingresar",
    style="LoginButton.TButton",
    command=intentar_login
)
btn_ingresar.grid(row=5, column=0, columnspan=2, pady=15)

# Estilo botón
style = ttk.Style()
style.configure(
    "LoginButton.TButton",
    font=("Segoe UI", 12, "bold"),
    padding=10
)

ventana.mainloop()
