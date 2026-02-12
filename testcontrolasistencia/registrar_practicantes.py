# registrar_practicantes.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import date
from tkcalendar import DateEntry

DB = "control_asistencias.db"

# ==============================
# CONEXIÓN BD
# ==============================
def conectar_bd():
    return sqlite3.connect(DB)

# ==============================
# ASEGURAR COLUMNAS
# ==============================
def asegurar_columnas_practicantes():
    conexion = conectar_bd()
    cursor = conexion.cursor()

    columnas = {
        "dni": "ALTER TABLE practicantes ADD COLUMN dni TEXT",
        "fecha_registro": "ALTER TABLE practicantes ADD COLUMN fecha_registro TEXT",
        "telefono_emergencia": "ALTER TABLE practicantes ADD COLUMN telefono_emergencia TEXT"
    }

    for cmd in columnas.values():
        try:
            cursor.execute(cmd)
        except sqlite3.OperationalError:
            pass

    conexion.commit()
    conexion.close()

# ==============================
# CARGAR ÁREAS (carreras)
# ==============================
def cargar_areas(combo):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    areas_predeterminadas = [
        "Desarrollo de Software",
        "Diseño Grafico",
    ]

    for area in areas_predeterminadas:
        cursor.execute("SELECT COUNT(*) FROM carreras WHERE nombre_carrera=?", (area,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO carreras (nombre_carrera) VALUES (?)", (area,))

    conexion.commit()

    cursor.execute("SELECT nombre_carrera FROM carreras ORDER BY nombre_carrera ASC")
    lista = [a[0] for a in cursor.fetchall()]
    conexion.close()

    combo["values"] = lista
    if lista:
        combo.current(0)

def agregar_area(combo):
    nuevo = simpledialog.askstring("Nueva área", "Nombre del área:")
    if nuevo:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO carreras (nombre_carrera) VALUES (?)", (nuevo,))
        conexion.commit()
        conexion.close()
        cargar_areas(combo)
        messagebox.showinfo("Área agregada", f"Área '{nuevo}' añadida correctamente")

# ==============================
# VENTANA PRINCIPAL
# ==============================
def ventana_registrar_practicante():
    asegurar_columnas_practicantes()

    ventana = tk.Toplevel()
    ventana.title("Registrar Practicante")
    ventana.geometry("900x650")
    ventana.config(bg="#f0f3f7")
    ventana.resizable(True, True)




    # Header
    header = tk.Frame(ventana, bg="#1e3799", height=70)
    header.pack(fill="x")

    tk.Label(header, text="🧾 REGISTRO DE PRACTICANTES",
             bg="#1e3799", fg="white",
             font=("Segoe UI", 16, "bold")).pack(pady=15)

    # Scroll
    contenedor_scroll = tk.Frame(ventana, bg="#f0f3f7")
    contenedor_scroll.pack(fill="both", expand=True)

    canvas = tk.Canvas(contenedor_scroll, bg="#f0f3f7", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(contenedor_scroll, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    interior = tk.Frame(canvas, bg="#f0f3f7")
    canvas_window = canvas.create_window((0, 0), window=interior, anchor="nw")

    def ajustar_scroll(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

    interior.bind("<Configure>", ajustar_scroll)
    canvas.bind("<Configure>", ajustar_scroll)

    cuerpo = tk.Frame(interior, bg="#f0f3f7")
    cuerpo.pack(pady=20)

    # ========================
    # CAMPOS DEL FORMULARIO
    # ========================

    # Nombre
    tk.Label(cuerpo, text="Nombres y Apellidos:",
             bg="#f0f3f7", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, pady=8, padx=20, sticky="w")
    entry_nombre = ttk.Entry(cuerpo, width=35)
    entry_nombre.grid(row=0, column=1, pady=8, padx=10)

    # DNI
    tk.Label(cuerpo, text="DNI:",
             bg="#f0f3f7", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, pady=8, padx=20, sticky="w")
    entry_dni = ttk.Entry(cuerpo, width=35)
    entry_dni.grid(row=1, column=1, pady=8, padx=10)

    # Fecha registro
    fecha_seleccionada = tk.StringVar(value="")

    def abrir_calendario():
        win = tk.Toplevel(ventana)
        win.title("Seleccionar fecha")
        win.geometry("300x150")

        tk.Label(win, text="Elegir fecha de inicio:", font=("Segoe UI", 11)).pack(pady=10)
        cal = DateEntry(win, date_pattern="yyyy-mm-dd")
        cal.pack()

        def confirmar():
            f = cal.get_date().strftime("%Y-%m-%d")
            fecha_seleccionada.set(f)
            lbl_fecha.config(text=f"📅 Inicio: {f}")
            win.destroy()

        ttk.Button(win, text="Confirmar", command=confirmar).pack(pady=10)

    ttk.Button(cuerpo, text="📅 Fecha / inicio", command=abrir_calendario)\
        .grid(row=1, column=2, padx=10)

    lbl_fecha = tk.Label(cuerpo, text="📅 Inicio: (automático)",
                         bg="#f0f3f7", font=("Segoe UI", 10, "italic"))
    lbl_fecha.grid(row=1, column=3)

    # Teléfono
    tk.Label(cuerpo, text="Teléfono:",
             bg="#f0f3f7", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, pady=8, padx=20, sticky="w")
    entry_telefono = ttk.Entry(cuerpo, width=35)
    entry_telefono.grid(row=2, column=1, pady=8, padx=10)

    # Teléfono emergencia
    tk.Label(cuerpo, text="Teléfono (Emergencia):",
             bg="#f0f3f7", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, pady=8, padx=20, sticky="w")
    entry_telefono_emerg = ttk.Entry(cuerpo, width=35)
    entry_telefono_emerg.grid(row=3, column=1, pady=8, padx=10)


    # Área
    tk.Label(cuerpo, text="Área:",
             bg="#f0f3f7", font=("Segoe UI", 11, "bold")).grid(row=4, column=0, pady=8, padx=20, sticky="w")

    combo_area = ttk.Combobox(cuerpo, width=30, state="readonly")
    combo_area.grid(row=4, column=1, pady=8, padx=10)
    cargar_areas(combo_area)

    ttk.Button(cuerpo, text="➕ Agregar área", command=lambda: agregar_area(combo_area))\
        .grid(row=3, column=2, padx=5)

    # Horario
    horas = [f"{h:02d}:{m:02d} {'AM' if h < 12 else 'PM'}"
             for h in range(6, 22) for m in (0, 30)]

    tk.Label(cuerpo, text="Horario:",
             bg="#f0f3f7", font=("Segoe UI", 11, "bold")).grid(row=5, column=0, pady=8, padx=20, sticky="w")

    frame_h = tk.Frame(cuerpo, bg="#f0f3f7")
    frame_h.grid(row=5, column=1, pady=8, padx=10)

    tk.Label(frame_h, text="Inicio:", bg="#f0f3f7").grid(row=0, column=0)
    combo_inicio = ttk.Combobox(frame_h, values=horas, width=12, state="readonly")
    combo_inicio.grid(row=0, column=1, padx=5)

    tk.Label(frame_h, text="Fin:", bg="#f0f3f7").grid(row=0, column=2)
    combo_fin = ttk.Combobox(frame_h, values=horas, width=12, state="readonly")
    combo_fin.grid(row=0, column=3, padx=5)

    # =====================
    # GUARDAR
    # =====================
    def guardar():
        nombre = entry_nombre.get().strip()
        dni = entry_dni.get().strip()
        telefono = entry_telefono.get().strip()
        telefono_emerg = entry_telefono_emerg.get().strip()
        area = combo_area.get().strip()

        h1, h2 = combo_inicio.get(), combo_fin.get()
        horario = f"{h1} a {h2}" if h1 and h2 else ""

        if not nombre or not area:
            messagebox.showwarning("Campos incompletos", "Nombre y Área son obligatorios.")
            return

        fecha_registro = fecha_seleccionada.get() or date.today().strftime("%Y-%m-%d")

        conexion = conectar_bd()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                INSERT INTO practicantes (nombre, telefono, telefono_emergencia, carrera, horario, dni, fecha_registro)
VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nombre, telefono, telefono_emerg, area, horario, dni, fecha_registro))

            conexion.commit()
            messagebox.showinfo("Registrado", f"Practicante '{nombre}' añadido correctamente.")
            ventana.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar:\n{e}")
        finally:
            conexion.close()

    # ======================
    # BOTONES
    # ======================
    frame_botones = tk.Frame(interior, bg="#f0f3f7")
    frame_botones.pack(pady=20)

    estilo = {
        "bg": "#dcdde1",
        "fg": "black",
        "font": ("Segoe UI", 11, "bold"),
        "width": 18,
        "height": 2,
        "relief": "raised",
        "bd": 3
    }

    tk.Button(frame_botones, text="💾 Guardar", command=guardar, **estilo)\
        .grid(row=0, column=0, padx=15)

    tk.Button(frame_botones, text="❌ Cerrar", command=ventana.destroy,
              bg="#b2bec3", fg="black", font=("Segoe UI", 11, "bold"),
              width=18, height=2, relief="raised", bd=3)\
        .grid(row=0, column=1, padx=15)

    

    return ventana
