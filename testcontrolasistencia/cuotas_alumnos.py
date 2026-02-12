# cuotas_alumnos.py
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB = "control_asistencias.db"

def conectar_bd():
    return sqlite3.connect(DB)

# ===========================
# Interfaz principal
# ===========================
def ventana_cuotas():

    ventana = tk.Toplevel()
    ventana.title("💰 Control de Cuotas de Alumnos")
    ventana.geometry("1000x700")
    ventana.configure(bg="#f4f7fc")
    ventana.resizable(True, True)




    header = tk.Label(ventana, text="💰 Control de Cuotas por Alumno",
                      bg="#0078D7", fg="white", font=("Segoe UI", 15, "bold"), pady=10)
    header.pack(fill=tk.X)

    # Contenedor principal con scroll (vertical + horizontal)
    cont = tk.Frame(ventana, bg="#f4f7fc")
    cont.pack(fill="both", expand=True)

    canvas = tk.Canvas(cont, bg="#f4f7fc", highlightthickness=0)
    h_scroll = ttk.Scrollbar(cont, orient="horizontal", command=canvas.xview)
    v_scroll = ttk.Scrollbar(cont, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    h_scroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    interior = tk.Frame(canvas, bg="#f4f7fc")
    canvas_window = canvas.create_window((0, 0), window=interior, anchor="nw")

    def ajustar_scroll(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfigure(canvas_window, width=canvas.winfo_width())

    interior.bind("<Configure>", ajustar_scroll)
    canvas.bind("<Configure>", ajustar_scroll)

    # ============= Top: cursos como botones largos =============
    cursos_frame = tk.Frame(interior, bg="#f4f7fc")
    cursos_frame.pack(fill="x", padx=12, pady=(12, 6))

    tk.Label(cursos_frame, text="Cursos:", bg="#f4f7fc", font=("Segoe UI", 11, "bold")).pack(anchor="w")

    botones_cursos_container = tk.Frame(cursos_frame, bg="#f4f7fc")
    botones_cursos_container.pack(fill="x", pady=(6, 0))

    curso_panels_container = tk.Frame(interior, bg="#f4f7fc")
    curso_panels_container.pack(fill="both", expand=True, padx=12, pady=8)

    # ================== helpers BD ==================
    def obtener_cursos():
        c = conectar_bd()
        cur = c.cursor()
        cur.execute("SELECT nombre_curso FROM cursos ORDER BY nombre_curso")
        rows = [r[0] for r in cur.fetchall()]
        c.close()
        return rows

    def cargar_alumnos_por_curso_db(curso):
        c = conectar_bd()
        cur = c.cursor()
        cur.execute("""
            SELECT id_alumno, dni, nombre, curso FROM alumnos
            WHERE curso = ? OR curso LIKE ?
            ORDER BY nombre
        """, (curso, f"%{curso}%"))
        rows = cur.fetchall()
        c.close()
        return rows

    def obtener_pagos_confirmados(id_alumno, curso):
        c = conectar_bd()
        cur = c.cursor()
        cur.execute("""
            SELECT cuota_num, fecha, metodo
            FROM pagos_cuotas
            WHERE id_alumno=? AND curso=?
            ORDER BY cuota_num
        """, (id_alumno, curso))

        filas = {r[0]: {"fecha": r[1], "metodo": r[2]} for r in cur.fetchall()}

        c.close()
        return filas

    def esta_habilitado_bd(id_alumno, curso):
        c = conectar_bd()
        cur = c.cursor()
        cur.execute("SELECT habilitado FROM cuotas_estado WHERE id_alumno=? AND curso=?",
                    (id_alumno, curso))
        r = cur.fetchone()
        c.close()
        return True if (r is None or r[0] == 1) else False

    def set_habilitado_bd(id_alumno, curso, val):
        c = conectar_bd()
        cur = c.cursor()
        cur.execute("""
            INSERT INTO cuotas_estado (id_alumno, curso, habilitado)
            VALUES (?, ?, ?)
            ON CONFLICT(id_alumno, curso) DO UPDATE SET habilitado=excluded.habilitado
        """, (id_alumno, curso, val))
        c.commit()
        c.close()

    def guardar_pago_bd(id_alumno, curso, cuota_num, metodo, fecha_yyyy_mm_dd):
        c = conectar_bd()
        cur = c.cursor()

        cur.execute("""
            INSERT INTO pagos_cuotas (id_alumno, curso, cuota_num, metodo, fecha, confirmado)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(id_alumno, curso, cuota_num) 
            DO UPDATE SET metodo=excluded.metodo, fecha=excluded.fecha, confirmado=1
        """, (id_alumno, curso, cuota_num, metodo, fecha_yyyy_mm_dd))

        c.commit()
        c.close()

    # ================== UI por curso ==================
    panels = {}

    def toggle_curso(curso):

        for c, info in panels.items():
            if c != curso and info["open"]:
                info["frame"].pack_forget()
                info["open"] = False

        info = panels.get(curso)
        if not info:
            return

        if info["open"]:
            info["frame"].pack_forget()
            info["open"] = False
        else:
            info["frame"].pack(fill="x", padx=6, pady=6)
            info["open"] = True
            refrescar_panel_curso(curso)

    def crear_botones_cursos():
        for w in botones_cursos_container.winfo_children():
            w.destroy()

        cursos = obtener_cursos()
        for curso in cursos:
            btn = tk.Button(
                botones_cursos_container,
                text=curso,
                anchor="w",
                font=("Segoe UI", 11, "bold"),
                bg="#dcdde1",
                fg="black",
                relief="ridge",
                bd=2,
                pady=8
            )
            btn.pack(fill="x", pady=4)
            btn.configure(command=lambda c=curso: toggle_curso(c))

            if curso not in panels:
                pframe = tk.Frame(curso_panels_container, bg="#eef3fa", bd=1, relief="solid")

                header = tk.Frame(pframe, bg="#eef3fa")
                header.pack(fill="x", padx=6, pady=6)
                tk.Label(header, text=f"{curso}", bg="#eef3fa", font=("Segoe UI", 12, "bold")).pack(
                    side="left", padx=(2, 6))

                busca_frame = tk.Frame(header, bg="#eef3fa")
                busca_frame.pack(side="right")
                
                entrada_var = tk.StringVar()
                entry_buscar = ttk.Entry(busca_frame, width=20, textvariable=entrada_var)
                entry_buscar.pack(side="left", padx=(0, 6))


            # Búsqueda al presionar Enter
                entry_buscar.bind(
                "<Return>",
                lambda event, c=curso, v=entrada_var: buscar_por_dni(c, v.get().strip())
            )

            # Actualizar lista automáticamente cuando cambie el texto
                entrada_var.trace_add(
                "write",
                lambda *args, c=curso, v=entrada_var: buscar_por_dni(c, v.get().strip())
            )


            # Botón de búsqueda (opcional)
                btn_buscar = ttk.Button(
                    busca_frame, text="Buscar DNI",
                    command=lambda c=curso, v=entrada_var: buscar_por_dni(c, v.get().strip())
                )
                btn_buscar.pack(side="left")

                list_container = tk.Frame(pframe, bg="#eef3fa")
                list_container.pack(fill="x", padx=6, pady=(2, 10))

                panels[curso] = {
                "frame": pframe,
                "list_container": list_container,
                "open": False,
                "search_entry": entry_buscar,
                "search_var": entrada_var
                }

    def refrescar_panel_curso(curso, filtro_dni=None):
        info = panels.get(curso)
        cont = info["list_container"]

    # Limpiar panel
        for w in cont.winfo_children():
            w.destroy()

        alumnos = cargar_alumnos_por_curso_db(curso)
        if filtro_dni:
            alumnos = [a for a in alumnos if filtro_dni in (a[1] or "")]

        for a in alumnos:
            id_a, dni, nombre, curso_db = a
            habil = esta_habilitado_bd(id_a, curso)

            fila = tk.Frame(cont, bg="#ffffff" if habil else "#e6e6e6", bd=1, relief="flat")
            fila.pack(fill="x", pady=4, padx=2)

        # toggle habilitar / deshabilitar
            def make_toggle(id_alumno=id_a, curso_local=curso):
                def toggle():
                    cur_state = esta_habilitado_bd(id_alumno, curso_local)
                    nuevo = 0 if cur_state else 1
                    set_habilitado_bd(id_alumno, curso_local, nuevo)
                    refrescar_panel_curso(curso_local)
                return toggle

            btn_toggle = tk.Button(
                fila,
                text=("Deshabilitar" if habil else "Habilitar"),
                bg=("#e74c3c" if habil else "#2e86de"),
                fg="white",
                font=("Segoe UI", 9, "bold"),
                width=12,
                command=make_toggle()
            )
            btn_toggle.pack(side="left", padx=6, pady=6)

            etiqueta = tk.Label(
                fila, text=f"{dni or ''}  |  {nombre}",
                anchor="w", font=("Segoe UI", 10),
                bg=fila.cget("bg")
            )
            etiqueta.pack(side="left", padx=6, fill="x", expand=True)

            pagos = obtener_pagos_confirmados(id_a, curso)
            max_confirmado = max(pagos) if pagos else 0

        # Canvas horizontal para cuotas
            cuotas_canvas = tk.Canvas(fila, height=40, bg=fila.cget("bg"), highlightthickness=0)
            cuotas_canvas.pack(side="right", fill="x", expand=True)

            h_scroll_cuotas = ttk.Scrollbar(fila, orient="horizontal", command=cuotas_canvas.xview)
            h_scroll_cuotas.pack(side="bottom", fill="x")

            cuotas_canvas.configure(xscrollcommand=h_scroll_cuotas.set)

            cuotas_frame = tk.Frame(cuotas_canvas, bg=fila.cget("bg"))
            cuotas_canvas_window = cuotas_canvas.create_window((0, 0), window=cuotas_frame, anchor="nw")

            def actualizar_scroll_cuotas(event=None):
                cuotas_canvas.configure(scrollregion=cuotas_canvas.bbox("all"))

            cuotas_frame.bind("<Configure>", actualizar_scroll_cuotas)

        # Crear botón de cuota
            def crear_boton_cuota(cuota_num, id_alumno=id_a, curso_local=curso):
                est_confirmado = cuota_num in pagos

                if est_confirmado:
                    fecha_sql = pagos[cuota_num]["fecha"]
                    aa, mm, dd = fecha_sql.split("-")
                    texto = f"{dd}/{mm}/{aa}"
                    bg = "#7bd67b" if habil else "#a5d6a7"
                else:
                    texto = f"Cuota {cuota_num}"
                    bg = "#dcdde1" if habil else "#cccccc"

                btn = tk.Button(
                    cuotas_frame,
                    text=texto,
                    bg=bg,
                    fg="black",
                    font=("Segoe UI", 10),
                    relief="raised",
                    bd=2,
                    width=12
                )
                btn.pack(side="left", padx=4)

                if not habil:
                    btn.configure(state="disabled")

                def on_click(id_alumno=id_alumno, curso_local=curso_local, cuota=cuota_num):
                    abrir_modal_pago(id_alumno, curso_local, cuota, lambda: refrescar_panel_curso(curso_local))

                btn.configure(command=on_click)

            for q in range(1, max_confirmado + 2):
                crear_boton_cuota(q)


    # ================================
    # MODAL DE PAGO (con EDITAR)
    # ================================
    def abrir_modal_pago(id_alumno, curso, cuota_num, callback):
        modal = tk.Toplevel(ventana)
        modal.title(f"Pagar {curso} - Cuota {cuota_num}")
        modal.geometry("360x280")
        modal.transient(ventana)
        modal.grab_set()

        tk.Label(modal, text=f"Alumno ID: {id_alumno}", font=("Segoe UI", 10)).pack(pady=(8, 4))
        tk.Label(modal, text=f"Curso: {curso}", font=("Segoe UI", 10, "bold")).pack(pady=(0, 8))

        pagos = obtener_pagos_confirmados(id_alumno, curso)
        ya_pagado = cuota_num in pagos

        tk.Label(modal, text="Método de pago:", font=("Segoe UI", 10)).pack(anchor="w", padx=12)
        metodo_var = tk.StringVar(value="Yape")
        opciones = ["Yape", "Plin", "Transferencia", "Efectivo"]
        combo = ttk.Combobox(modal, values=opciones, state="readonly", textvariable=metodo_var)
        combo.pack(fill="x", padx=12, pady=(2, 8))
        combo.current(0)

        fecha_frame = tk.Frame(modal)
        fecha_frame.pack(pady=6)
        tk.Label(fecha_frame, text="Fecha (DD  MM  AA):").grid(row=0, column=0, columnspan=3, sticky="w", padx=6)

        e_dd = ttk.Entry(fecha_frame, width=4)
        e_mm = ttk.Entry(fecha_frame, width=4)
        e_aa = ttk.Entry(fecha_frame, width=6)

        e_dd.grid(row=1, column=0, padx=(6, 4))
        e_mm.grid(row=1, column=1, padx=4)
        e_aa.grid(row=1, column=2, padx=(4, 6))

        # Si ya está pagado → mostrar datos y deshabilitar
        if ya_pagado:
            fecha_sql = pagos[cuota_num]["fecha"]
            metodo_guardado = pagos[cuota_num]["metodo"]

            aa, mm, dd = fecha_sql.split("-")
            e_dd.insert(0, dd)
            e_mm.insert(0, mm)
            e_aa.insert(0, aa)

            metodo_var.set(metodo_guardado)

            combo.configure(state="disabled")
            e_dd.configure(state="disabled")
            e_mm.configure(state="disabled")
            e_aa.configure(state="disabled")

            # ========================
            # BOTÓN EDITAR
            # ========================
            def habilitar_edicion():
                combo.configure(state="readonly")
                e_dd.configure(state="normal")
                e_mm.configure(state="normal")
                e_aa.configure(state="normal")
                btn_editar.pack_forget()

            btn_editar = tk.Button(
                modal,
                text="Editar",
                bg="#d63031",
                fg="white",
                font=("Segoe UI", 10, "bold"),
                command=habilitar_edicion
            )
            btn_editar.pack(pady=8)

        # ================================
        # CONFIRMAR
        # ================================
        def confirmar():
            dd, mm, aa = e_dd.get(), e_mm.get(), e_aa.get()

            if not (dd.isdigit() and mm.isdigit() and aa.isdigit()):
                messagebox.showerror("Fecha inválida", "Introduce fecha válida en dígitos.")
                return

            try:
                dd_i, mm_i, aa_i = int(dd), int(mm), int(aa)
                if not (1 <= dd_i <= 31 and 1 <= mm_i <= 12):
                    raise ValueError()

                aa_full = 2000 + aa_i if len(aa) == 2 else aa_i
                fecha_str = f"{aa_full:04d}-{mm_i:02d}-{dd_i:02d}"

            except:
                messagebox.showerror("Fecha inválida", "Formato incorrecto.")
                return

            guardar_pago_bd(id_alumno, curso, cuota_num, metodo_var.get(), fecha_str)
            messagebox.showinfo("Confirmado", f"Pago registrado/actualizado: Cuota {cuota_num}")
            modal.destroy()
            callback()

        tk.Button(modal, text="Confirmar", command=confirmar).pack(side="left", padx=20, pady=12)
        tk.Button(modal, text="Cancelar", command=modal.destroy).pack(side="right", padx=20, pady=12)

    # ========================================================
    def buscar_por_dni(curso, dni):
        refrescar_panel_curso(curso, filtro_dni=dni)

    crear_botones_cursos()

    def refrescar_todo():
        crear_botones_cursos()
        for curso, info in panels.items():
            if info["open"]:
                refrescar_panel_curso(curso)

    ventana.refrescar_cuotas = refrescar_todo

    footer_frame = tk.Frame(ventana, bg="#f4f7fc")
    footer_frame.pack(fill="x", pady=(6, 12))
    ttk.Button(footer_frame, text="Actualizar listado", command=refrescar_todo).pack(side="left", padx=12)

    tk.Button(
        footer_frame, text="Cerrar", command=ventana.destroy,
        bg="#0078D7", fg="white",
        font=("Segoe UI", 10, "bold"),
        relief="flat", width=12
    ).pack(side="right", padx=12)

    ajustar_scroll()

    return ventana


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    ventana_cuotas()
    root.mainloop()

