# Clase Producto
# Autor: Jorge Comesaña Lozoya  

import uuid     # Usaré la opcion de generar un id random con uuid4


class Producto:
    """
    Clase padre para cualquier producto de la tienda
    """


    def __init__(self,nombre:str,precio:float,stock:int):
        self.id:str=str(uuid.uuid4())
        self.nombre:str=nombre
        self.precio:float=precio
        self.stock:int=stock


    def __str__(self)->str:
        return f"[{self.id[:8]}] - {self.nombre} - {self.precio} eur.  (Stock:{self.stock})."


    def hay_stock(self, cantidad:int)->bool:
        """
        Verifica si hay stock disponible para lo pedido
        """

        return self.stock>=cantidad


    def actualizar_stock(self,cantidad:int)->None:
        """"
        Actualiza el stock. Un numero positivo añade (reponer) y uno negativo resta (vender)
        """

        self.stock+=cantidad


    def es_equivalente(self,otro:"Producto")->bool:
        """
        Dice si 'otro' es el mismo articulo (mismo tipo, nombre y precio). Sirve para fusionar stock en vez de duplicar el producto.
        Cada subclase lo amplia con sus atributos propios (talla, color, autor...)
        """

        return type(self) is type(otro) and self.nombre==otro.nombre and self.precio==otro.precio



class ProductoElectronico (Producto):
    """
    Subclase para productos electronicos
    """


    def __init__(self,nombre:str,precio:float,stock:int,meses_garantia:int):
        super().__init__(nombre,precio,stock)
        self.meses_garantia:int=meses_garantia


    def __str__(self)->str:
        str_producto=super().__str__()
        return f"{str_producto} - Garantia: {self.meses_garantia} meses."


    def es_equivalente(self,otro:"Producto")->bool:
        return super().es_equivalente(otro) and self.meses_garantia==otro.meses_garantia



class ProductoRopa(Producto):
    """
    Subclase para ropa, que necesita a mayores datos de talla y color
    """


    def __init__(self,nombre:str,precio:float,stock:int,talla:str,color:str):
        super().__init__(nombre,precio,stock)
        self.talla:str=talla
        self.color:str=color


    def __str__(self)->str:
        str_producto=super().__str__()
        return f"{str_producto} - Talla: {self.talla} - Color: {self.color}."


    def es_equivalente(self,otro:"Producto")->bool:
        return super().es_equivalente(otro) and self.talla==otro.talla and self.color==otro.color



class ProductoLibro(Producto):
    """
    Añado esta subclase extra para vender libros. Tiene los atributos autor y edicion a mayores
    """


    def __init__(self,nombre:str,precio:float,stock:int,autor:str,edicion:str):
        super().__init__(nombre,precio,stock)
        self.autor:str=autor
        self.edicion:str=edicion


    def __str__(self)->str:
        str_producto=super().__str__()
        return f"{str_producto} - Autor: {self.autor} - Edición: {self.edicion}."


    def es_equivalente(self,otro:"Producto")->bool:
        return super().es_equivalente(otro) and self.autor==otro.autor and self.edicion==otro.edicion
