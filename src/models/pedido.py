# Clase Pedido
# Autor: Jorge Comesaña Lozoya

import uuid
from datetime import datetime
from typing import List,Tuple
from models.usuario import Cliente
from models.producto import Producto


class Pedido:
    """
    Representa un pedido hecho por un cliente
    """

    def __init__(self,cliente:Cliente,lista_items:List[Tuple[Producto, int]]):
        self.id:str=str(uuid.uuid4())
        self.cliente:Cliente=cliente
        self.lista_items:List[Tuple[Producto,int]]=lista_items     # Haciendolo asi queda una lista de tuplas formadas por el producto y la cantidad 
        self.fecha_pedido:datetime=datetime.now()


    def __str__(self)->str:

        fecha_str=self.fecha_pedido.strftime("%Y-%m-%d %H:%M")
        return (f"Pedido con id {self.id[:8]} - Cliente: {self.cliente.nombre}. - "
                f"Fecha: {fecha_str} - Total: {self.total_compra():.2f} euros.")


    def total_compra(self)->float:
        """
        Metodo que calcula el importe total de una compra sumando los precios de los productos en la lista
        """
        total=0.0
        for producto,cantidad in self.lista_items:
            total+=producto.precio*cantidad
        return total

    