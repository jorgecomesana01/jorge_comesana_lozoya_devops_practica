# Frontend (Streamlit) de la tienda online
# Autor: Jorge Comesaña Lozoya

# Este frontend no importa nada de la aplicacion FastAPI: habla con ella solo por HTTP (libreria requests).
# Todas las peticiones estan en la seccion "ACCESO A LA API" (las funciones api_*). 
# El resto del archivo dibuja la interfaz y llama a esas funciones.

# Endpoint que usa cada parte de la interfaz:
#   pestana "Productos"              GET  /productos
#   pestana "Crear producto"         POST /productos
#   pestana "Usuarios"               GET  /usuarios        y   POST /usuarios
#   pestana "Nuevo pedido"           GET  /usuarios, GET /productos   y   POST /pedidos
#   pestana "Pedidos de un usuario"  GET  /usuarios/{id}/pedidos
#
# Streamlit ejecuta este codigo en el servidor de Streamlit, asi que las peticiones HTTP salen de ese proceso y no del navegador. 
# La URL de la API debe ser alcanzable desde el equipo donde se ejecuta Streamlit.

# Arrancar (desde esta carpeta):   streamlit run app.py
# URL de la API: se cambia en la barra lateral, o con la variable de entorno TIENDA_API_URL.

import os

import requests
import streamlit as st 

TIMEOUT=5     # segundos que se espera una respuesta antes de dar la API por inaccesible
URL_POR_DEFECTO=os.environ.get("TIENDA_API_URL","http://localhost:8000")
TIPOS_PRODUCTO=["generico","electronico","ropa","libro"]


# Acceso a la API: aqui se hacen las peticiones HTTP
class ErrorAPI(Exception):
    """
    No se ha podido contactar con la API, o ha respondido con un codigo HTTP que no se esperaba
    """


def _url_base()->str:
    return st.session_state["api_url"].strip().rstrip("/")


def _mensaje_de_error(r:requests.Response)->str:
    """
    Convierte una respuesta de error de la API ({"detail": ...}) en un texto legible
    """
    try:
        detalle=r.json().get("detail",r.text)
    except (ValueError,AttributeError):
        detalle=r.text[:200] or "sin detalle"
    if isinstance(detalle, list):
        partes=[]
        for e in detalle:
            campo=".".join(str(x) for x in e.get("loc",[]) if x!="body")
            mensaje=str(e.get("msg","")).removeprefix("Value error, ")
            partes.append(f"{campo}: {mensaje}" if campo else mensaje)
        detalle="; ".join(partes)
    return f"Error {r.status_code}: {detalle}" 


def _peticion(metodo:str,ruta:str,esperado:tuple,**kwargs):
    """
    Envia la peticion, comprueba el codigo HTTP y devuelve (codigo, json). Si algo falla lanza ErrorAPI
    """
    base=_url_base()
    try:
        r=requests.request(metodo,base+ruta,timeout=TIMEOUT,**kwargs)
    except requests.exceptions.ConnectionError:
        raise ErrorAPI(f"No se puede conectar con la API en {base}. Comprobar que está arrancada y que la dirección es correcta (si es otro equipo: su IP, el firewall y uvicorn con --host 0.0.0.0).") from None
    except requests.exceptions.Timeout:
        raise ErrorAPI(f"La API en {base} no ha respondido en {TIMEOUT} segundos.") from None
    except requests.exceptions.RequestException as e:
        raise ErrorAPI(f"No se ha podido hacer la petición a '{base}': {e}") from None
    if r.status_code not in esperado:
        raise ErrorAPI(_mensaje_de_error(r))
    try:
        return r.status_code,(r.json() if r.content else None)
    except ValueError:
        raise ErrorAPI("La API ha devuelto una respuesta que no es JSON.") from None


def api_listar_productos()->list:
    """
    GET /productos
    """
    return _peticion("GET","/productos",(200,))[1]


def api_crear_producto(datos:dict):
    """
    POST /productos  ->  (201, producto) si es nuevo, (200, producto) si ya existia y se ha sumado el stock
    """
    return _peticion("POST","/productos",(200, 201),json=datos)


def api_listar_usuarios()->list:
    """
    GET /usuarios
    """
    return _peticion("GET","/usuarios",(200,))[1]


def api_crear_usuario(datos:dict):
    """
    POST /usuarios
    """
    return _peticion("POST","/usuarios",(201,),json=datos)


def api_crear_pedido(cliente_id:str,items:list):
    """
    POST /pedidos   items = [{"producto_id": ..., "cantidad": ...}, ...]
    """
    return _peticion("POST","/pedidos",(201,),json={"cliente_id":cliente_id,"items":items})


def api_listar_pedidos_usuario(cliente_id:str)->list:
    """
    GET /usuarios/{cliente_id}/pedidos
    """
    return _peticion("GET",f"/usuarios/{cliente_id}/pedidos",(200,))[1]


# Acciones
def _aviso(nivel:str,texto:str)->None:
    st.session_state["mensaje"]=(nivel, texto)


def cb_crear_producto():
    tipo=st.session_state["np_tipo"]
    datos={"tipo":tipo,"nombre":st.session_state["np_nombre"].strip(),"precio":float(st.session_state["np_precio"]),"stock":int(st.session_state["np_stock"])}
    if tipo=="electronico":
        datos["meses_garantia"]=int(st.session_state["np_garantia"])
    elif tipo=="ropa":
        datos["talla"]=st.session_state["np_talla"].strip()
        datos["color"]=st.session_state["np_color"].strip()
    elif tipo=="libro":
        datos["autor"]=st.session_state["np_autor"].strip()
        datos["edicion"]=st.session_state["np_edicion"].strip()
    try:
        codigo,producto=api_crear_producto(datos)
    except ErrorAPI as e:
        _aviso("error",str(e))
        return
    if codigo==201:
        _aviso("ok",f"Producto creado: {producto['nombre']} (id {producto['id']}).")
    else:
        _aviso("ok",f"Ese artículo ya existía: se ha sumado el stock. Stock actual de {producto['nombre']}: {producto['stock']}.")


def cb_crear_usuario():
    tipo=st.session_state["nu_tipo"]
    datos={"tipo":tipo,"nombre":st.session_state["nu_nombre"].strip(),"email":st.session_state["nu_email"].strip()}
    if tipo=="cliente":
        datos["direccion_postal"]=st.session_state["nu_direccion"].strip()
    try:
        _,usuario=api_crear_usuario(datos)
    except ErrorAPI as e:
        _aviso("error",str(e))
        return
    _aviso("ok",f"Usuario creado: {usuario['nombre']} (id {usuario['id']}).")


def cb_anadir_al_carrito():
    producto_id=st.session_state["pedido_producto"]
    cantidad=int(st.session_state["pedido_cantidad"])
    carrito=st.session_state["carrito"]
    carrito[producto_id]=carrito.get(producto_id,0)+cantidad


def cb_vaciar_carrito():
    st.session_state["carrito"]={}


def cb_realizar_pedido():
    items=[{"producto_id":pid,"cantidad":cantidad} for pid,cantidad in st.session_state["carrito"].items()]
    try:
        _,pedido=api_crear_pedido(st.session_state["pedido_cliente"],items)
    except ErrorAPI as e:
        _aviso("error",str(e))
        return
    st.session_state["carrito"]={}
    _aviso("ok",f"Pedido realizado para {pedido['cliente']['nombre']}: total {pedido['total']:.2f} EUR (id {pedido['id']}).")


# Interfaz
def detalles_producto(p:dict)->str:
    """
    Atributos propios de cada tipo de producto (la API solo envia los que aplican)
    """
    partes=[]
    if "meses_garantia" in p:
        partes.append(f"garantía {p['meses_garantia']} meses")
    if "talla" in p:
        partes.append(f"talla {p['talla']}, color {p['color']}")
    if "autor" in p:
        partes.append(f"{p['autor']} ({p['edicion']})")
    return " · ".join(partes)


st.set_page_config(page_title="Tienda online",layout="wide")
st.session_state.setdefault("api_url",URL_POR_DEFECTO)
st.session_state.setdefault("carrito",{})

st.sidebar.header("Conexión con la API")
st.sidebar.text_input("URL de la API",key="api_url")
st.sidebar.caption("En este equipo: http://localhost:8000\n\nEn otro equipo de la red: http://IP-DEL-SERVIDOR:8000")

st.title("Tienda online")

if "mensaje" in st.session_state:
    nivel,texto=st.session_state.pop("mensaje")
    (st.success if nivel=="ok" else st.error)(texto)

try:
    productos=api_listar_productos()
    usuarios=api_listar_usuarios()
except ErrorAPI as e:
    st.error(str(e))
    st.stop()
st.sidebar.success(f"Conectado a {_url_base()}")

clientes=[u for u in usuarios if not u["es_admin"]]
productos_por_id={p["id"]: p for p in productos}
etiqueta_cliente={c["id"]: f"{c['nombre']} ({c['email']})" for c in clientes}
etiqueta_producto={p["id"]: f"{p['nombre']} - {p['precio']:.2f} EUR (stock {p['stock']})" for p in productos}


def texto_cliente(cliente_id:str)->str:
    """
    Lo que se ve en los desplegables: nombre y email en vez del id (si no lo conoce, devuelve el propio id)
    """
    return etiqueta_cliente.get(cliente_id,cliente_id)


def texto_producto(producto_id:str)->str:
    return etiqueta_producto.get(producto_id,producto_id)


tab_productos,tab_crear,tab_usuarios,tab_pedido,tab_historial=st.tabs(["Productos","Crear producto","Usuarios","Nuevo pedido","Pedidos de un usuario"])

# Productos: GET /productos
with tab_productos:
    st.subheader("Catálogo")
    if productos:
        st.dataframe([{"id":p["id"],"tipo":p["tipo"],"nombre":p["nombre"],"precio (EUR)":p["precio"],"stock":p["stock"],"detalles":detalles_producto(p)} for p in productos],hide_index=True)
    else:
        st.info("Todavía no hay productos.")

# Crear producto: POST /productos
with tab_crear:
    st.subheader("Crear producto")
    tipo_producto=st.selectbox("Tipo de producto",TIPOS_PRODUCTO,key="np_tipo")
    with st.form("form_producto"):
        st.text_input("Nombre",key="np_nombre")
        col_precio,col_stock=st.columns(2)
        col_precio.number_input("Precio (EUR)",min_value=0.01,value=10.00,step=0.01,format="%.2f",key="np_precio")
        col_stock.number_input("Stock",min_value=0,value=1,step=1,key="np_stock")
        if tipo_producto=="electronico":
            st.number_input("Meses de garantía",min_value=1,value=24,step=1,key="np_garantia")
        elif tipo_producto=="ropa":
            st.text_input("Talla",key="np_talla")
            st.text_input("Color",key="np_color")
        elif tipo_producto=="libro":
            st.text_input("Autor",key="np_autor")
            st.text_input("Edición",key="np_edicion")
        st.form_submit_button("Crear producto",on_click=cb_crear_producto)

# Usuarios: GET /usuarios y POST /usuarios
with tab_usuarios:
    st.subheader("Usuarios registrados")
    if usuarios:
        st.dataframe([{"id":u["id"],"nombre":u["nombre"],"email":u["email"],"rol":"admin" if u["es_admin"] else "cliente"} for u in usuarios],hide_index=True)
    else:
        st.info("Todavía no hay usuarios.")
    st.subheader("Crear usuario")
    tipo_usuario=st.selectbox("Tipo de usuario",["cliente","admin"],key="nu_tipo")
    with st.form("form_usuario"):
        st.text_input("Nombre",key="nu_nombre")
        st.text_input("Email",key="nu_email")
        if tipo_usuario=="cliente":
            st.text_input("Dirección postal",key="nu_direccion")
        st.form_submit_button("Crear usuario",on_click=cb_crear_usuario)

# Nuevo pedido: POST /pedidos (los clientes y productos salen de GET /usuarios y GET /productos)
with tab_pedido:
    st.subheader("Nuevo pedido")
    if not clientes:
        st.info("Primero hace falta un cliente: créalo en la pestaña Usuarios.")
    elif not productos:
        st.info("Primero hace falta algún producto: créalo en la pestaña Crear producto.")
    else:
        st.selectbox("Cliente",[c["id"] for c in clientes],format_func=texto_cliente,key="pedido_cliente")
        col_producto,col_cantidad,col_boton=st.columns([3,1,1],vertical_alignment="bottom")
        col_producto.selectbox("Producto",[p["id"] for p in productos],format_func=texto_producto,key="pedido_producto")
        col_cantidad.number_input("Cantidad",min_value=1,value=1,step=1,key="pedido_cantidad")
        col_boton.button("Añadir al pedido",on_click=cb_anadir_al_carrito)

        carrito=st.session_state["carrito"]
        if carrito:
            st.markdown("**Líneas del pedido**")
            filas,total=[],0.0
            for producto_id,cantidad in carrito.items():
                p=productos_por_id.get(producto_id)
                precio=p["precio"] if p else 0.0
                total+=precio*cantidad
                filas.append({"producto":p["nombre"] if p else "(producto ya no disponible)","cantidad":cantidad,"precio unitario (EUR)":precio,"subtotal (EUR)":round(precio*cantidad,2)})
            st.dataframe(filas,hide_index=True)
            st.markdown(f"**Total estimado:{total:.2f} EUR**")
            col_realizar,col_vaciar,_=st.columns([1,1,4])
            col_realizar.button("Realizar pedido",type="primary",on_click=cb_realizar_pedido)
            col_vaciar.button("Vaciar",on_click=cb_vaciar_carrito)
        else:
            st.caption("Todavía no has añadido ningún producto al pedido.")

# Pedidos de un usuario: GET /usuarios/{id}/pedidos
with tab_historial:
    st.subheader("Pedidos de un usuario")
    if not clientes:
        st.info("Todavía no hay clientes.")
    else:
        cliente_id=st.selectbox("Cliente",[c["id"] for c in clientes],format_func=texto_cliente,key="historial_cliente")
        try:
            pedidos=api_listar_pedidos_usuario(cliente_id)
        except ErrorAPI as e:
            st.error(str(e))
            pedidos=[]
        if not pedidos:
            st.info("Este cliente todavía no ha hecho ningún pedido.")
        for pedido in reversed(pedidos):
            fecha=pedido["fecha_pedido"][:16].replace("T"," ")
            with st.expander(f"{fecha} — {pedido['total']:.2f} EUR — {len(pedido['items'])} línea(s)"):
                st.caption(f"Pedido {pedido['id']}")
                st.dataframe([{"producto":i["nombre"],"cantidad":i["cantidad"],"precio unitario (EUR)":i["precio_unitario"],"subtotal (EUR)":i["subtotal"]}for i in pedido["items"]],hide_index=True)
