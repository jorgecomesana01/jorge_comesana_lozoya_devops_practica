# Excepciones propias de la tienda
# Autor: Jorge Comesaña Lozoya

# Todas heredan de ValueError a proposito: asi el codigo que ya capturaba ValueError sigue funcionando igual, 
# y la API puede distinguir el tipo de fallo para devolver el codigo HTTP adecuado (404, 409...) sin leer el texto del mensaje.


class TiendaError(ValueError):
    """
    Error base de la logica de la tienda
    """


class ClienteNoEncontradoError(TiendaError):
    """
    El id no corresponde a ningun usuario de tipo cliente
    """


class ProductoNoEncontradoError(TiendaError):
    """
    El id no corresponde a ningun producto del inventario
    """


class StockInsuficienteError(TiendaError):
    """
    No hay unidades suficientes para cubrir lo pedido
    """
