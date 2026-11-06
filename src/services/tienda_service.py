# Servicios de la tienda
# Autor: Jorge Coemsaña Lozoya

from typing import List,Tuple
from models.usuario import Usuario,Cliente,Admin
from models.producto import Producto
from models.pedido import Pedido
from services.excepciones import ClienteNoEncontradoError,ProductoNoEncontradoError,StockInsuficienteError


class TiendaService:
    """
    Clase que gestiona la logistica de la tienda y simula una base de datosen memoria
    """

    def __init__(self):
        self.usuarios:List[Usuario]=[]
        self.productos:List[Producto]=[]
        self.pedidos:List[Pedido]=[]


    def registrar_usuario(self,tipo:str,nombre:str,email:str,direccion:str="")->Usuario:
        """
        Registra un nuevo usuario segun su tipo (cliente o admin)
        """
        if tipo.lower()=="cliente":
            nuevo_usuario=Cliente(nombre,email,direccion)

        elif tipo.lower()=="admin":
            nuevo_usuario=Admin(nombre,email)

        else:
            raise ValueError("Tipo de usuario no definido. Debe ser 'cliente' o 'admin'.")

        self.usuarios.append(nuevo_usuario)
        return nuevo_usuario


    def añadir_producto(self,nuevo_producto:Producto)->Producto:
        """
        Añade un producto al inventario. 
        Si ya existe el mismo articulo (mismo tipo, nombre, precio y atributos propios, como talla y color en la ropa) suma el stock al existente. 
        Devuelve el producto que ha quedado en el inventario: el nuevo, o el existente si se ha fusionado (se distingue con 'resultado is nuevo_producto')
        """
        for prod_existente in self.productos:
            if prod_existente.es_equivalente(nuevo_producto):
                prod_existente.actualizar_stock(nuevo_producto.stock)
                return prod_existente
        self.productos.append(nuevo_producto)
        return nuevo_producto


    def buscar_producto_por_id(self,id_producto:str)->Producto|None:
        """
        Busca un producto del inventario por su id
        """
        for producto in self.productos:
            if producto.id==id_producto:
                return producto
        return None



    def eliminar_producto(self,id_producto:str)->bool:
        """
        Elimina el producto del inventario mediante el id
        """
        for producto in self.productos:
            if producto.id==id_producto:
                self.productos.remove(producto)
                return True
        return False


    def listar_productos(self)->List[Producto]:
        """
        Da la lista de todos los productos disponibles
        """
        return self.productos


    def _buscar_cliente(self,id_usuario:str)->Cliente|None:
        """
        Busca un cliente por su id. Metodo interno ya que solo se usa para hacer pedidos, no en el main
        """
        for usuario in self.usuarios:
            if usuario.id==id_usuario and isinstance(usuario,Cliente):
                return usuario
        return None

    
    def realizar_pedido(self,id_cliente:str,carro_compra:List[Tuple[Producto,int]])->Pedido:
        """
        Crea un pedido. Primero verifica la existencia del cliente y el stock. Luego resta del stock lo pedido y por ultimo genera el pedido
        """
        cliente=self._buscar_cliente(id_cliente)
        if not cliente:
            raise ClienteNoEncontradoError("Cliente no existente o el usuario no es de tipo 'cliente'.")
        if not carro_compra:
            raise ValueError("El pedido no contiene ningun producto.")

        # Si el mismo producto aparece en varias lineas se suman antes de comprobar el stock; 
        # si no, cada linea pasaria la comprobacion por separado y juntas podrian dejar el stock en negativo
        totales:dict[str,list]={}
        for producto, cantidad_pedida in carro_compra:
            if cantidad_pedida<=0:
                raise ValueError(f"La cantidad pedida de {producto.nombre} debe ser mayor que 0.")
            if producto.id in totales:
                totales[producto.id][1]+=cantidad_pedida
            else:
                totales[producto.id]=[producto,cantidad_pedida]
        lineas:List[Tuple[Producto,int]]=[(producto,cantidad) for producto,cantidad in totales.values()]

        for producto,cantidad_pedida in lineas:
            if not producto.hay_stock(cantidad_pedida):
                raise StockInsuficienteError(f"Stock insuficiente para el producto: {producto.nombre}. Disponible: {producto.stock}. Solicitado: {cantidad_pedida}.")

        for producto,cantidad_pedida in lineas:
            producto.actualizar_stock(-cantidad_pedida)
        nuevo_pedido=Pedido(cliente, lineas)
        self.pedidos.append(nuevo_pedido)
        return nuevo_pedido


    def lista_pedidos_usuario(self,id_usuario:str)->List[Pedido]:
        """
        Da los pedidos del usuario ordenados por fecha
        """
        pedidos_usuario=[p for p in self.pedidos if p.cliente.id==id_usuario]
        pedidos_usuario.sort(key=lambda p:p.fecha_pedido)
        return pedidos_usuario


    # Los siguientes métodos son útiles para la API y la lógica interna
    def eliminar_usuario(self,id_usuario:str)->bool:
        """
        Elimina un usuario del sistema mediante su id
        """
        for usuario in self.usuarios:
            if usuario.id==id_usuario:
                self.usuarios.remove(usuario)
                return True
        return False


    def listar_usuarios(self)->List[Usuario]:
        """
        Da la lista de todos los usuarios registrados (clientes y admins)
        """
        return self.usuarios


    def buscar_usuario_por_id(self,id_usuario:str)->Usuario|None:
        """
        Busca usuarios por id
        """
        for usuario in self.usuarios:
            if usuario.id==id_usuario:
                return usuario
        return None


    def es_admin_valido(self,id_usuario:str)->bool:
        """
        Compruebaque el usuario es un admin  para poder eliminar usuarios en el main. Es, basicamente,un control de seguridad
        """
        usuario=self.buscar_usuario_por_id(id_usuario)
        return usuario is not None and usuario.is_admin()