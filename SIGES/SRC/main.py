import flet as ft
from conexion_sql import ConexionSQL
from datetime import datetime
import pyodbc
import warnings

# Ignorar advertencias de deprecación
warnings.filterwarnings("ignore", category=DeprecationWarning)

def main(page: ft.Page):
    page.title = "SIGES - Administrador SQL"
    page.window_width = 1300
    page.window_height = 850
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    current_connection = None

    txt_query = ft.TextField(
        label="Consulta SQL",
        multiline=True,
        min_lines=5,
        value="",  # CONSULTA AUTOMÁTICA
        width=1200,
        text_size=14,
        border_color=ft.colors.BLUE_800
    )

    tbl_resultados = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Presione 'Ejecutar' para cargar datos"))],
        rows=[],
        width=1200,
        heading_row_color=ft.colors.BLUE_GREY_100,
        heading_row_height=40,
        data_row_min_height=40,
        column_spacing=20,
        horizontal_margin=10,
        divider_thickness=0.5
    )

    status_bar = ft.Text("Estado: Listo para conectar", color=ft.colors.BLUE_800)

    def format_value(value):
        """Formatea valores para mejor visualización"""
        if value is None:
            return ft.Text("NULL", italic=True, color=ft.colors.GREY)
        if isinstance(value, datetime):
            return ft.Text(value.strftime("%Y-%m-%d"), size=12)
        return ft.Text(str(value), size=12, overflow=ft.TextOverflow.ELLIPSIS)

    def ejecutar_consulta(e):
        nonlocal current_connection
        try:
            if current_connection:
                current_connection.close()

            current_connection = ConexionSQL.conectar()
            if not current_connection:
                raise Exception("No se pudo establecer la conexión")
                
            cursor = current_connection.cursor()
            cursor.execute(txt_query.value)

            if cursor.description is None:
                status_bar.value = "Operación completada (sin resultados)"
                status_bar.color = ft.colors.GREEN
                tbl_resultados.columns = [ft.DataColumn(ft.Text("Información"))]
                tbl_resultados.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text("Consulta ejecutada exitosamente", color=ft.colors.GREEN))])]
            else:
                # Obtener nombres de las columnas dinámicamente
                columnas = [ft.DataColumn(ft.Text(col[0], size=12, weight="bold")) for col in cursor.description]

                # Obtener filas y celdas con formato
                filas = []
                for row in cursor.fetchall():
                    celdas = [ft.DataCell(format_value(valor)) for valor in row]
                    filas.append(ft.DataRow(cells=celdas))

                # Actualizar la tabla con nuevos datos
                tbl_resultados.columns = columnas
                tbl_resultados.rows = filas

                status_bar.value = f"Consulta exitosa - {len(filas)} registros"
                status_bar.color = ft.colors.GREEN

        except pyodbc.Error as e:
            status_bar.value = f"Error SQL: {str(e)}"
            status_bar.color = ft.colors.RED
            tbl_resultados.columns = [ft.DataColumn(ft.Text("Error SQL"))]
            tbl_resultados.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(e), color=ft.colors.RED))])]

        except Exception as e:
            status_bar.value = f"Error: {str(e)}"
            status_bar.color = ft.colors.ORANGE
            tbl_resultados.columns = [ft.DataColumn(ft.Text("Error"))]
            tbl_resultados.rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(e), color=ft.colors.ORANGE))])]

        finally:
            page.update()

    page.add(
        ft.Column(
            controls=[
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Sistema de Gestión SIGES", size=24, weight="bold", color=ft.colors.BLUE_800),
                            ft.Divider(height=10),
                            txt_query,
                            ft.Row([
                                ft.ElevatedButton(
                                    "Ejecutar Consulta",
                                    on_click=ejecutar_consulta,
                                    icon=ft.icons.PLAY_ARROW,
                                    width=200,
                                    height=45,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                        padding=10,
                                        bgcolor=ft.colors.BLUE_600,
                                        color=ft.colors.WHITE
                                    )
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ]),
                        padding=20,
                    ),
                    elevation=5
                ),
                
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Resultados:", size=16, weight="bold", color=ft.colors.BLUE_800),
                            ft.Divider(height=10),
                            ft.Container(
                                content=ft.ListView([tbl_resultados], height=500, auto_scroll=True),
                                padding=10,
                                border=ft.border.all(1, ft.colors.GREY_300),
                                border_radius=8
                            )
                        ]),
                        padding=15
                    ),
                    elevation=3
                ),
                
                ft.Container(
                    content=status_bar,
                    padding=15,
                    bgcolor=ft.colors.BLUE_GREY_50,
                    border_radius=8,
                    margin=ft.margin.only(top=10)
                )
            ],
            spacing=15,
            expand=True
        )
    )

    def on_window_event(e):
        if e.data == "close" and current_connection:
            current_connection.close()

    page.on_window_event = on_window_event
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
