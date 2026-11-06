# Práctica 2: cliente Python y frontend para la API de la tienda online

Tres piezas independientes que usan los mismos endpoints HTTP y trabajan sobre los mismos datos:

```
Tienda_API/           API FastAPI              
cliente_python/       cliente con requests         -> cliente.py
frontend_streamlit/   frontend web con Streamlit   -> app.py
```

Ni el cliente ni el frontend importan nada de la API (ni `TiendaService`, ni modelos, ni esquemas): solo hablan HTTP.

## 0. Instalación

Desde la carpeta raíz del proyecto, crear el venv e instalar las dependencias (API, cliente y frontend):

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

El segundo equipo, que solo ejecuta el cliente, necesita únicamente `pip install -r cliente_python/requirements.txt`.

## 1. Arrancar la API

Los comandos cd parten de la carpeta raíz del proyecto; usa una terminal por cada pieza.

Desde la carpeta `Tienda_API/`:

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
