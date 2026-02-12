import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
from asistencia_alumnos import ventana_asistencia_alumnos
from registrar_alumno import ventana_registrar_alumno
from cuotas_alumnos import ventana_cuotas
from info_alumnos import ventana_info_alumnos
from registrar_practicantes import ventana_registrar_practicante
from asistencia_practicantes import ventana_asistencia_practicantes


# ======================================================
# FUNCIÓN PARA CREAR AUTOMÁTICAMENTE LA BASE DE DATOS
# ======================================================
def crear_base_datos():
    conexion = sqlite3.connect("control_asistencias.db")
    cursor = conexion.cursor()

    # =======================================
    # TABLA DE CURSOS
    # =======================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cursos (
        id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_curso TEXT NOT NULL UNIQUE
    )
    """)

    cursos_predeterminados = [
        ("Robótica",),
        ("Electrónica",),
        ("Reparación de celulares",),
        ("Reparación de PC",),
        ("Ofimática",)
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO cursos (nombre_curso)
        VALUES (?)
    """, cursos_predeterminados)

    # =======================================
    # TABLA DE CARRERAS
    # =======================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS carreras (
        id_carrera INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_carrera TEXT NOT NULL
    )
    """)

    # =======================================
    # TABLA DE ALUMNOS
    # =======================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos (
        id_alumno INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        telefonopadres TEXT,         
        telefonoapoderado TEXT,      
        curso TEXT,
        horario TEXT,
        cuota1 INTEGER DEFAULT 0,
        cuota2 INTEGER DEFAULT 0,
        cuota3 INTEGER DEFAULT 0,
        cuota4 INTEGER DEFAULT 0,
        id_curso INTEGER,
        dni TEXT,
        fecha_baja TEXT,
        fecha_registro TEXT DEFAULT (date('now')),
        FOREIGN KEY (id_curso) REFERENCES cursos(id_curso)
    )
    """)


    # =======================================
    # TABLA DE PRACTICANTES
    # =======================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS practicantes (
        id_practicante INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        telefono_emergencia TEXT,
        carrera TEXT,
        horario TEXT,
        dni TEXT,
        id_carrera INTEGER,
        fecha_baja TEXT,
        fecha_registro TEXT DEFAULT (date('now')),
        FOREIGN KEY (id_carrera) REFERENCES carreras(id_carrera)
    )
    """)

    # =======================================
    # TABLA DE ASISTENCIAS
    # =======================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias (
        id_asistencia INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        id_persona INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        hora_entrada TEXT,
        hora_salida TEXT,
        tareas_asignadas TEXT,
        tareas_terminadas TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias_practicantes (
    id_asistencia INTEGER PRIMARY KEY AUTOINCREMENT,
    id_practicante INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    hora_entrada TEXT,
    hora_salida TEXT,
    tareas_asignadas TEXT,
    tareas_terminadas TEXT,
    FOREIGN KEY (id_practicante) REFERENCES practicantes(id_practicante)
)
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos_cuotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alumno INTEGER NOT NULL,
            curso TEXT NOT NULL,
            cuota_num INTEGER NOT NULL,
            metodo TEXT,
            fecha TEXT,  -- YYYY-MM-DD
            confirmado INTEGER DEFAULT 1
        )
    """)

    # =======================================
    # TABLA PARA ESTADO DE HABILITACIÓN / DESHABILITACIÓN POR CURSO
    # =======================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuotas_estado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_alumno INTEGER NOT NULL,
            curso TEXT NOT NULL,
            habilitado INTEGER DEFAULT 1,
            UNIQUE(id_alumno, curso)
        )
    """)
    cursor.execute("""
       CREATE UNIQUE INDEX IF NOT EXISTS idx_pago_unico
       ON pagos_cuotas(id_alumno, curso, cuota_num)
    """)

    conexion.commit()
    conexion.close()
    print("✅ Base de datos 'control_asistencias.db' creada o verificada correctamente.")


# Crear la base de datos antes de iniciar la ventana principal
crear_base_datos()

ventanas_abiertas = {}

def abrir_ventana_controlada(nombre, constructor):
    # Si ya existe y la ventana sigue viva → traerla al frente
    if nombre in ventanas_abiertas:
        if ventanas_abiertas[nombre].winfo_exists():
            ventanas_abiertas[nombre].lift()
            ventanas_abiertas[nombre].focus_force()
            return
        else:
            # El registro existe pero la ventana ya fue cerrada
            del ventanas_abiertas[nombre]

    # Crear nueva ventana
    nueva = constructor()
    ventanas_abiertas[nombre] = nueva

    # Cuando la ventana se cierre, eliminarla del diccionario
    nueva.protocol("WM_DELETE_WINDOW", lambda: cerrar_ventana(nombre))

def cerrar_ventana(nombre):
    if nombre in ventanas_abiertas:
        try:
            ventanas_abiertas[nombre].destroy()
        except:
            pass
        del ventanas_abiertas[nombre]



# ======================================================
# CONFIGURACIÓN PRINCIPAL DE LA INTERFAZ
# ======================================================


ventana = tk.Tk()
ventana.title("Sistema de Control de Asistencias")
ventana.geometry("1050x720")
ventana.minsize(700, 600)
ventana.resizable(True, True)

# ==============================
# ENCABEZADO SUPERIOR
# ==============================
header = tk.Frame(ventana, bg="#273c75", height=80)
header.pack(fill="x")

titulo = tk.Label(
    header,
    text="📋 CONTROL DE ASISTENCIAS",
    bg="#273c75",
    fg="white",
    font=("Segoe UI", 22, "bold")
)
titulo.pack(pady=20)

# ======================================================
# CUERPO PRINCIPAL CON SCROLL Y CONTENIDO CENTRADO
# ======================================================
cuerpo = tk.Frame(ventana, bg="#f5f6fa")
cuerpo.pack(fill="both", expand=True)

canvas = tk.Canvas(cuerpo, bg="#f5f6fa", highlightthickness=0)
canvas.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(cuerpo, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.configure(yscrollcommand=scrollbar.set)

wrapper = tk.Frame(canvas, bg="#f5f6fa")
canvas_window = canvas.create_window((0, 0), window=wrapper, anchor="nw")

contenedor_tarjetas = tk.Frame(wrapper, bg="#f5f6fa")
contenedor_tarjetas.grid(row=0, column=0, pady=20)

wrapper.grid_columnconfigure(0, weight=1)

def on_canvas_configure(event):
    canvas.itemconfig(canvas_window, width=event.width)
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_wrapper_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

canvas.bind("<Configure>", on_canvas_configure)
wrapper.bind("<Configure>", on_wrapper_configure)

def _on_mousewheel(event):
    if event.delta:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

# ==============================
# ESTILO DE BOTONES
# ==============================
estilo = ttk.Style()
estilo.configure("MenuButton.TButton", font=("Segoe UI", 12, "bold"), padding=10)

def mostrar_mensaje(tipo):
    if tipo == "Alumnos":
        abrir_ventana_controlada("asistencia", ventana_asistencia_alumnos)

    elif tipo == "Practicantes":
        abrir_ventana_controlada("asistencia_practicant", ventana_asistencia_practicantes)

    elif tipo == "RegistrarAlumno":
        abrir_ventana_controlada("registrar_alumno", ventana_registrar_alumno)

    elif tipo == "RegistrarPracticante":
        abrir_ventana_controlada("registrar_practicant", ventana_registrar_practicante)

    elif tipo == "Cuotas":
        abrir_ventana_controlada("cuotas", ventana_cuotas)

    elif tipo == "Info":
        abrir_ventana_controlada("info_alumnos", ventana_info_alumnos)
        
# ==============================
# TARJETAS DE OPCIONES
# ==============================
tarjetas = [
    ("🎓", "Asistencia Alumnos", lambda: mostrar_mensaje("Alumnos")),
    ("🧰", "Asistencia Practicantes", lambda: mostrar_mensaje("Practicantes")),
    ("📝", "Registrar Alumno", lambda: mostrar_mensaje("RegistrarAlumno")),
    ("🧾", "Registrar Practicante", lambda: mostrar_mensaje("RegistrarPracticante")),
    ("💰", "Control de Cuotas", lambda: mostrar_mensaje("Cuotas")),
    ("📘", "Info Alumnos", lambda: mostrar_mensaje("Info"))   # ✅ NUEVA TARJETA
]

def crear_tarjeta(parent, emoji, titulo_texto, comando):
    card = tk.Frame(parent, bg="white", bd=2, relief="ridge", width=280, height=180)
    card.propagate(False)
    lbl = tk.Label(
        card,
        text=f"{emoji}\n{titulo_texto}",
        font=("Segoe UI", 13, "bold"),
        bg="white",
        fg="#273c75",
        wraplength=240,
        justify="center"
    )
    lbl.pack(expand=True, pady=(15, 5))
    btn = ttk.Button(card, text="Abrir", command=comando, style="MenuButton.TButton")
    btn.pack(pady=(0, 10))
    return card

frames_tarjetas = [crear_tarjeta(contenedor_tarjetas, *data) for data in tarjetas]

def distribuir_tarjetas():
    for widget in contenedor_tarjetas.winfo_children():
        widget.grid_forget()

    ancho = ventana.winfo_width()

    if ancho < 850:
        for i, frame in enumerate(frames_tarjetas):
            frame.grid(row=i, column=0, padx=10, pady=15)
    else:
        posiciones = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)]  # ← incluí la tarjeta 6
        for i, (frame, (r, c)) in enumerate(zip(frames_tarjetas, posiciones)):
            frame.grid(row=r, column=c, padx=30, pady=30)

    ventana.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_resize(event):
    distribuir_tarjetas()

ventana.bind("<Configure>", on_resize)
ventana.after(200, distribuir_tarjetas)

# ==============================
# PIE DE PÁGINA (FECHA Y HORA)
# ==============================
footer = tk.Frame(ventana, bg="#dcdde1", height=40)
footer.pack(fill="x", side="bottom")

def actualizar_hora():
    hora_actual = datetime.now().strftime("%d/%m/%Y  %I:%M %p")
    lbl_hora.config(text=hora_actual)
    ventana.after(1000, actualizar_hora)

lbl_hora = tk.Label(footer, text="", bg="#dcdde1", font=("Segoe UI", 10))
lbl_hora.pack(pady=10)
actualizar_hora()

ventana.mainloop()
