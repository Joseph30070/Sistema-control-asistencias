# info_alumnos.py
import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta
from datetime import date

# --------------------------
# CONFIG / DB
# --------------------------
DB = "control_asistencias.db"

def conectar_bd():
    return sqlite3.connect(DB)

def parsear_fecha_a_date(fecha_txt):
    """
    Acepta formatos:
      - "YYYY-MM-DD"
      - "DD/MM/YYYY"
    Devuelve datetime.date o None.
    """
    if not fecha_txt:
        return None
    fecha_txt = fecha_txt.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(fecha_txt, fmt).date()
        except Exception:
            pass
    try:
        return datetime.fromisoformat(fecha_txt).date()
    except Exception:
        return None

# --------------------------
# VENTANA
# --------------------------
def ventana_info_alumnos():
    ventana = tk.Toplevel()
    ventana.title("📘 Información de Alumnos")
    ventana.geometry("1100x650")
    ventana.configure(bg="white")

    

   

    lbl = tk.Label(
        ventana,
        text="📘 Información de Alumnos",
        font=("Segoe UI", 20, "bold"),
        bg="white",
        fg="#273c75"
    )
    lbl.pack(pady=15)

    # --------------------------
    # MARCO FILTROS
    # --------------------------
    frame_filtros = tk.Frame(ventana, bg="white")
    frame_filtros.pack(fill="x", pady=5)

    tk.Label(frame_filtros, text="Filtrar por Curso:", bg="white", fg="#2f3640",
             font=("Segoe UI", 10, "bold")).pack(side="left", padx=10)

    # obtener cursos
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre_curso FROM cursos ORDER BY nombre_curso")
    cursos = ["Todos"] + [row[0] for row in cursor.fetchall()]
    conexion.close()

    combo_curso = ttk.Combobox(frame_filtros, values=cursos, state="readonly", width=20)
    combo_curso.current(0)
    combo_curso.pack(side="left")

    tk.Label(frame_filtros, text="   Buscar DNI:", bg="white", fg="#2f3640",
             font=("Segoe UI", 10, "bold")).pack(side="left", padx=(20, 5))

    dni_var = tk.StringVar()
    entry_dni = ttk.Entry(frame_filtros, width=20, textvariable=dni_var)
    entry_dni.pack(side="left")

    # --------------------------
    # TABLA
    # --------------------------
    frame_tabla = tk.Frame(ventana, bg="white")
    frame_tabla.pack(fill="both", expand=True, padx=15, pady=10)

    columnas = (
        "ID", "Nombre", "DNI", "Teléfono",
        "Tel. Padres", "Tel. Apoderado",
        "Curso", "Horario", "F. Registro", "Estado"
    )

    tabla = ttk.Treeview(
        frame_tabla,
        columns=columnas,
        show="headings",
    )

    estilo = ttk.Style()
    estilo.configure("Treeview.Heading",
                     font=("Segoe UI", 10, "bold"),
                     foreground="#2f3640")

    encabezados = {
        "ID": ("ID", 60),
        "Nombre": ("Nombres y Apellidos", 220),
        "DNI": ("DNI", 110),
        "Teléfono": ("Teléfono", 120),
        "Tel. Padres": ("Tel. Padres", 120),
        "Tel. Apoderado": ("Tel. Apoderado", 120),
        "Curso": ("Curso", 160),
        "Horario": ("Horario", 160),
        "F. Registro": ("F. Registro", 110),
        "Estado": ("Estado", 120)
    }

    for col in columnas:
        tabla.heading(col, text=encabezados[col][0])
        tabla.column(col, width=encabezados[col][1], anchor="center")

    tabla.column("Nombre", width=220, anchor="w")

    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll_y.set)
    scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=tabla.xview)
    tabla.configure(xscrollcommand=scroll_x.set)

    tabla.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")
    frame_tabla.rowconfigure(0, weight=1)
    frame_tabla.columnconfigure(0, weight=1)

    # --------------------------
    # COLORES
    # --------------------------
    tabla.tag_configure("cursando", background="#dff7d8")     # verde claro
    tabla.tag_configure("ultima_fecha", background="#fbdbdb") # rojo claro
    tabla.tag_configure("por_cursar", background="#eeeeee")   # gris claro

    # --------------------------
    # LÓGICA NUEVA (SOLO FECHAS)
    # --------------------------
    hoy = date.today()

    def cargar_datos():
        conexion = conectar_bd()
        cursor = conexion.cursor()

        filtro_curso = combo_curso.get()
        dni_buscar = dni_var.get().strip()

        query = """
            SELECT id_alumno, nombre, dni, telefono,
                   telefonopadres, telefonoapoderado,
                   curso, horario, fecha_registro, fecha_baja
            FROM alumnos
            WHERE 1=1
        """
        params = []

        if filtro_curso != "Todos":
            query += " AND curso = ?"
            params.append(filtro_curso)

        if dni_buscar != "":
            query += " AND dni LIKE ?"
            params.append("%" + dni_buscar + "%")

        query += " ORDER BY nombre ASC"

        cursor.execute(query, params)
        datos = cursor.fetchall()
        conexion.close()

        tabla.delete(*tabla.get_children())

        for fila in datos:
            (id_a, nombre, dni, tel, tpadres, tapode,
             curso, horario, freg, f_baja) = fila

            fecha_reg = parsear_fecha_a_date(freg)
            fecha_baja = parsear_fecha_a_date(f_baja)

            # --------------------------
            #   NUEVA LÓGICA DE ESTADO
            # --------------------------
            if fecha_reg and fecha_reg > hoy:
                estado_texto = "Por cursar"
                tag = "por_cursar"
                freg_display = fecha_reg.strftime("%d/%m/%Y")

            else:
                if fecha_baja:
                    ultimo_dia = fecha_baja - timedelta(days=1)
                    estado_texto = ultimo_dia.strftime("%d/%m/%Y")
                    tag = "ultima_fecha"
                    freg_display = fecha_reg.strftime("%d/%m/%Y") if fecha_reg else ""
                else:
                    estado_texto = "Cursando"
                    tag = "cursando"
                    freg_display = fecha_reg.strftime("%d/%m/%Y") if fecha_reg else ""

            tabla.insert(
                "",
                "end",
                values=(
                    id_a,
                    nombre,
                    dni if dni else "Sin info",
                    tel if tel else "Sin info",
                    tpadres if tpadres else "Sin info",
                    tapode if tapode else "Sin info",
                    curso if curso else "Sin info",
                    horario if horario else "Sin info",
                    freg_display,
                    estado_texto
                ),
                tags=(tag,)
            )

    # filtros reactivos
    entry_dni.bind("<Return>", lambda e: cargar_datos())
    dni_var.trace_add("write", lambda *args: cargar_datos())
    combo_curso.bind("<<ComboboxSelected>>", lambda e: cargar_datos())

    btn_buscar = tk.Button(
        frame_filtros,
        text="Buscar",
        bg="#273c75",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=10,
        command=cargar_datos
    )
    btn_buscar.pack(side="left", padx=(10, 0))

    cargar_datos()

    return ventana

# pruebas
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    ventana_info_alumnos()
    root.mainloop()
