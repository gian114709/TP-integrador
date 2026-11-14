import sqlite3
from contextlib import closing

from base_datos import ARCHIVO


def mostrar_tabla(base, nombre, columnas):
    cantidad = base.execute(f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
    print(f"\n{nombre}: {cantidad} registros")
    for fila in base.execute(f"SELECT {columnas} FROM {nombre} LIMIT 10"):
        print("  " + " | ".join(str(valor) for valor in fila))
    if cantidad > 10:
        print("  ... se muestran sólo los primeros 10")


def main():
    if not ARCHIVO.is_file():
        print("Todavía no existe la base. Ejecutá primero crear_usuario.py o servidor.py.")
        return

    print(f"Base de datos: {ARCHIVO}")
    with closing(sqlite3.connect(ARCHIVO.as_uri() + "?mode=ro", uri=True)) as base:
        mostrar_tabla(base, "usuarios", "nombre, length(sal), length(clave_hash)")
        print("  Columnas: usuario | largo de la sal | largo del hash (no la clave)")
        mostrar_tabla(base, "repositorios", "usuario_github, nombre, url")
        mostrar_tabla(base, "followers", "usuario_github, nombre, url")


if __name__ == "__main__":
    main()
