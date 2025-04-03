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
    page.bgcolor = "#1C1748"  # Fondo violeta oscuro
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 0

    # Variables de estado
    current_connection = None
    tablas_disponibles: List[str] = []
    estructura_tablas: Dict[str, List[Dict]] = {}

    # Componentes UI con paleta de colores original
    tbl_datos = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Seleccione una tabla", color=ft.colors.WHITE))],
        rows=[],
        width=1100,
        heading_row_color="#7B1FA2",  # Violeta medio
        heading_text_style=ft.TextStyle(color=ft.colors.WHITE),
        data_row_color={"hovered": "#34286F"},  # Violeta oscuro
        border=ft.border.all(1, "#7B1FA2"),
        border_radius=8,
        horizontal_lines=ft.border.BorderSide(1, "#7B1FA2"),
        column_spacing=20
    )

    # Navbar superior
    navbar = ft.Container(
        content=ft.Row(
            [
                ft.Text("SIGES", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ft.Container(width=20),
                ft.TextField(
                    hint_text="BUSCAR...",
                    border_color="#7B1FA2",
                    bgcolor="#34286F",
                    text_style=ft.TextStyle(color=ft.colors.WHITE),
                    width=300
                ),
                ft.ElevatedButton(
                    "INICIO",
                    bgcolor=ft.colors.WHITE,
                    color="#1C1748",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        ),
        bgcolor="#34286F",
        padding=15,
        border_radius=ft.border_radius.only(top_left=10, top_right=10)
    )

    # Funciones mejoradas con manejo de tooltips
    def cargar_estructura_bd():
        try:
            nonlocal tablas_disponibles, estructura_tablas
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

    def cargar_datos_tabla(tabla: str):
        try:
            nonlocal current_connection
            if current_connection:
                current_connection.close()
            
            current_connection = ConexionSQL.conectar()
            cursor = current_connection.cursor()
            cursor.execute(f"SELECT TOP 50 * FROM {tabla}")
            
            # Configurar columnas con manejo seguro de tooltips
            columnas = []
            for col in cursor.description:
                nombre_columna = col[0] if col[0] else "Columna"
                tooltip_text = f"{nombre_columna} ({col[1]})" if col[1] else nombre_columna
                columnas.append(
                    ft.DataColumn(
                        ft.Text(nombre_columna, color=ft.colors.WHITE, weight="bold"),
                        tooltip=tooltip_text if tooltip_text else None  # Evita tooltips vacíos
                    )
                )
            
            # Configurar filas con manejo seguro de tooltips
            filas = []
            for row in cursor.fetchall():
                celdas = []
                for valor in row:
                    texto = str(valor)[:50] + "..." if valor and len(str(valor)) > 50 else str(valor) if valor is not None else "NULL"
                    tooltip_valor = str(valor) if valor is not None else "NULL"
                    celdas.append(
                        ft.DataCell(
                            ft.Text(texto, color=ft.colors.WHITE, size=12),
                            celdas=tooltip_valor if tooltip_valor else None  # Evita tooltips vacíos
                        )
                    )
                filas.append(ft.DataRow(cells=celdas))
            
            tbl_datos.columns = columnas
            tbl_datos.rows = filas
            mostrar_mensaje(f"{tabla}: {len(filas)} registros cargados")
            
        except Exception as e:
            mostrar_mensaje(f"Error al cargar {tabla}: {str(e)}", error=True)
            tbl_datos.columns = [ft.DataColumn(ft.Text("Error", color=ft.colors.RED))]
            tbl_datos.rows = [ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(e), color=ft.colors.RED))
            ])]
        finally:
            page.update()

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

    def mostrar_mensaje(mensaje: str, error: bool = False):
        status_bar.value = mensaje
        status_bar.color = ft.colors.RED if error else "#7B1FA2"
        page.update()

    def actualizar_lista_tablas():
        dropdown_tablas.options = [
            ft.dropdown.Option(tabla) for tabla in tablas_disponibles
        ]
        page.update()

    # Sidebar con diseño original
    dropdown_tablas = ft.Dropdown(
        label="TABLAS DISPONIBLES",
        options=[],
        on_change=lambda e: cargar_datos_tabla(e.control.value),
        width=200,
        border_color="#7B1FA2",
        text_style=ft.TextStyle(color=ft.colors.WHITE),
        label_style=ft.TextStyle(color="#D8BFD8"),
        focused_border_color="#7B1FA2"
    )

    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("MENÚ", color="#D8BFD8", size=16, weight="bold"),
                            ft.Divider(height=10, color="#7B1FA2"),
                            dropdown_tablas,
                            ft.Divider(height=20, color="#7B1FA2"),
                            ft.ElevatedButton(
                                "Refrescar",
                                icon=ft.icons.REFRESH,
                                on_click=lambda e: cargar_estructura_bd(),
                                style=ft.ButtonStyle(
                                    bgcolor="#7B1FA2",
                                    color=ft.colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            ),
                            ft.ElevatedButton(
                                "Exportar CSV",
                                icon=ft.icons.FILE_DOWNLOAD,
                                on_click=lambda e: exportar_a_csv(),
                                style=ft.ButtonStyle(
                                    bgcolor="#7B1FA2",
                                    color=ft.colors.WHITE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            )
                        ],
                        spacing=15
                    ),
                    padding=15
                )
            ],
            alignment=ft.MainAxisAlignment.START
        ),
        width=250,
        bgcolor="#34286F",
        padding=10,
        border_radius=ft.border_radius.only(bottom_left=10)
    )

    # Área de contenido principal
    content = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(
                        "VISUALIZACIÓN DE DATOS", 
                        size=20, 
                        color="#D8BFD8",
                        weight="bold"
                    ),
                    padding=15,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.ListView(
                        [tbl_datos],
                        expand=True,
                        auto_scroll=True
                    ),
                    padding=10,
                    border_radius=10
                )
            ],
            spacing=10,
            expand=True
        ),
        bgcolor="#4B0082",
        padding=15,
        expand=True,
        border_radius=ft.border_radius.only(bottom_right=10)
    )

    # Barra de estado
    status_bar = ft.Text(
        "Sistema listo",
        color="#D8BFD8",
        size=14
    )

    # Layout principal
    main_layout = ft.Column(
        [
            navbar,
            ft.Row(
                [sidebar, content],
                expand=True
            ),
            ft.Container(
                content=status_bar,
                bgcolor="#34286F",
                padding=10,
                border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10)
            )
        ],
        spacing=0
    )

    page.add(main_layout)
    
    # Cargar estructura al iniciar
    cargar_estructura_bd()

if __name__ == "__main__":
    ft.app(target=main)