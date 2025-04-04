import pyodbc

class ConexionSQL:
    @staticmethod
    def conectar():
        """Establece la conexión con SQL Server y devuelve el objeto conexión."""
        try:
            connection = pyodbc.connect(
                "Driver={SQL Server};"
                "Server=PC-1BDIRINVES05;"
                "Database=SIGETRATA;"
                "Trusted_Connection=yes;"
            )
            print("Conexión exitosa a la base de datos.")
            return connection
        except pyodbc.Error as e:
            print("Error al conectar a la base de datos:", e)
            return None  # Devuelve None si hay un error

    @staticmethod
    def cerrar_conexion(connection):
        """Cierra la conexión con la base de datos."""
        if connection:
            connection.close()
            print("Conexión cerrada correctamente.")

# Prueba de conexión
if __name__ == "__main__":
    conn = ConexionSQL.conectar()
    if conn:
        ConexionSQL.cerrar_conexion(conn)
