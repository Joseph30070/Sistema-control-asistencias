# asistencia_practicantes.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime, date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
import locale

# ============================
# CONFIGURACIÓN DE IDIOMA
# ============================
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except:
    try:
        locale.setlocale(locale.LC_TIME, "es_ES")
    except:
        pass

DB = "control_asistencias.db"

# ============================
# CONEXIÓN BASE DE DATOS
# ============================
def conectar_bd():
    return sqlite3.connect(DB)

def asegurar_columnas_practicantes():
    """Asegura que existan las columnas necesarias en la tabla practicantes (fecha_baja, fecha_registro, dni)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    columnas = {
        "fecha_baja": "ALTER TABLE practicantes ADD COLUMN fecha_baja TEXT",
        "fecha_registro": "ALTER TABLE practicantes ADD COLUMN fecha_registro TEXT",
        "dni": "ALTER TABLE practicantes ADD COLUMN dni TEXT",
        "telefono_emergencia": "ALTER TABLE practicantes ADD COLUMN telefono_emergencia TEXT"

    }
    for comando in columnas.values():
        try:
            cursor.execute(comando)
            conexion.commit()
        except sqlite3.OperationalError:
            # columna ya existe
            pass
    conexion.close()

# ============================
# VENTANA PRINCIPAL DE ASISTENCIA (PRACTICANTES)
# ============================
def ventana_asistencia_practicantes():
    asegurar_columnas_practicantes()

    ventana = tk.Toplevel()
    ventana.title("Asistencia de Practicantes")
    ventana.geometry("1200x750")
    ventana.config(bg="#f5f6fa")
    ventana.resizable(True, True)




    # ENCABEZADO
    header = tk.Frame(ventana, bg="#273c75", height=70)
    header.pack(fill="x")

    titulo = tk.Label(header, text="🛠️ CONTROL DE ASISTENCIA - PRACTICANTES",
                      bg="#273c75", fg="white", font=("Segoe UI", 16, "bold"))
    titulo.pack(pady=15)

    # SELECCIONAR FECHA
    frame_fecha = tk.Frame(ventana, bg="#f5f6fa")
    frame_fecha.pack(pady=10)

    tk.Label(frame_fecha, text="Selecciona una fecha:", bg="#f5f6fa", font=("Segoe UI", 11)).pack(side="left", padx=10)
    fecha_var = tk.StringVar()
    fecha_selector = DateEntry(
        frame_fecha, textvariable=fecha_var,
        date_pattern="dd/MM/yyyy",
        maxdate=None,   # permitimos seleccionar fechas futuras también
        background="#273c75", foreground="white",
        borderwidth=2, width=12
    )
    fecha_selector.pack(side="left")
    fecha_selector.set_date(date.today())

    # BOTONES SUPERIORES
    frame_superior = tk.Frame(ventana, bg="#f5f6fa")
    frame_superior.pack(fill="x", pady=(0, 5), padx=30)

    # -----------------------------
    # REPORTE POR RANGO DE FECHAS
    # -----------------------------
    def abrir_ventana_reporte():
        ventana_rango = tk.Toplevel(ventana)
        ventana_rango.title("Reporte por Rango de Fechas (Practicantes)")
        ventana_rango.geometry("350x220")
        ventana_rango.config(bg="#f5f6fa")
        ventana_rango.resizable(False, False)


        tk.Label(ventana_rango, text="Desde:", bg="#f5f6fa", font=("Segoe UI", 10)).pack(pady=(15, 5))
        fecha_desde = DateEntry(ventana_rango, date_pattern="dd/MM/yyyy", background="#273c75", foreground="white", width=12)
        fecha_desde.set_date(date.today() - timedelta(days=7))
        fecha_desde.pack()

        tk.Label(ventana_rango, text="Hasta:", bg="#f5f6fa", font=("Segoe UI", 10)).pack(pady=(10, 5))
        fecha_hasta = DateEntry(ventana_rango, date_pattern="dd/MM/yyyy", background="#273c75", foreground="white", width=12)
        fecha_hasta.set_date(date.today())
        fecha_hasta.pack()

        def generar_pdf_rango():
            f1 = datetime.strptime(fecha_desde.get(), "%d/%m/%Y").date()
            f2 = datetime.strptime(fecha_hasta.get(), "%d/%m/%Y").date()
            if f2 < f1:
                messagebox.showerror("Error", "La fecha final no puede ser anterior a la inicial.")
                return

            ruta_archivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivo PDF", "*.pdf")],
                title="Guardar reporte como"
            )
            if not ruta_archivo:
                return

            conexion = conectar_bd()
            cursor = conexion.cursor()

            doc = SimpleDocTemplate(ruta_archivo, pagesize=A4)
            story = []
            estilos = getSampleStyleSheet()
            estilo_titulo = estilos["Heading1"]
            estilo_subtitulo = estilos["Heading2"]

            rango_texto = f"📅 Reporte de asistencias (Practicantes) del {f1.strftime('%d/%m/%Y')} al {f2.strftime('%d/%m/%Y')}"
            story.append(Paragraph(rango_texto, estilo_titulo))
            story.append(Spacer(1, 12))

            fecha_actual = f1
            mes_actual = None
            items_en_pagina = 0

            while fecha_actual <= f2:
                mes_texto = fecha_actual.strftime("%B %Y").capitalize()
                if mes_texto != mes_actual:
                    if mes_actual is not None:
                        story.append(PageBreak())
                    mes_actual = mes_texto
                    story.append(Paragraph(mes_actual, estilo_titulo))
                    story.append(Spacer(1, 12))
                    items_en_pagina = 0

                # Título del día
                story.append(Paragraph(f"📅 {fecha_actual.strftime('%d de %B de %Y')}", estilo_subtitulo))
                story.append(Spacer(1, 6))

                fecha_consulta_db = fecha_actual.strftime("%d/%m/%Y")

                cursor.execute("""
                    SELECT p.dni, p.nombre, p.carrera, p.horario, ap.hora_entrada, ap.hora_salida
                    FROM practicantes p
                    LEFT JOIN asistencias_practicantes ap
                        ON p.id_practicante = ap.id_practicante
                        AND ap.fecha = ?
                    WHERE 
                        (p.fecha_registro IS NULL OR date(p.fecha_registro) <= ?)
                        AND (p.fecha_baja IS NULL OR date(p.fecha_baja) > ?)
                    ORDER BY p.nombre ASC
                """, (fecha_consulta_db, fecha_actual, fecha_actual))
                registros = cursor.fetchall()

                if not registros:
                    data = [["Sin registros para este día."]]
                    tabla = Table(data)
                    tabla.setStyle(TableStyle([
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]))
                else:
                    data = [["DNI", "Nombre", "Área", "Horario", "Entrada", "Salida"]]
                    for r in registros:
                        dni, nombre, area, horario, entrada, salida = r
                        data.append([dni or "", nombre, area or "", horario or "", entrada or "", salida or ""])
                    tabla = Table(data, repeatRows=1)
                    tabla.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273c75")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]))

                story.append(tabla)
                story.append(Spacer(1, 12))

                items_en_pagina += 1
                if items_en_pagina >= 6:
                    story.append(PageBreak())
                    items_en_pagina = 0

                fecha_actual += timedelta(days=1)

            conexion.close()

            def agregar_pie_pagina(canvas, doc):
                canvas.saveState()
                canvas.setFont("Helvetica-Oblique", 8)
                canvas.drawString(40, 20, "Reporte generado automáticamente por el sistema.")
                canvas.restoreState()

            doc.build(story, onFirstPage=agregar_pie_pagina, onLaterPages=agregar_pie_pagina)
            messagebox.showinfo("Éxito", "Reporte generado correctamente.")
            ventana_rango.destroy()

        ttk.Button(ventana_rango, text="📄 Generar Reporte", command=generar_pdf_rango).pack(pady=20)

    btn_reporte_rango = tk.Button(
        frame_superior, text="📅 Reporte por Fecha (Practicantes)",
        bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"),
        relief="flat", command=abrir_ventana_reporte
    )
    btn_reporte_rango.pack(side="left")

    # -----------------------------
    # REPORTE DIARIO
    # -----------------------------
    def generar_reporte_diario():
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivo PDF", "*.pdf")],
            title="Guardar reporte diario como"
        )
        if not ruta_archivo:
            return

        fecha_consulta = datetime.strptime(fecha_var.get(), "%d/%m/%Y").date()
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("""
          SELECT p.dni, p.nombre, p.carrera, p.horario, ap.hora_entrada, ap.hora_salida
          FROM practicantes p
          LEFT JOIN asistencias_practicantes ap
            ON p.id_practicante = ap.id_practicante
            AND ap.fecha = ?
          WHERE (p.fecha_registro IS NULL OR date(p.fecha_registro) <= ?)
          AND (p.fecha_baja IS NULL OR date(p.fecha_baja) > ?)
          ORDER BY p.nombre ASC
        """, (fecha_var.get(), fecha_consulta, fecha_consulta))
        registros = cursor.fetchall()
        conexion.close()

        doc = SimpleDocTemplate(ruta_archivo, pagesize=A4)
        estilos = getSampleStyleSheet()
        story = [
            Paragraph(f"Asistencia del {fecha_consulta.strftime('%d de %B de %Y')} (Practicantes)", estilos["Title"]),
            Spacer(1, 12)
        ]
        data = [["DNI", "Nombre", "Área", "Horario", "Entrada", "Salida"]]
        for r in registros:
            dni, nombre, area, horario, entrada, salida = r
            data.append([dni or "", nombre, area or "", horario or "", entrada or "", salida or ""])
        tabla_pdf = Table(data, repeatRows=1)
        tabla_pdf.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273c75")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(tabla_pdf)

        def pie_diario(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica-Oblique", 8)
            canvas.drawString(40, 20, "Reporte generado automáticamente por el sistema.")
            canvas.restoreState()

        doc.build(story, onFirstPage=pie_diario, onLaterPages=pie_diario)
        messagebox.showinfo("Éxito", "Reporte diario generado correctamente.")

    # --- BOTÓN ELIMINAR (marca fecha_baja en practicantes) ---
    def eliminar_practicante():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un practicante para eliminar.")
            return

        datos = tabla.item(seleccionado, "values")
        # values = (id_practicante, dni, nombre, telefono, area, horario, entrada, salida)
        id_pr = datos[0]
        nombre = datos[2]
        fecha_baja = datetime.strptime(fecha_var.get(), "%d/%m/%Y").date()

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Deseas eliminar a '{nombre}' desde el {fecha_baja.strftime('%d/%m/%Y')}?\n"
            f"Su historial anterior se conservará."
        )
        if not confirmar:
            return

        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("UPDATE practicantes SET fecha_baja = ? WHERE id_practicante = ?", (fecha_baja.strftime("%Y-%m-%d"), id_pr))
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Practicante eliminado", f"'{nombre}' fue dado de baja desde el {fecha_baja.strftime('%d/%m/%Y')}.")
        cargar_practicantes()

    btn_eliminar = tk.Button(
        frame_superior, text="🗑️ Eliminar Practicante",
        bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
        relief="flat", command=eliminar_practicante
    )
    btn_eliminar.pack(side="right")

    # TABLA DE PRACTICANTES
    marco_tabla = tk.Frame(ventana, bg="white", bd=3, relief="groove")
    marco_tabla.pack(pady=15, padx=30, fill="both", expand=True)

    columnas = ("id_practicante", "dni", "nombre", "telefono", "telefono_emerg", "area", "horario", "entrada", "salida")
    tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")

    scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla.yview)
    scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    tabla.pack(fill="both", expand=True)

    encabezados = {
        "id_practicante": "ID",
        "dni": "DNI",
        "nombre": "Nombres y Apellidos",
        "telefono": "Teléfono",
        "telefono_emerg": "Teléfono Emergencia",
        "area": "Área",
        "horario": "Horario",
        "entrada": "Entrada",
        "salida": "Salida"
    }
    for col, texto in encabezados.items():
        tabla.heading(col, text=texto)
        if col == "id_practicante":
            tabla.column(col, anchor="center", width=60)
        elif col == "dni":
            tabla.column(col, anchor="center", width=110)
        elif col == "nombre":
            tabla.column(col, anchor="w", width=220)
        else:
            tabla.column(col, anchor="center", width=130)

    def parsear_fecha(fecha_txt):
        """Convierte fechas YYYY-MM-DD o DD/MM/YYYY a objeto date()."""
        if not fecha_txt:
            return None
        try:
            return datetime.strptime(fecha_txt, "%Y-%m-%d").date()
        except:
            return datetime.strptime(fecha_txt, "%d/%m/%Y").date()

    # ================================================
    # EDICIÓN DE ENTRADA / SALIDA POR DOBLE CLIC
    # ================================================
    def editar_celda(event):
        item = tabla.identify_row(event.y)
        col = tabla.identify_column(event.x)

        if not item:
            return

        col_index = int(col.replace("#", "")) - 1
        columna_nombre = columnas[col_index]

        if columna_nombre not in ("entrada", "salida"):
            return

        valores = tabla.item(item, "values")
        id_pr = valores[0]
        fecha = fecha_var.get()

        x, y, ancho, alto = tabla.bbox(item, col)
        entrada_edit = tk.Entry(tabla, width=12)
        entrada_edit.place(x=x, y=y, width=ancho, height=alto)
        entrada_edit.insert(0, valores[col_index])
        entrada_edit.focus()

        def guardar_edicion(event=None):
            nuevo_valor = entrada_edit.get().strip()

            try:
                if len(nuevo_valor) == 5:
                    datetime.strptime(nuevo_valor, "%H:%M")
                else:
                    datetime.strptime(nuevo_valor, "%H:%M:%S")
            except:
                messagebox.showerror("Formato inválido", "Usa formato HH:MM o HH:MM:SS")
                entrada_edit.destroy()
                return

            tabla.set(item, columna_nombre, nuevo_valor)

            conexion = conectar_bd()
            cursor = conexion.cursor()

            if columna_nombre == "entrada":
                cursor.execute("""
                    SELECT id_asistencia, hora_salida
                    FROM asistencias_practicantes
                    WHERE id_practicante=? AND fecha=?
                """, (id_pr, fecha))
                fila = cursor.fetchone()
                if fila:
                    id_as = fila[0]
                    cursor.execute("""
                        UPDATE asistencias_practicantes
                        SET hora_entrada=?
                        WHERE id_asistencia=?
                    """, (nuevo_valor, id_as))
                else:
                    cursor.execute("""
                        INSERT INTO asistencias_practicantes (id_practicante, fecha, hora_entrada)
                        VALUES (?, ?, ?)
                    """, (id_pr, fecha, nuevo_valor))
            else:  # salida
                cursor.execute("""
                    UPDATE asistencias_practicantes
                    SET hora_salida=?
                    WHERE id_practicante=? AND fecha=?
                """, (nuevo_valor, id_pr, fecha))

            conexion.commit()
            conexion.close()
            entrada_edit.destroy()

        entrada_edit.bind("<Return>", guardar_edicion)
        entrada_edit.bind("<FocusOut>", guardar_edicion)

    tabla.bind("<Double-1>", editar_celda)

    # FUNCIONES INTERNAS
    def cargar_practicantes():
        fecha_consulta = datetime.strptime(fecha_var.get(), "%d/%m/%Y").date()

        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id_practicante, dni, nombre, telefono, telefono_emergencia, carrera, horario, fecha_registro, fecha_baja
            FROM practicantes
        """)
        registros = cursor.fetchall()
        tabla.delete(*tabla.get_children())

        for a in registros:
            id_p, dni, nombre, tel, tel_emerg, area, horario, f_reg, f_baja = a

            fecha_reg = parsear_fecha(f_reg)
            fecha_baja = parsear_fecha(f_baja)

            # Si aún no inicia → NO mostrar
            if fecha_reg and fecha_consulta < fecha_reg:
                continue

            # Si ya está dado de baja → NO mostrar
            if fecha_baja and fecha_consulta >= fecha_baja:
                continue

            cursor.execute("""
                SELECT hora_entrada, hora_salida
                FROM asistencias_practicantes
                WHERE id_practicante = ? AND fecha = ?
            """, (id_p, fecha_var.get()))
            asistencia = cursor.fetchone()
            entrada, salida = asistencia if asistencia else ("", "")

            tabla.insert("", "end", values=(id_p, dni or "", nombre, tel, tel_emerg, area, horario, entrada, salida))

        conexion.close()

    def registrar_asistencia(tipo):
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un practicante.")
            return
        datos = tabla.item(seleccionado, "values")
        # datos = (id_practicante, dni, nombre, telefono, area, horario, entrada, salida)
        id_pr = datos[0]
        hora = datetime.now().strftime("%H:%M:%S")
        conexion = conectar_bd()
        cursor = conexion.cursor()
        if tipo == "entrada":
            # Insert or update: buscamos si ya existe
            cursor.execute("""
                SELECT id_asistencia FROM asistencias_practicantes
                WHERE id_practicante=? AND fecha=?
            """, (id_pr, fecha_var.get()))
            fila = cursor.fetchone()
            if fila:
                cursor.execute("""
                    UPDATE asistencias_practicantes
                    SET hora_entrada=?
                    WHERE id_asistencia=?
                """, (hora, fila[0]))
            else:
                cursor.execute("""
                    INSERT INTO asistencias_practicantes (id_practicante, fecha, hora_entrada)
                    VALUES (?, ?, ?)
                """, (id_pr, fecha_var.get(), hora))
            tabla.set(seleccionado, "entrada", hora)
        else:
            # salida
            cursor.execute("""
                UPDATE asistencias_practicantes
                SET hora_salida=?
                WHERE id_practicante=? AND fecha=?
            """, (hora, id_pr, fecha_var.get()))
            tabla.set(seleccionado, "salida", hora)

        conexion.commit()
        conexion.close()

    # BOTONES INFERIORES
    frame_botones = tk.Frame(ventana, bg="#f5f6fa")
    frame_botones.pack(pady=15)

    estilo_boton = {
        "bg": "#dcdde1",
        "fg": "black",
        "font": ("Segoe UI", 11, "bold"),
        "width": 18,
        "height": 2,
        "relief": "ridge",
        "bd": 3
    }

    btn_cargar = tk.Button(frame_botones, text="🔄  Cargar", command=cargar_practicantes, **estilo_boton)
    btn_cargar.grid(row=0, column=0, padx=15)

    btn_entrada = tk.Button(frame_botones, text="🕓  Entrada", command=lambda: registrar_asistencia("entrada"), **estilo_boton)
    btn_entrada.grid(row=0, column=1, padx=15)

    btn_salida = tk.Button(frame_botones, text="🚪  Salida", command=lambda: registrar_asistencia("salida"), **estilo_boton)
    btn_salida.grid(row=0, column=2, padx=15)

    btn_pdf = tk.Button(frame_botones, text="📄  Generar Reporte PDF", command=generar_reporte_diario, **estilo_boton)
    btn_pdf.grid(row=0, column=3, padx=15)

    btn_cerrar = tk.Button(frame_botones, text="❌  Cerrar", command=ventana.destroy, bg="#b2bec3",
                       fg="black", font=("Segoe UI", 11, "bold"),
                       width=18, height=2, relief="raised", bd=3)
    btn_cerrar.grid(row=0, column=4, padx=15)

    cargar_practicantes()
    fecha_selector.bind("<<DateEntrySelected>>", lambda e: cargar_practicantes())

    # No ejecutar mainloop aquí para permitir import desde main.py
    return ventana

# Si querés probar en forma independiente descomenta lo siguiente:
# if __name__ == "__main__":
#     root = tk.Tk(); root.withdraw(); ventana_asistencia_practicantes(); root.mainloop()
