import flet as ft
from conexion_sql import ConexionSQL
import pyodbc
import csv
from datetime import datetime
from typing import List, Dict

def main(page: ft.Page):
    # Configuración de la página
    page.title = "SIGES - Sistema de Gestión"
    page.window_width = 1200
    page.window_height = 800
    page.bgcolor = "#e6ebe0"  # Fondo violeta oscuro
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0

    # Variables de estado
    current_connection = None
    tablas_disponibles: List[str] = []
    estructura_tablas: Dict[str, List[Dict]] = {}

    # Variables para formularios dinámicos
    form_fields = []  
    dropdown_tablas: ft.Dropdown = None  
    btn_guardar: ft.ElevatedButton = None  
    formulario: ft.Column = None

    # Área dinámica de contenido (donde se carga tabla o formulario)
    content_area = ft.Container(expand=True, padding=10, bgcolor="#E6EBE0", border_radius=ft.border_radius.all(8))

    # DataTable para visualizar registros
    tbl_datos = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Seleccione una tabla", color="#000000"))],
        rows=[],
        width=1100,
        heading_row_color="#F4F1BB",  # Pale Spring Bud
        heading_text_style=ft.TextStyle(color="#000000"),
        data_row_color={"hovered": "#E6EBE0"},  # Alabaster
        border=ft.border.all(1, "#000000"),
        border_radius=8,
        horizontal_lines=ft.border.BorderSide(1, "#ED6A5A"),  # Terra Cotta
        column_spacing=20
    )

    # Navbar superior (se mantiene sin cambios)
    navbar = ft.Container(
        content=ft.Row(
            [
                ft.Text("SIGES", size=24, weight=ft.FontWeight.BOLD, color="#ED6A5A"),  # Terra Cotta
                ft.Container(width=20),
                ft.TextField(
                    hint_text="BUSCAR...",
                    border_color="#000000",
                    bgcolor="#E6EBE0",
                    text_style=ft.TextStyle(color="#000000"),
                    width=300
                ),
                ft.ElevatedButton(
                    "INICIO",
                    bgcolor=ft.colors.WHITE,
                    color="#ED6A5A",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor="#F4F1BB",  # Pale Spring Bud
        padding=15,
        border_radius=ft.border_radius.only(top_left=10, top_right=10)
    )

    # Funciones generales de mensajes y actualización
    def mostrar_mensaje(mensaje: str, error: bool = False):
        status_bar.value = mensaje
        status_bar.color = ft.colors.RED if error else "#7B1FA2"
        page.update()

    # Cargar estructura de la BD (tablas y columnas)
    def cargar_estructura_bd():
        nonlocal tablas_disponibles, estructura_tablas
        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tablas_disponibles = [row[0] for row in cursor.fetchall()]
            for tabla in tablas_disponibles:
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{tabla}'
                    ORDER BY ORDINAL_POSITION
                """)
                estructura_tablas[tabla] = [
                    {"nombre": row[0], "tipo": row[1]} for row in cursor.fetchall()
                ]
            actualizar_lista_tablas()
            mostrar_mensaje(f"Estructura cargada: {len(tablas_disponibles)} tablas")
        except Exception as e:
            mostrar_mensaje(f"Error: {str(e)}", error=True)

    # Actualizar el dropdown de tablas
    def actualizar_lista_tablas():
        dropdown_tablas.options = [
            ft.dropdown.Option(tabla) for tabla in tablas_disponibles
        ]
        # Después de cargar las opciones:
        if dropdown_tablas.options:
            dropdown_tablas.value = dropdown_tablas.options[0].key

        page.update()

    # Función para visualizar registros de la tabla
    def cargar_datos_tabla(tabla: str):
        nonlocal current_connection
        try:
            if current_connection:
                current_connection.close()
            current_connection = ConexionSQL.conectar()
            cursor = current_connection.cursor()
            cursor.execute(f"SELECT TOP 50 * FROM {tabla}")

            # Configurar columnas con tooltips
            columnas = []
            for col in cursor.description:
                nombre_columna = col[0] if col[0] else "Columna"
                tooltip_text = f"{nombre_columna} ({col[1]})" if col[1] else nombre_columna
                columnas.append(
                    ft.DataColumn(
                        ft.Text(nombre_columna, color="#000000", weight="bold"),
                        tooltip=tooltip_text if tooltip_text else None
                    )
                )

            # Configurar filas con tooltips
            filas = []
            for row in cursor.fetchall():
                celdas = []
                for valor in row:
                    texto = str(valor)[:50] + "..." if valor and len(str(valor)) > 50 else str(valor) if valor is not None else "NULL"
                    tooltip_valor = str(valor) if valor is not None else "NULL"
                    celdas.append(
                        ft.DataCell(
                                    ft.Container(
                                        content=ft.Text(texto, color="#000000", size=12),
                                        tooltip=tooltip_valor if tooltip_valor else ""
                                    )
                                )

                    )
                filas.append(ft.DataRow(cells=celdas))

            tbl_datos.columns = columnas
            tbl_datos.rows = filas
            mostrar_mensaje(f"{tabla}: {len(filas)} registros cargados")
            # Mostrar la tabla en el área dinámica
            content_area.content = ft.ListView([tbl_datos], expand=True, auto_scroll=True)
        except Exception as e:
            mostrar_mensaje(f"Error al cargar {tabla}: {str(e)}", error=True)
            tbl_datos.columns = [ft.DataColumn(ft.Text("Error", color=ft.colors.RED))]
            tbl_datos.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(e), color=ft.colors.RED))])]
            content_area.content = ft.ListView([tbl_datos], expand=True)
        finally:
            page.update()

    # Función para cargar formulario dinámico para agregar registro
    def actualizar_formulario_agregar():
        tabla = dropdown_tablas.value
        if not tabla:
            return

        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{tabla}'
            """)
            columnas = cursor.fetchall()
            conn.close()
        except Exception as e:
            mostrar_mensaje(f"Error: {str(e)}", error=True)
            return

        # Limpiar formulario anterior
        formulario.controls.clear()
        form_fields.clear()

        for columna, tipo in columnas:
            # Determinar tipo de campo según SQL Server
            if "int" in tipo or "decimal" in tipo:
                input_type = "number"
            elif "date" in tipo:
                input_type = "date"
            else:
                input_type = "text"

            campo = ft.TextField(
                label=columna, 
                width=300, 
                tooltip=f"Tipo: {tipo}",
                bgcolor="#ffffff",
                text_style=ft.TextStyle(color="#000000"),
                input_filter=input_type
            )
            form_fields.append((columna, campo))
            formulario.controls.append(campo)
        btn_guardar.text = "Agregar Registro"
        btn_guardar.visible = True
        # Mostrar formulario en el área dinámica
        content_area.content = formulario
        page.update()

    # Función para guardar registro (para agregar)
    def guardar_registro():
        tabla = dropdown_tablas.value
        if not tabla:
            mostrar_mensaje("Seleccione una tabla", error=True)
            return

        datos = {col: campo.value for col, campo in form_fields}

        # Validar que los campos no estén vacíos
        if any(valor.strip() == "" for valor in datos.values()):
            mostrar_mensaje("Todos los campos son obligatorios", error=True)
            return

        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            columnas = ", ".join(datos.keys())
            valores_placeholder = ", ".join(["?" for _ in datos])
            valores = tuple(datos.values())
            query = f"INSERT INTO {tabla} ({columnas}) VALUES ({valores_placeholder})"
            cursor.execute(query, valores)
            conn.commit()
            conn.close()

            mostrar_mensaje("Registro guardado con éxito")
            # Limpiar formulario
            for _, campo in form_fields:
                campo.value = ""
            page.update()
        except Exception as e:
            mostrar_mensaje(f"Error: {str(e)}", error=True)

    # Función para cargar formulario para eliminación (usando la clave primaria, se asume que es la primera columna)
    def actualizar_formulario_eliminar():
        tabla = dropdown_tablas.value
        if not tabla:
            return
        # Limpiar formulario anterior
        formulario.controls.clear()
        form_fields.clear()
        try:
            # Se asume que la primera columna es la clave primaria
            primer_campo = estructura_tablas[tabla][0]["nombre"]
        except Exception as e:
            mostrar_mensaje(f"Error obteniendo clave primaria: {str(e)}", error=True)
            return
        campo = ft.TextField(
            label=f"Ingrese {primer_campo} a eliminar", 
            width=300, 
            tooltip="Clave primaria",
            bgcolor="#ffffff",
            text_style=ft.TextStyle(color="#000000")
        )
        form_fields.append((primer_campo, campo))
        formulario.controls.append(campo)
        btn_guardar.text = "Eliminar Registro"
        btn_guardar.visible = True
        content_area.content = formulario
        page.update()

    # Función para eliminar registro (basado en la clave primaria)
    def eliminar_registro():
        tabla = dropdown_tablas.value
        if not tabla:
            mostrar_mensaje("Seleccione una tabla", error=True)
            return
        clave, campo = form_fields[0]
        valor = campo.value
        if not valor.strip():
            mostrar_mensaje("Debe ingresar el valor de la clave primaria", error=True)
            return
        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            query = f"DELETE FROM {tabla} WHERE {clave} = ?"
            cursor.execute(query, (valor,))
            conn.commit()
            conn.close()
            mostrar_mensaje("Registro eliminado con éxito")
            campo.value = ""
            page.update()
        except Exception as e:
            mostrar_mensaje(f"Error: {str(e)}", error=True)

    # Función para cargar formulario para modificar registro
    # Se solicita primero el valor de la clave primaria para cargar los datos actuales
    def actualizar_formulario_modificar():
        tabla = dropdown_tablas.value
        if not tabla:
            return
        formulario.controls.clear()
        form_fields.clear()
        try:
            # Se asume que la primera columna es la clave primaria
            clave_primaria = estructura_tablas[tabla][0]["nombre"]
        except Exception as e:
            mostrar_mensaje(f"Error obteniendo clave primaria: {str(e)}", error=True)
            return
        # Primer campo para buscar el registro a modificar
        campo_busqueda = ft.TextField(
            label=f"Ingrese {clave_primaria} para modificar", 
            width=300, 
            tooltip="Clave primaria",
            bgcolor="#ffffff",
            text_style=ft.TextStyle(color="#000000")
        )
        formulario.controls.append(campo_busqueda)
        btn_guardar.text = "Cargar Registro"
        btn_guardar.visible = True
        content_area.content = formulario
        page.update()

        # Al presionar "Cargar Registro", se llamará a la función cargar_registro_modificar()
        btn_guardar.on_click = lambda e: cargar_registro_modificar(clave_primaria, campo_busqueda.value)

    # Función para cargar registro y crear formulario con los datos actuales
    def cargar_registro_modificar(clave_primaria: str, valor_clave: str):
        tabla = dropdown_tablas.value
        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            query = f"SELECT * FROM {tabla} WHERE {clave_primaria} = ?"
            cursor.execute(query, (valor_clave,))
            registro = cursor.fetchone()
            if not registro:
                mostrar_mensaje("Registro no encontrado", error=True)
                return

            # Limpiar formulario y crear campos con valores actuales
            formulario.controls.clear()
            form_fields.clear()
            columnas = [col["nombre"] for col in estructura_tablas[tabla]]
            for idx, columna in enumerate(columnas):
                campo = ft.TextField(
                    label=columna,
                    width=300,
                    value=str(registro[idx]),
                    bgcolor="#ffffff",
                    text_style=ft.TextStyle(color="#000000")
                )
                form_fields.append((columna, campo))
                formulario.controls.append(campo)
            btn_guardar.text = "Modificar Registro"
            btn_guardar.on_click = lambda e: modificar_registro()
            page.update()
        except Exception as e:
            mostrar_mensaje(f"Error: {str(e)}", error=True)

    # Función para modificar registro
    def modificar_registro():
        tabla = dropdown_tablas.value
        if not tabla:
            mostrar_mensaje("Seleccione una tabla", error=True)
            return
        datos = {col: campo.value for col, campo in form_fields}
        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            # Se asume que la primera columna es la clave primaria para identificar el registro
            clave_primaria = list(datos.keys())[0]
            valor_clave = list(datos.values())[0]
            # Se actualizan los campos (excluyendo la clave primaria)
            set_part = ", ".join([f"{col} = ?" for col in list(datos.keys())[1:]])
            valores = list(datos.values())[1:]
            valores.append(valor_clave)
            query = f"UPDATE {tabla} SET {set_part} WHERE {clave_primaria} = ?"
            cursor.execute(query, tuple(valores))
            conn.commit()
            conn.close()
            mostrar_mensaje("Registro modificado con éxito")
            page.update()
        except Exception as e:
            mostrar_mensaje(f"Error: {str(e)}", error=True)

    # Botón principal para ejecutar la acción del formulario (se reutiliza para agregar, eliminar o modificar)
    btn_guardar = ft.ElevatedButton(
        "Guardar Registro",
        on_click=lambda e: guardar_registro(),  # acción por defecto para agregar
        bgcolor="#ED6A5A",
        color="#ffffff",
        visible=False
    )

    # Contenedor del formulario (se usa en agregar, eliminar y modificar)
    formulario = ft.Column([], spacing=10)

    # Área dinámica de contenido inicial (se muestra la tabla por defecto)
    content_area.content = ft.ListView([tbl_datos], expand=True, auto_scroll=True)

    # Sidebar con el menú y botones ABM (se mantiene el dropdown original y se agregan nuevos botones)
    dropdown_tablas = ft.Dropdown(
        label="TABLAS DISPONIBLES",
        options=[],
        on_change=lambda e: cargar_datos_tabla(e.control.value),
        width=200,
        border_color="#9BC1BC",  # Opal
        text_style=ft.TextStyle(color="#000000"),
        label_style=ft.TextStyle(color="#000000"),
        focused_border_color="#9BC1BC"
    )
    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("MENÚ", color="#000000", size=16, weight="bold"),
                            ft.Divider(height=10, color="#9BC1BC"),
                            dropdown_tablas,
                            ft.Divider(height=20, color="#9BC1BC"),
                            ft.ElevatedButton(
                                "Refrescar",
                                icon=ft.icons.REFRESH,
                                on_click=lambda e: cargar_estructura_bd(),
                                style=ft.ButtonStyle(
                                    bgcolor="#9BC1BC",
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                            ft.ElevatedButton(
                                "Exportar CSV",
                                icon=ft.icons.FILE_DOWNLOAD,
                                on_click=lambda e: exportar_a_csv(),
                                style=ft.ButtonStyle(
                                    bgcolor="#9BC1BC",
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                            ft.Divider(height=20, color="#9BC1BC"),
                            ft.Text("Operaciones ABM", color="#000000", size=14, weight="bold"),
                            ft.ElevatedButton(
                                "Ver Registros",
                                on_click=lambda e: cargar_datos_tabla(dropdown_tablas.value),
                                style=ft.ButtonStyle(
                                    bgcolor="#9BC1BC",
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                            ft.ElevatedButton(
                                "Agregar Registro",
                                on_click=lambda e: actualizar_formulario_agregar(),
                                style=ft.ButtonStyle(
                                    bgcolor="#9BC1BC",
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                            ft.ElevatedButton(
                                "Eliminar Registro",
                                on_click=lambda e: actualizar_formulario_eliminar(),
                                style=ft.ButtonStyle(
                                    bgcolor="#9BC1BC",
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                            ft.ElevatedButton(
                                "Modificar Registro",
                                on_click=lambda e: actualizar_formulario_modificar(),
                                style=ft.ButtonStyle(
                                    bgcolor="#9BC1BC",
                                    color="#000000",
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                        ],
                        spacing=15
                    ),
                    padding=15
                )
            ],
            alignment=ft.MainAxisAlignment.START
        ),
        width=250,
        bgcolor="#F4F1BB",  # Robin Egg Blue
        padding=10,
        border_radius=ft.border_radius.only(bottom_left=10)
    )

    # Barra de estado
    status_bar = ft.Text("Sistema listo", color="#000000", size=14)

    # Layout principal: Navbar, Sidebar, Área de contenido y Status Bar
    main_layout = ft.Column(
        [
            navbar,
            ft.Row(
                [sidebar, content_area],
                expand=True
            ),
            ft.Container(
                content=status_bar,
                bgcolor="#9BC1BC",
                padding=10,
                border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
            ),
            # Botón de acción dinámico (se ubica al final de la pantalla)
            ft.Container(
                content=btn_guardar,
                alignment=ft.alignment.center,
                padding=10
            )
        ],
        spacing=0
    )

    # Función para exportar datos a CSV
    def exportar_a_csv():
        if not dropdown_tablas.value:
            mostrar_mensaje("Seleccione una tabla primero", error=True)
            return
        tabla = dropdown_tablas.value
        try:
            conn = ConexionSQL.conectar()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {tabla}")
            nombre_archivo = f"{tabla}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([col[0] for col in cursor.description])
                writer.writerows(cursor.fetchall())
            mostrar_mensaje(f"Exportado: {nombre_archivo}")
        except Exception as e:
            mostrar_mensaje(f"Error al exportar: {str(e)}", error=True)
        finally:
            if conn:
                conn.close()

    # Cargar nombres de las tablas disponibles al iniciar
    try:
        conn = ConexionSQL.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        dropdown_tablas.options = [ft.dropdown.Option(row[0]) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        mostrar_mensaje(f"Error al cargar tablas: {str(e)}", error=True)

    page.add(main_layout)
    cargar_estructura_bd()

if __name__ == "__main__":
    ft.app(target=main)