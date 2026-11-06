# Punto de entrada de la API de la tienda online (FastAPI)
# Autor: Jorge Comesaña Lozoya
# Arrancar desde esta carpeta con:   uvicorn main:app --reload
# Documentacion interactiva (Swagger):  http://127.0.0.1:8000/docs
# Este main valida con los esquemas de schemas/, delega el trabajo en TiendaService y traduce los errores del dominio a codigos HTTP. 
# La interfaz de consola anterior ha sido eliminada ante esta mejora.

from typing import Annotated
from fastapi import Depends, FastAPI,HTTPException,Response,status
from models.producto import Producto,ProductoElectronico,ProductoRopa,ProductoLibro
from models.usuario import Cliente
from schemas import (ErrorRead,PedidoCreate,PedidoRead,ProductoCreate,ProductoRead,UsuarioCreate,UsuarioRead)
from services.excepciones import ClienteNoEncontradoError,StockInsuficienteError
from services.tienda_service import TiendaService


app=FastAPI(
    title="Tienda online",
    description="API REST de la tienda online: gestiona usuarios, productos y pedidos sobre TiendaService ""(los datos viven en memoria y se pierden al reiniciar el servidor).",
    version="1.0.0",
)           

# Una unica instancia del servicio para toda la aplicacion (siendo asi la base de datos en memoria)
_servicio=TiendaService()


def cargar_datos_iniciales(servicio:TiendaService)->None:
    """
    Rellena la tienda con usuarios y productos de ejemplo para poder probar la API sin crearlo todo a mano.
    Los ids de estos datos de demo son fijos (en vez de uuid) para que no cambien al reiniciar el servidor y sean faciles de escribir en /docs. 
    Los usuarios y productos que se creen despues tendran uuid normales.
    """

    pedro=servicio.registrar_usuario("cliente","Pedro Picapiedra","SoyElMotorDeMiCoche@gmail.com","Calle Triceratops 64, Piedradura")
    vegeta=servicio.registrar_usuario("cliente","Principe Vegeta IV","AlgunDiaGanareAKakarot@gmail.com","Mansión de Bulma, West City")
    felipe=servicio.registrar_usuario("cliente","Rey Felipe II","TengoUnImperioDondeNoSePoneElSol@gmail.com","Real Alcazar de Madrid")
    admin=servicio.registrar_usuario("admin","Jorge Comesaña","NoVoyAPonerAquiMiMail@gmail.com")
    pedro.id,vegeta.id,felipe.id,admin.id="cliente-pedro","cliente-vegeta","cliente-felipe","admin-jorge"

    gafas=Producto("Gafas eclipse",15.95,24)
    gpu=ProductoElectronico("GPU QueNvidia A100",24999.99,6,meses_garantia=48)
    camiseta_m=ProductoRopa("Camiseta de España 2 estrellas (Contrabando)",25.00,50,talla="M",color="Blanco")
    camiseta_l=ProductoRopa("Camiseta de España 2 estrellas (Contrabando)",25.00,40,talla="L",color="Rojo")
    libro=ProductoLibro("Clean Code: A Handbook of Agile Software Craftsmanship",43.72,17,autor="Robert C. Martin",edicion="1ª")
    gafas.id,gpu.id,camiseta_m.id,camiseta_l.id,libro.id=("producto-gafas","producto-gpu","producto-camiseta-m","producto-camiseta-l","producto-clean-code")
    for producto in (gafas,gpu,camiseta_m,camiseta_l, libro):
        servicio.añadir_producto(producto)


cargar_datos_iniciales(_servicio)    # para arrancar con la tienda vacia, hay que comentar esta linea


def get_servicio()->TiendaService:
    """
    Dependencia de FastAPI que entrega el servicio a cada endpoint. Los tests la sustituyen por uno vacio
    """
    return _servicio

# Con Annotated le digo a python que ServicioDep es de tipo TiendaService y FastAPI debe usar get_servicio para obtener sus datos. Así evito tener que escribirlo en cada endpoint
ServicioDep=Annotated[TiendaService,Depends(get_servicio)]    # Gracias a Depends podemos sustituir el servicio para los test (o para que en uso real con una base de datos real no haya quue tocar los endpoints)

def _cliente_o_404(servicio:TiendaService,cliente_id:str)->Cliente:
    """
    Devuelve el cliente o responde 404 si no existe o el id es de un admin
    """
    usuario=servicio.buscar_usuario_por_id(cliente_id)
    if not isinstance(usuario,Cliente):
        raise HTTPException(status.HTTP_404_NOT_FOUND,f"Cliente '{cliente_id}' no encontrado")
    return usuario


# Usuarios
@app.post("/usuarios",response_model=UsuarioRead,status_code=status.HTTP_201_CREATED,tags=["usuarios"],summary="Crear un usuario")
def crear_usuario(datos:UsuarioCreate,servicio:ServicioDep):
    """
    Crea un cliente (con dirección postal) o un admin (sin ella)
    """
    try:
        usuario=servicio.registrar_usuario(datos.tipo.value,datos.nombre,datos.email,datos.direccion_postal or "")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,str(e))
    return UsuarioRead.desde_dominio(usuario)


@app.get("/usuarios",response_model=list[UsuarioRead],tags=["usuarios"],summary="Listar usuarios")
def listar_usuarios(servicio:ServicioDep):
    """
    Devuelve todos los usuarios registrados: clientes y admins
    """
    return [UsuarioRead.desde_dominio(u) for u in servicio.listar_usuarios()]


@app.get("/usuarios/{usuario_id}",response_model=UsuarioRead,tags=["usuarios"],summary="Consultar un usuario",responses={404:{"model":ErrorRead,"description":"El usuario no existe"}})
def obtener_usuario(usuario_id:str,servicio:ServicioDep):
    """
    Encuentra un usuario por id
    """
    usuario=servicio.buscar_usuario_por_id(usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,f"Usuario '{usuario_id}' no encontrado")
    return UsuarioRead.desde_dominio(usuario)


# Productos
@app.post("/productos",response_model=ProductoRead,response_model_exclude_none=True,status_code=status.HTTP_201_CREATED,tags=["productos"],summary="Crear un producto",
          responses={200:{"model":ProductoRead,"description":"Ya existía el mismo artículo: se ha sumado el stock al producto existente"}})
def crear_producto(datos:ProductoCreate,response:Response,servicio:ServicioDep):
    """
    Crea un producto genérico, electrónico, de ropa o libro; cada tipo exige sus atributos propios.
    Si ya existe el mismo artículo (mismo tipo, nombre, precio y atributos propios) no se duplica: se suma el stock al existente y se responde 200 con ese producto en lugar de 201.
    """
    nuevo=datos.a_dominio()
    resultante=servicio.añadir_producto(nuevo)
    if resultante is not nuevo:
        response.status_code=status.HTTP_200_OK
    return ProductoRead.desde_dominio(resultante)


@app.get("/productos",response_model=list[ProductoRead],response_model_exclude_none=True,tags=["productos"],summary="Listar productos")
def listar_productos(servicio:ServicioDep):
    return [ProductoRead.desde_dominio(p) for p in servicio.listar_productos()]


@app.get("/productos/{producto_id}",response_model=ProductoRead,response_model_exclude_none=True,tags=["productos"],summary="Consultar un producto",
         responses={404: {"model":ErrorRead,"description":"El producto no existe"}})
def obtener_producto(producto_id:str,servicio:ServicioDep):
    """
    Busca producto por id
    """
    producto=servicio.buscar_producto_por_id(producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,f"Producto '{producto_id}' no encontrado")
    return ProductoRead.desde_dominio(producto)


@app.delete("/productos/{producto_id}",status_code=status.HTTP_204_NO_CONTENT,tags=["productos"],summary="Eliminar un producto",
            responses={404:{"model":ErrorRead,"description":"El producto no existe"}})
def eliminar_producto(producto_id:str,servicio:ServicioDep):
    """
    Lo quita del inventario. Los pedidos ya realizados conservan sus líneas
    """
    if not servicio.eliminar_producto(producto_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND,f"Producto '{producto_id}' no encontrado")


# Pedidos
@app.post("/pedidos",response_model=PedidoRead,status_code=status.HTTP_201_CREATED,tags=["pedidos"],summary="Crear un pedido",
          responses={404:{"model":ErrorRead,"description":"No existe el cliente o algún producto"},
                     409:{"model":ErrorRead,"description":"Stock insuficiente"}})
def crear_pedido(datos:PedidoCreate,servicio:ServicioDep):
    """
    Comprueba que existan el cliente y todos los productos y que haya stock para todo,
    sólo entonces descuenta el stock y registra el pedido. Si algo falla no se modifica nada
    """
    _cliente_o_404(servicio,datos.cliente_id)
    carro=[]
    no_encontrados=[]
    for item in datos.items:
        producto=servicio.buscar_producto_por_id(item.producto_id)
        if producto is None:
            no_encontrados.append(item.producto_id)
        else:
            carro.append((producto, item.cantidad))
    if no_encontrados:
        raise HTTPException(status.HTTP_404_NOT_FOUND,f"Producto/s no encontrado/s: {', '.join(no_encontrados)}")

    try:
        pedido=servicio.realizar_pedido(datos.cliente_id,carro)
    except ClienteNoEncontradoError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND,str(e))
    except StockInsuficienteError as e:
        raise HTTPException(status.HTTP_409_CONFLICT,str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,str(e))
    return PedidoRead.desde_dominio(pedido)


@app.get("/usuarios/{cliente_id}/pedidos",response_model=list[PedidoRead],tags=["pedidos"],summary="Historial de pedidos de un cliente",
         responses={404:{"model":ErrorRead,"description":"El cliente no existe"}})
def listar_pedidos_cliente(cliente_id:str,servicio:ServicioDep):
    """
    Pedidos del cliente ordenados del más antiguo al más reciente (lista vacía si aún no ha comprado)
    """
    cliente=_cliente_o_404(servicio,cliente_id)
    return [PedidoRead.desde_dominio(p) for p in servicio.lista_pedidos_usuario(cliente.id)]
