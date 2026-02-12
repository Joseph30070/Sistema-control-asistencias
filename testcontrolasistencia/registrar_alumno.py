import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import date
from tkcalendar import DateEntry   # <--- ya lo tienes instalado

# ==============================
# CONEXIÓN CON LA BASE DE DATOS
# ==============================
def conectar_bd():
    return sqlite3.connect("control_asistencias.db")

# ==============================
# ASEGURAR COLUMNAS
# ==============================
def asegurar_columnas():
    conexion = conectar_bd()
    cursor = conexion.cursor()

    columnas = {
        "fecha_registro": "ALTER TABLE alumnos ADD COLUMN fecha_registro TEXT",
        "dni": "ALTER TABLE alumnos ADD COLUMN dni TEXT",
        "telefonopadres": "ALTER TABLE alumnos ADD COLUMN telefonopadres TEXT",
        "telefonoapoderado": "ALTER TABLE alumnos ADD COLUMN telefonoapoderado TEXT"
    }

    for col, cmd in columnas.items():
        try:
            cursor.execute(cmd)
            conexion.commit()
        except sqlite3.OperationalError:
            pass

    conexion.close()

# ==============================
# CARGAR CURSOS
# ==============================
def cargar_cursos(combo):
    conexion = conectar_bd()
    cursor = conexion.cursor()

    cursos_predeterminados = [
        "Robótica", "Electrónica",
        "Reparación de celulares",
        "Reparación de PC",
        "Ofimática"
    ]

    for c in cursos_predeterminados:
        cursor.execute("SELECT COUNT(*) FROM cursos WHERE nombre_curso=?", (c,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO cursos (nombre_curso) VALUES (?)", (c,))

    conexion.commit()

    cursor.execute("SELECT nombre_curso FROM cursos ORDER BY nombre_curso ASC")
    lista = [x[0] for x in cursor.fetchall()]
    conexion.close()

    combo["values"] = lista
    if lista:
        combo.current(0)

def agregar_curso(combo):
    
    nuevo = simpledialog.askstring("Nuevo curso", "Ingresa el nombre del nuevo curso:")
    if nuevo:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO cursos (nombre_curso) VALUES (?)", (nuevo,))
        conexion.commit()
        conexion.close()
        cargar_cursos(combo)
        messagebox.showinfo("Curso agregado", f"Curso '{nuevo}' añadido correctamente.")



# ==============================
# VENTANA PRINCIPAL
# ==============================
def ventana_registrar_alumno():
    asegurar_columnas()

    ventana = tk.Toplevel()
    ventana.title("Registrar Alumno")
    ventana.geometry("900x650")
    ventana.config(bg="#f0f3f7")
    ventana.resizable(True, True)


  

    # ==============================
    # ENCABEZADO
    # ==============================
    header = tk.Frame(ventana, bg="#1e3799", height=70)
    header.pack(fill="x")

    tk.Label(
        header,
        text="🧾 REGISTRO DE ALUMNOS",
        bg="#1e3799",
        fg="white",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=15)

    # ==================================================
    #   ZONA DESLIZABLE (Canvas + Scrollbar)
    # ==================================================
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

    # ==================================================
    #        CUERPO DEL FORMULARIO
    # ==================================================
    cuerpo = tk.Frame(interior, bg="#f0f3f7")
    cuerpo.pack(pady=20)

    # --------------------------
    # CAMPOS
    # --------------------------
    tk.Label(cuerpo, text="Nombres y Apellidos:", bg="#f0f3f7",
             font=("Segoe UI", 11, "bold")).grid(row=0, column=0, pady=8, padx=20, sticky="w")
    entry_nombre = ttk.Entry(cuerpo, width=35)
    entry_nombre.grid(row=0, column=1, pady=8, padx=10)

    tk.Label(cuerpo, text="DNI:", bg="#f0f3f7",
             font=("Segoe UI", 11, "bold")).grid(row=1, column=0, pady=8, padx=20, sticky="w")
    entry_dni = ttk.Entry(cuerpo, width=35)
    entry_dni.grid(row=1, column=1, pady=8, padx=10)

    # Fecha
    fecha_seleccionada = tk.StringVar(value="")

    def abrir_calendario():
        win = tk.Toplevel(ventana)
        win.title("Seleccionar fecha")
        win.geometry("300x150")
        win.resizable(False, False)
  

        tk.Label(win, text="Elegir fecha de inicio:", font=("Segoe UI", 11)).pack(pady=10)
        cal = DateEntry(win, date_pattern="yyyy-mm-dd")
        cal.pack()

        def confirmar():
            f = cal.get_date().strftime("%Y-%m-%d")
            fecha_seleccionada.set(f)
            lbl_fecha.config(text=f"📅 Inicio: {f}")
            win.destroy()

        ttk.Button(win, text="Confirmar", command=confirmar).pack(pady=10)

    ttk.Button(cuerpo, text="📅 Fecha / inicio", command=abrir_calendario).grid(row=1, column=2, padx=10)

    lbl_fecha = tk.Label(cuerpo, text="📅 Inicio: (automático)", bg="#f0f3f7",
                         font=("Segoe UI", 10, "italic"))
    lbl_fecha.grid(row=1, column=3)

    # Teléfono obligatorio
    tk.Label(cuerpo, text="Teléfono (obligatorio):", bg="#f0f3f7",
             font=("Segoe UI", 11, "bold")).grid(row=2, column=0, pady=8, padx=20, sticky="w")
    entry_telefono = ttk.Entry(cuerpo, width=35)
    entry_telefono.grid(row=2, column=1, pady=8, padx=10)

    # Teléfono padre/madre (opcional)
    tk.Label(cuerpo, text="Teléfono padre/madre (opcional):", bg="#f0f3f7",
             font=("Segoe UI", 11)).grid(row=3, column=0, pady=8, padx=20, sticky="w")
    entry_tel_padres = ttk.Entry(cuerpo, width=35)
    entry_tel_padres.grid(row=3, column=1, pady=8, padx=10)

    # Teléfono apoderado (opcional)
    tk.Label(cuerpo, text="Teléfono apoderado (opcional):", bg="#f0f3f7",
             font=("Segoe UI", 11)).grid(row=4, column=0, pady=8, padx=20, sticky="w")
    entry_tel_apoderado = ttk.Entry(cuerpo, width=35)
    entry_tel_apoderado.grid(row=4, column=1, pady=8, padx=10)

    # Curso
    tk.Label(cuerpo, text="Curso:", bg="#f0f3f7",
             font=("Segoe UI", 11, "bold")).grid(row=5, column=0, pady=8, padx=20, sticky="w")

    combo_curso = ttk.Combobox(cuerpo, width=30, state="readonly")
    combo_curso.grid(row=5, column=1, pady=8, padx=10)
    cargar_cursos(combo_curso)

    ttk.Button(cuerpo, text="➕ Agregar curso",
               command=lambda: agregar_curso(combo_curso)).grid(row=5, column=2, padx=5)

    # Horario
    horas = [f"{h:02d}:{m:02d} {'AM' if h < 12 else 'PM'}"
             for h in range(6, 22) for m in (0, 30)]

    tk.Label(cuerpo, text="Horario:", bg="#f0f3f7",
             font=("Segoe UI", 11, "bold")).grid(row=6, column=0, pady=8, padx=20, sticky="w")

    frame_h = tk.Frame(cuerpo, bg="#f0f3f7")
    frame_h.grid(row=6, column=1, pady=8, padx=10)

    tk.Label(frame_h, text="Inicio:", bg="#f0f3f7").grid(row=0, column=0)
    combo_inicio = ttk.Combobox(frame_h, values=horas, width=12, state="readonly")
    combo_inicio.grid(row=0, column=1, padx=5)

    tk.Label(frame_h, text="Fin:", bg="#f0f3f7").grid(row=0, column=2)
    combo_fin = ttk.Combobox(frame_h, values=horas, width=12, state="readonly")
    combo_fin.grid(row=0, column=3, padx=5)

    # =====================
    # GUARDAR (MISMO CÓDIGO ORIGINAL + CAMPOS NUEVOS)
    # =====================
    def guardar():
        nombre = entry_nombre.get().strip()
        dni = entry_dni.get().strip()
        telefono = entry_telefono.get().strip()
        tel_padres = entry_tel_padres.get().strip()
        tel_apoderado = entry_tel_apoderado.get().strip()
        curso = combo_curso.get().strip()
        h1, h2 = combo_inicio.get(), combo_fin.get()
        horario = f"{h1} a {h2}" if h1 and h2 else ""

        if not nombre or not dni or not telefono or not curso:
            messagebox.showwarning("Campos incompletos",
                                   "Nombre, DNI, Teléfono y Curso son obligatorios.")
            return

        fecha_registro = fecha_seleccionada.get() or date.today().strftime("%Y-%m-%d")
        conexion = conectar_bd()
        cursor = conexion.cursor()

 
        try:
           cursor.execute("""
            INSERT INTO alumnos (nombre, telefono, telefonopadres, telefonoapoderado,
                                 curso, horario, dni, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, telefono, tel_padres, tel_apoderado,
              curso, horario, dni, fecha_registro))

           conexion.commit()
           messagebox.showinfo("Alumno registrado", f"Alumno '{nombre}' registrado correctamente.")
           ventana.destroy()
        except Exception as e:
            # Mensaje de error más amable en caso de fallo en la BD
            messagebox.showerror("Error al guardar", f"No se pudo registrar el alumno:\n{e}")
        finally:
            conexion.close()
        

    # ======================
    # BOTONES ABAJO
    # ======================
    frame_botones = tk.Frame(interior, bg="#f0f3f7")
    frame_botones.pack(pady=20)

    estilo_boton = {
        "bg": "#dcdde1",
        "fg": "black",
        "font": ("Segoe UI", 11, "bold"),
        "width": 18,
        "height": 2,
        "relief": "raised",
        "bd": 3
    }

    btn_guardar = tk.Button(frame_botones, text="💾  Guardar", command=guardar, **estilo_boton)
    btn_guardar.grid(row=0, column=0, padx=15)

    btn_cerrar = tk.Button(
        frame_botones,
        text="❌  Cerrar",
        command=ventana.destroy,
        bg="#b2bec3",
        fg="black",
        font=("Segoe UI", 11, "bold"),
        width=18,
        height=2,
        relief="raised",
        bd=3
    )
    btn_cerrar.grid(row=0, column=1, padx=15)
    return ventana

