# Práctica 3

Tres piezas independientes que usan los mismos endpoints HTTP y trabajan sobre los mismos datos:

```
src/                  API FastAPI              
cliente_python/       cliente con requests         -> cliente.py
frontend_streamlit/   frontend web con Streamlit   -> app.py
```

Ni el cliente ni el frontend importan nada de la API (ni TiendaService, ni modelos, ni esquemas): solo hablan HTTP.

## 0. Instalación

Desde la carpeta raíz del proyecto, crear el venv e instalar las dependencias (API, cliente y frontend):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
```

`requirements.txt` contiene solo lo necesario para ejecutar la API (es el que usa Docker); 
`requirements-dev.txt` lo incluye y añade pytest, requests y streamlit para trabajar en local.

El segundo equipo, que solo ejecuta el cliente, necesita únicamente `pip install -r cliente_python/requirements.txt`.

## 1. Arrancar la API

Los comandos cd parten de la carpeta raíz del proyecto; se usa una terminal por cada pieza antes de usar el Docker, una vez aplicado ya no será necesario.

Desde la carpeta `src/`:

```
uvicorn main:app --reload
```

Documentación interactiva: http://localhost:8000/docs

## 2. Cliente Python (`cliente_python/`)

```
cd .\cliente_python
python cliente.py                             # usa BASE_URL (para local)
python cliente.py http://192.168.1.34:8000    # usa otra dirección
```

Recorre el flujo completo: crear usuario, listar usuarios, crear productos, listar productos, crear un pedido,
consultar los pedidos del usuario y, al final, provoca tres errores a propósito (404, 409 y 422) para comprobar que la API
responde con el código correcto. Cada petición imprime su código HTTP, y si alguno no es el esperado el script se detiene
con un mensaje y código de salida 1.

## 3. Frontend (`frontend_streamlit/`)

```
cd .\frontend_streamlit
streamlit run app.py
```

La URL de la API se cambia en la barra lateral de la propia página (o con la variable de entorno `TIENDA_API_URL`).
En el código, todas las peticiones están en la sección `ACCESO A LA API` (funciones `api_*`), y la cabecera de `app.py`
indica qué endpoint usa cada pestaña.

Streamlit ejecuta el código en su propio servidor, así que las peticiones salen de ese proceso y no del navegador.
La URL de la API debe ser alcanzable desde el equipo donde corre `streamlit run`.

## 4. Prueba entre dos equipos de la misma red

Equipo servidor

1. Averiguar IP local: `ipconfig` (Windows)
2. Arrancar la API aceptando conexiones de la red:
   ```
   cd .\Tienda_API
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   Por defecto uvicorn escucha en `127.0.0.1` (local), que sólo es accesible desde el propio equipo.
3. Firewall de Windows: la primera vez saldrá un aviso, hay que permitir el acceso en redes privadas.

Equipo cliente

1. Abrir en el navegador `http://192.168.1.34:8000/docs` (con la IP del servidor).
2. Ejecutar el cliente apuntando a esa IP:
   ```
   cd .\cliente_python
   python cliente.py http://192.168.1.34:8000
   ```
3. Opcional: arrancar el frontend y escribir esa misma URL en la barra lateral.


Si no conecta: comprobar la IP, que uvicorn use `--host 0.0.0.0`, el firewall y que la red de Windows esté marcada como privada. 
Probar `ping 192.168.1.34` desde el cliente ya que algunas redes aíslan los dispositivos entre sí; en ese caso, usar el punto de acceso del móvil.

## 5. Comprobación final

Con la API en marcha, los datos creados desde cualquiera de los tres clientes aparecen en los otros dos:

- crear un cliente con `python cliente.py` y comprobarlo en la pestaña "Usuarios" del frontend y en `GET /usuarios` de `/docs`;
- hacer un pedido desde el frontend y consultarlo en `GET /usuarios/{id}/pedidos` de `/docs`.

Los datos viven en memoria: al reiniciar la API (también con `--reload` al guardar un archivo) vuelven al estado inicial.

## 6. Docker

Cada pieza tiene su propia imagen, con su `Dockerfile`, y `compose.yaml` las arranca juntas:

```
Dockerfile                      imagen de la API            (tienda-api)
frontend_streamlit/Dockerfile   imagen del frontend         (tienda-frontend)
cliente_python/Dockerfile       imagen del cliente          (tienda-cliente)
compose.yaml                    define los tres servicios: api, frontend y cliente
```

Dentro de la red de Compose cada servicio se alcanza por su nombre, así que el frontend y el cliente hablan con la API en
`http://api:8000`. No se usa `localhost`, porque dentro de un contenedor `localhost` es el propio contenedor.

### Con Docker Compose

```
docker compose up --build        # construye las imágenes y arranca la API y el frontend
docker compose up -d --build     # lo mismo, en segundo plano
docker compose run --rm cliente  # ejecuta el cliente una vez contra la API (la arranca si hace falta)
docker compose logs -f api       # ver los logs de un servicio
docker compose down              # parar y eliminar los contenedores
```

El cliente no es un servidor: hace su recorrido y termina, por eso no arranca con `up` y se lanza con `run`.
El frontend y el cliente esperan a que la API esté lista (`healthcheck`) antes de arrancar.

| Servicio | Dirección en el equipo |
|---|---|
| API | http://localhost:8000/docs |
| Frontend | http://localhost:8501 |

Para cambiar los puertos del equipo sin editar el archivo:
`PUERTO=8080 PUERTO_FRONTEND=8502 docker compose up` (en PowerShell: `$env:PUERTO=8080; $env:PUERTO_FRONTEND=8502; docker compose up`).

### Construir y ejecutar cada imagen por separado

```
docker build -t tienda-api:1.0 .
docker run --rm -p 8000:8000 --name tienda tienda-api:1.0

docker build -t tienda-frontend:1.0 ./frontend_streamlit
docker run --rm -p 8501:8501 -e TIENDA_API_URL=http://host.docker.internal:8000 tienda-frontend:1.0

docker build -t tienda-cliente:1.0 ./cliente_python
docker run --rm tienda-cliente:1.0 python cliente.py http://host.docker.internal:8000
```

`host.docker.internal` es la forma de llegar desde un contenedor a un puerto publicado en el equipo (Docker Desktop).
Para tener la API en segundo plano: `docker run -d -p 8000:8000 --name tienda tienda-api:1.0`, `docker logs tienda`,
`docker stop tienda && docker rm tienda`.

### Variables de entorno

| Variable | Dónde | Para qué | Valor por defecto |
|---|---|---|---|
| `TIENDA_API_URL` | frontend | dirección de la API | `http://localhost:8000` (en Compose: `http://api:8000`) |
| `PUERTO` | compose.yaml | puerto del equipo para la API | `8000` |
| `PUERTO_FRONTEND` | compose.yaml | puerto del equipo para el frontend | `8501` |

La API no lee variables de entorno. El cliente recibe la dirección de la API como argumento (`python cliente.py URL`).

### Comprobar que funciona

1. `docker compose up --build` y abrir `http://localhost:8000/docs`: se ve la documentación de la API.
2. Abrir `http://localhost:8501`: se ve el frontend con las pestañas Productos, Crear producto, Usuarios, Nuevo pedido y
   Pedidos de un usuario, y con los productos iniciales cargados.
3. `docker compose run --rm cliente` recorre el flujo completo y termina con `Flujo completado correctamente.`
4. Los tres usan los mismos datos: el usuario que crea el cliente aparece en la pestaña Usuarios del frontend y en
   `GET /usuarios` de `/docs`.
5. `docker run --rm tienda-api:1.0 whoami` imprime `appuser`: la aplicación no se ejecuta como root.

### Descargar la imagen 

"""
docker pull superbojum/tienda-api:1.0
docker run --rm -p 8000:8000 superbojum/tienda-api:1.0
"""