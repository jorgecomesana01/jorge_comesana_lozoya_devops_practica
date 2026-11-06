# Esquemas Pydantic de pedido. 
# La gracia es que toda la lógica sea la ya hecha, asi que aquí solo se lo "envío" a la API por asi decirlo
# Autor: Jorge Comesaña Lozoya

from datetime import datetime
from pydantic import BaseModel,ConfigDict,Field
from models.pedido import Pedido
from schemas.usuario import UsuarioRead


class PedidoItemCreate(BaseModel):
    """
    Una linea del pedido que envia el cliente de la API: que producto y cuantas unidades
    """
    producto_id:str=Field(min_length=1,description="Id del producto")
    cantidad:int=Field(gt=0,description="Unidades pedidas (mayor que 0)")


class PedidoCreate(BaseModel):
    """
    Datos para crear un pedido: quien lo hace y que lineas incluye
    """
    model_config=ConfigDict(
        json_schema_extra={"examples":[{"cliente_id":"cliente-pedro","items":[{"producto_id":"producto-gafas","cantidad":2},{"producto_id":"producto-clean-code","cantidad":1}]}]},)
    cliente_id:str=Field(min_length=1,description="Id del cliente que hace el pedido")
    items:list[PedidoItemCreate]=Field(min_length=1,description="Al menos una linea de pedido")


class PedidoItemRead(BaseModel):
    """
    Una linea de un pedido ya realizado
    """
    producto_id:str
    nombre:str
    precio_unitario:float
    cantidad:int
    subtotal:float


class PedidoRead(BaseModel):
    """
    Pedido completo que devuelve la API
    """
    id:str
    fecha_pedido:datetime
    cliente:UsuarioRead
    total:float
    items:list[PedidoItemRead]

    @classmethod
    def desde_dominio(cls,pedido:Pedido)->"PedidoRead":
        items=[PedidoItemRead(producto_id=producto.id,nombre=producto.nombre,precio_unitario=producto.precio,cantidad=cantidad,subtotal=round(producto.precio*cantidad,2)) for producto,cantidad in pedido.lista_items]
        return cls(id=pedido.id,fecha_pedido=pedido.fecha_pedido,cliente=UsuarioRead.desde_dominio(pedido.cliente),total=round(pedido.total_compra(),2),items=items)
