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
    locale.setlocale(locale.LC_TIME, "es_ES")

# ============================
# CONEXIÓN BASE DE DATOS
# ============================
def conectar_bd():
    return sqlite3.connect("control_asistencias.db")

def asegurar_columnas():
    """Asegura que existan las columnas necesarias (fecha_baja, fecha_registro, dni)."""
    conexion = conectar_bd()
    cursor = conexion.cursor()
    columnas = {
        "fecha_baja": "ALTER TABLE alumnos ADD COLUMN fecha_baja TEXT",
        "fecha_registro": "ALTER TABLE alumnos ADD COLUMN fecha_registro TEXT",
        "dni": "ALTER TABLE alumnos ADD COLUMN dni TEXT"
    }
    for comando in columnas.values():
        try:
            cursor.execute(comando)
            conexion.commit()
        except sqlite3.OperationalError:
            pass
    conexion.close()

# ============================
# VENTANA PRINCIPAL DE ASISTENCIA
# ============================
def ventana_asistencia_alumnos():
    asegurar_columnas()

    ventana = tk.Toplevel()
    ventana.title("Asistencia de Alumnos")
    ventana.geometry("1200x750")
    ventana.config(bg="#f5f6fa")
    ventana.resizable(True, True)  # la ventana es escalable


    # ENCABEZADO
    header = tk.Frame(ventana, bg="#273c75", height=70)
    header.pack(fill="x")

    titulo = tk.Label(header, text="🎓 CONTROL DE ASISTENCIA - ALUMNOS",
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
        maxdate=None,
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
        ventana_rango.title("Reporte por Rango de Fechas")
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

            # Encabezado del rango (aparece al inicio del PDF)
            rango_texto = f"📅 Reporte de asistencias del {f1.strftime('%d/%m/%Y')} al {f2.strftime('%d/%m/%Y')}"
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

                # Usar el mismo formato que se guarda (dd/mm/YYYY) para asi.fecha si así lo guardas
                fecha_consulta_db = fecha_actual.strftime("%d/%m/%Y")

                cursor.execute("""
                    SELECT a.dni, a.nombre, a.curso, a.horario, asi.hora_entrada, asi.hora_salida
                    FROM alumnos a
                    LEFT JOIN asistencias asi 
                        ON a.id_alumno = asi.id_persona 
                        AND asi.fecha = ? 
                        AND asi.tipo = 'Alumno'
                    WHERE 
                        (a.fecha_registro IS NULL OR date(a.fecha_registro) <= ?)
                        AND (a.fecha_baja IS NULL OR date(a.fecha_baja) > ?)
                    ORDER BY a.nombre ASC
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
                    # Agregamos DNI antes del nombre en la cabecera
                    data = [["DNI", "Nombre", "Curso", "Horario", "Entrada", "Salida"]]
                    for r in registros:
                        dni, nombre, curso, horario, entrada, salida = r
                        data.append([dni or "", nombre, curso or "", horario or "", entrada or "", salida or ""])
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
        frame_superior, text="📅 Reporte por Fecha",
        bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"),
        relief="flat", command=abrir_ventana_reporte
    )
    btn_reporte_rango.pack(side="left")

    # -----------------------------
    # REPORTE DIARIO (mantener funcionalidad)
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
          SELECT a.dni, a.nombre, a.curso, a.horario, asi.hora_entrada, asi.hora_salida
          FROM alumnos a
          LEFT JOIN asistencias asi ON a.id_alumno = asi.id_persona
          AND asi.fecha = ? AND asi.tipo='Alumno'
          WHERE (a.fecha_registro IS NULL OR date(a.fecha_registro)<=?)
          AND (a.fecha_baja IS NULL OR date(a.fecha_baja)>?)
          ORDER BY a.nombre ASC
        """, (fecha_var.get(), fecha_consulta, fecha_consulta))
        registros = cursor.fetchall()
        conexion.close()

        doc = SimpleDocTemplate(ruta_archivo, pagesize=A4)
        estilos = getSampleStyleSheet()
        story = [
            Paragraph(f"Asistencia del {fecha_consulta.strftime('%d de %B de %Y')}", estilos["Title"]),
            Spacer(1, 12)
        ]
        # Cabecera con DNI primero
        data = [["DNI", "Nombre", "Curso", "Horario", "Entrada", "Salida"]]
        for r in registros:
            dni, nombre, curso, horario, entrada, salida = r
            data.append([dni or "", nombre, curso or "", horario or "", entrada or "", salida or ""])
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

    # --- BOTÓN ELIMINAR (se mantiene igual, ajustar índices por nuevo orden de columnas) ---
    def eliminar_alumno():
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un alumno para eliminar.")
            return

        datos = tabla.item(seleccionado, "values")
        id_alumno = datos[0]
        nombre = datos[2]
        fecha_baja = datetime.strptime(fecha_var.get(), "%d/%m/%Y").date()
        hoy_str = fecha_baja.strftime("%Y-%m-%d")

        confirmar = messagebox.askyesno(
        "Confirmar eliminación",
        f"¿Deseas eliminar a '{nombre}' desde el {fecha_baja.strftime('%d/%m/%Y')}?\n"
        f"Su historial anterior se conservará."
        )
        if not confirmar:
            return

        conexion = conectar_bd()
        cursor = conexion.cursor()

    # Obtener la fecha de registro real
        cursor.execute("SELECT fecha_registro FROM alumnos WHERE id_alumno=?", (id_alumno,))
        res = cursor.fetchone()

        if res:
            fecha_registro = res[0]

        # ------------------------------
        # 🔥 CASO ESPECIAL:
        # Si lo elimino el MISMO día que lo registré → borrar completamente
        # ------------------------------
            try:
                fecha_registro_date = datetime.strptime(fecha_registro, "%Y-%m-%d").date()
            except:
                fecha_registro_date = datetime.strptime(fecha_registro, "%d/%m/%Y").date()

            if fecha_registro_date == fecha_baja:
                cursor.execute("DELETE FROM alumnos WHERE id_alumno=?", (id_alumno,))
                conexion.commit()
                conexion.close()
                messagebox.showinfo("Eliminado", f"'{nombre}' fue eliminado COMPLETAMENTE (mismo día de registro).")
                cargar_alumnos()
                return

    # -------------------------------------
    # Eliminación normal → marcar fecha_baja
    # -------------------------------------
        cursor.execute("UPDATE alumnos SET fecha_baja=? WHERE id_alumno=?", (hoy_str, id_alumno))
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Alumno eliminado", f"'{nombre}' fue dado de baja desde el {fecha_baja.strftime('%d/%m/%Y')}.")
        cargar_alumnos()

    btn_eliminar = tk.Button(
        frame_superior, text="🗑️ Eliminar Alumno",
        bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"),
        relief="flat", command=eliminar_alumno
    )
    btn_eliminar.pack(side="right")

    # TABLA DE ALUMNOS (con scroll horizontal y vertical)
    marco_tabla = tk.Frame(ventana, bg="white", bd=3, relief="groove")
    marco_tabla.pack(pady=15, padx=30, fill="both", expand=True)

    # Ajustamos columnas para incluir DNI antes del nombre
    columnas = ("id_alumno", "dni", "nombre", "telefono", "curso", "horario", "entrada", "salida")
    tabla = ttk.Treeview(marco_tabla, columns=columnas, show="headings")

    scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla.yview)
    scroll_x = ttk.Scrollbar(marco_tabla, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    tabla.pack(fill="both", expand=True)

    encabezados = {
        "id_alumno": "ID",
        "dni": "DNI",
        "nombre": "Nombres y Apellidos",
        "telefono": "Teléfono",
        "curso": "Curso",
        "horario": "Horario",
        "entrada": "Entrada",
        "salida": "Salida"
    }
    for col, texto in encabezados.items():
        tabla.heading(col, text=texto)
        # ancho por columna razonable
        if col == "id_alumno":
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
#   EDICIÓN DE ENTRADA / SALIDA POR DOBLE CLIC
# ================================================
    def editar_celda(event):
        item = tabla.identify_row(event.y)
        col = tabla.identify_column(event.x)

        if not item:
            return

        col_index = int(col.replace("#", "")) - 1
        columna_nombre = columnas[col_index]

        # Solo permitir editar entrada o salida
        if columna_nombre not in ("entrada", "salida"):
            return

        valores = tabla.item(item, "values")
        id_alumno = valores[0]
        fecha = fecha_var.get()

        # Posición de la celda dentro del treeview
        x, y, ancho, alto = tabla.bbox(item, col)

        # Crear un Entry encima de la celda
        entrada_edit = tk.Entry(tabla, width=12)
        entrada_edit.place(x=x, y=y, width=ancho, height=alto)

        # Valor actual
        entrada_edit.insert(0, valores[col_index])
        entrada_edit.focus()

        def guardar_edicion(event=None):
            nuevo_valor = entrada_edit.get().strip()

             # Validar formato HH:MM o HH:MM:SS
            try:
                if len(nuevo_valor) == 5:
                  datetime.strptime(nuevo_valor, "%H:%M")
                else:
                  datetime.strptime(nuevo_valor, "%H:%M:%S")
            except:
                messagebox.showerror("Formato inválido",
                                 "Usa formato HH:MM o HH:MM:SS")
                entrada_edit.destroy()
                return

        # Actualizar en la tabla visual
            tabla.set(item, columna_nombre, nuevo_valor)

        # Guardar en BD
            conexion = conectar_bd()
            cursor = conexion.cursor()

        # =================================
        # FIX: EDITAR ENTRADA SIN BORRAR SALIDA
        # =================================
            if columna_nombre == "entrada":

            # Buscar si ya existe asistencia para ese alumno y fecha
                cursor.execute("""
                    SELECT id_asistencia, hora_salida
                    FROM asistencias
                    WHERE id_persona=? AND fecha=? AND tipo='Alumno'
                """, (id_alumno, fecha))

                fila = cursor.fetchone()

                if fila:
                # Ya existe el registro → actualizar sin duplicar
                    id_asistencia, hora_salida_existente = fila

                    cursor.execute("""
                        UPDATE asistencias
                        SET hora_entrada=?
                        WHERE id_asistencia=?
                    """, (nuevo_valor, id_asistencia))

                else:
                # No existe registro → insertar uno nuevo (caso raro)
                    cursor.execute("""
                        INSERT INTO asistencias (tipo, id_persona, fecha, hora_entrada)
                        VALUES ('Alumno', ?, ?, ?)
                    """, (id_alumno, fecha, nuevo_valor))

            else:  # ====== EDITAR SALIDA ======
                cursor.execute("""
                    UPDATE asistencias
                    SET hora_salida=?
                    WHERE id_persona=? AND fecha=? AND tipo='Alumno'
                """, (nuevo_valor, id_alumno, fecha))


            conexion.commit()
            conexion.close()

            entrada_edit.destroy()

    # Guardar con Enter o al perder foco
        entrada_edit.bind("<Return>", guardar_edicion)
        entrada_edit.bind("<FocusOut>", guardar_edicion)

    tabla.bind("<Double-1>", editar_celda)







    # FUNCIONES INTERNAS
    def cargar_alumnos():
        fecha_consulta = datetime.strptime(fecha_var.get(), "%d/%m/%Y").date()

        conexion = conectar_bd()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT id_alumno, dni, nombre, telefono, curso, horario, fecha_registro, fecha_baja 
            FROM alumnos
        """)
        registros = cursor.fetchall()

        tabla.delete(*tabla.get_children())

        for a in registros:
            id_a, dni, nombre, tel, curso, horario, f_reg, f_baja = a

            # --- manejo seguro de fechas (nuevo) ---
            fecha_reg = parsear_fecha(f_reg)
            fecha_baja = parsear_fecha(f_baja)

            # Si aún no inicia → NO mostrar
            if fecha_reg and fecha_consulta < fecha_reg:
                continue

            # Si ya está dado de baja → NO mostrar
            if fecha_baja and fecha_consulta >= fecha_baja:
                continue

            # Obtener asistencia para ese día
            cursor.execute("""
                SELECT hora_entrada, hora_salida 
                FROM asistencias
                WHERE id_persona = ? AND fecha = ? AND tipo='Alumno'
            """, (id_a, fecha_var.get()))
            
            asistencia = cursor.fetchone()
            entrada, salida = asistencia if asistencia else ("", "")

            tabla.insert(
                "", "end",
                values=(id_a, dni or "", nombre, tel, curso, horario, entrada, salida)
            )

        conexion.close()


    def registrar_asistencia(tipo):
        seleccionado = tabla.focus()
        if not seleccionado:
            messagebox.showwarning("Atención", "Selecciona un alumno.")
            return
        datos = tabla.item(seleccionado, "values")
        # datos = (id_alumno, dni, nombre, telefono, curso, horario, entrada, salida)
        id_alumno = datos[0]
        hora = datetime.now().strftime("%H:%M:%S")
        conexion = conectar_bd()
        cursor = conexion.cursor()
        if tipo == "entrada":
            # Guardar fecha en el mismo formato que usa la UI: dd/MM/yyyy
            cursor.execute("""
                INSERT OR REPLACE INTO asistencias (id_asistencia, tipo, id_persona, fecha, hora_entrada)
                VALUES (
                  (SELECT id_asistencia FROM asistencias WHERE id_persona=? AND fecha=? AND tipo='Alumno'),
                  'Alumno', ?, ?, ?
                )
            """, (id_alumno, fecha_var.get(), id_alumno, fecha_var.get(), hora))
            tabla.set(seleccionado, "entrada", hora)
        else:
            cursor.execute("""
                UPDATE asistencias SET hora_salida=? 
                WHERE id_persona=? AND fecha=? AND tipo='Alumno'
            """, (hora, id_alumno, fecha_var.get()))
            tabla.set(seleccionado, "salida", hora)
        conexion.commit()
        conexion.close()

# BOTONES INFERIORES GRANDES (como antes)
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

    btn_cargar = tk.Button(frame_botones, text="🔄  Cargar", command=cargar_alumnos, **estilo_boton)
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


    cargar_alumnos()
    fecha_selector.bind("<<DateEntrySelected>>", lambda e: cargar_alumnos())
    return ventana

# Ejecutar la ventana principal si se ejecuta este archivo directamente
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    ventana_asistencia_alumnos()
    