# TP integrador - Programación sobre Redes

Alumno: Gian Oliva  
Materia: Programación sobre Redes

El programa permite conectar varios clientes a un servidor TCP. El servidor verifica el usuario y la contraseña en una base SQLite. Después del acceso, el cliente puede enviar mensajes y usar comandos para consultar la hora, ver usuarios conectados y guardar datos públicos de GitHub.

## Archivos

- `servidor.py`: acepta varios clientes con un hilo por conexión, verifica el acceso y responde comandos.
- `cliente.py`: se conecta, envía las credenciales y permite escribir y recibir mensajes al mismo tiempo.
- `base_datos.py`: crea y consulta la base SQLite `redes.db`.
- `crear_usuario.py`: registra un usuario local para poder probar el acceso.
- `github_api.py`: consulta los repositorios y seguidores públicos mediante la API de GitHub.
- `ver_base.py`: muestra en la terminal los registros guardados, sin modificarlos ni mostrar contraseñas.
- `requirements.txt`: versiones de `requests` y sus dependencias para instalar el proyecto en otra computadora.

Se necesita Python 3.9 o posterior. La base SQLite se crea automáticamente en la misma carpeta. `redes.db` no se incluye en el repositorio porque contiene cuentas de prueba.

## Instalación y uso

Abrí esta carpeta completa en VS Code. La primera vez, en una terminal de PowerShell, prepará el entorno e instalá las dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell no permite activar el entorno, podés usar directamente `.\.venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes. El entorno `.venv` no se sube a GitHub.

Ejecutá `python crear_usuario.py` una vez por cada usuario que quieras probar. Después iniciá el servidor:

```powershell
python crear_usuario.py
python servidor.py
```

Dejá la terminal del servidor abierta. En otra terminal ejecutá:

```powershell
python cliente.py
```

Abrí una tercera terminal, activá también `.venv` y ejecutá otro `python cliente.py` con el segundo usuario. Podés probar:

```text
hola
/usuarios
/hora
/todos hola a todos
/repos octocat
/followers javierblancoedu
/adios
```

El texto normal del cliente se muestra en la terminal del servidor. Allí, `@usuario mensaje` responde a un cliente concreto; un texto sin `@` se envía a todos. Para apagar el servidor, escribí `/salir` en su terminal. Una contraseña incorrecta recibe un error y cierra esa sesión.

Los comandos `/repos` y `/followers` necesitan Internet. El nombre indicado es una **cuenta pública de GitHub**, que puede ser de otra persona y no tiene que coincidir con el usuario del chat. Por ejemplo, podés iniciar sesión como `gian2` y escribir `/repos octocat` o `/followers javierblancoedu` (cuenta indicada en la consigna). `requests.get()` hace la petición y `respuesta.json()` lee los datos. El servidor confirma cuántos registros guardó en las tablas `repositorios` y `followers`. Se guardan nombre y URL, más la descripción de cada repositorio; la consigna no especifica otros campos. Para la prueba conviene elegir cuentas con pocos resultados y evitar cientos de páginas.

Para comprobar que los datos quedaron en la base, abrí otra terminal en esta carpeta y ejecutá:

```powershell
python ver_base.py
```

Muestra los usuarios registrados (no sus contraseñas) y hasta 10 filas de cada tabla. Los usuarios **registrados** pueden ser más que los **conectados** que devuelve `/usuarios`. La base es el archivo `redes.db` que imprime el servidor al iniciar.

También podés abrir `redes.db` con un visor de SQLite y mirar las tablas `usuarios`, `repositorios` y `followers`. En `usuarios` se guardan una sal y un hash, no la contraseña escrita.

GitHub limita la cantidad de consultas públicas. Si aparece un error de límite, probá más tarde. No guardes claves de API dentro del proyecto.

## Prueba guiada en una computadora

1. Creá dos usuarios distintos con `python crear_usuario.py` (por ejemplo, `gian2` y `gian3`). Ejecutá el comando una vez por usuario.
2. Iniciá `python servidor.py` en una terminal y dejala abierta. Debe aparecer `Servidor escuchando en 127.0.0.1:12345`.
3. Abrí otras dos terminales, ejecutá `python cliente.py` en cada una e ingresá con un usuario diferente. Cada cliente debe recibir `OK Bienvenido`.
4. En un cliente escribí `/usuarios`. La respuesta debe incluir los dos nombres conectados. Probá también `/hora`: debe devolver la hora del servidor.
5. Escribí `/todos hola` en un cliente. Los dos clientes deben recibir el mensaje. Si escribís un texto normal, debe aparecer en la terminal del servidor. Desde esa terminal, escribí `@gian2 hola` para responder solo a `gian2`.
6. En un cliente escribí `/repos octocat` y `/followers javierblancoedu`. El servidor debe confirmar cuántos registros guardó. En otra terminal ejecutá `python ver_base.py` y comprobá que las tablas `repositorios` y `followers` tengan filas. Estas consultas requieren Internet.
7. Escribí `/adios` en uno de los clientes. Debe recibir la despedida y desconectarse. Desde el otro cliente, `/usuarios` ya no debe mostrarlo.
8. Ejecutá de nuevo `python cliente.py` e ingresá una contraseña incorrecta. Debe mostrar `ERROR Usuario o contraseña incorrectos.` y cerrar esa sesión. Para terminar, escribí `/salir` en la terminal del servidor.

## Prueba entre dos computadoras de la misma red

En la computadora del servidor, indicá que escuche en la red local:

```powershell
$env:REDES_ESCUCHA_IP = "0.0.0.0"
python servidor.py
```

En la otra computadora, cambiá la IP de ejemplo por la IP local real del servidor:

```powershell
$env:REDES_SERVIDOR_IP = "192.168.1.10"
python cliente.py
```

Las dos computadoras deben estar en la misma red y el puerto `12345` debe estar permitido por el firewall. `0.0.0.0` se usa **solo en el servidor** para escuchar; el cliente necesita una IP concreta. No expongas este proyecto a Internet: TCP aquí no cifra usuario, contraseña ni mensajes.

Por defecto el proyecto escucha únicamente en `127.0.0.1`, es decir, en la misma computadora. TCP por sí solo no cifra el tráfico: antes de exponerlo fuera de una LAN de prueba habría que añadir TLS y revisar la seguridad general.
