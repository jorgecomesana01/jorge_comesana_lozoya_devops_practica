# Cliente Python de la API de la tienda online (solo HTTP, con la libreria requests)
# Autor: Jorge Comesaña Lozoya

# Este script no importa nada de la aplicacion FastAPI (ni TiendaService, ni los modelos, ni los esquemas):
# toda la comunicacion es por HTTP. 
# Por eso funciona igual contra localhost que contra otro ordenador.

# Uso:
#   python cliente.py                              -> usa el BASE_URL de abajo
#   python cliente.py http://192.168.1.34:8000     -> usa esa direccion sin tocar el codigo

import sys

import requests

# Direccion de la API. En el mismo equipo: localhost. En otro equipo de la red: la IP del que ejecuta la API.
BASE_URL="http://localhost:8000"

TIMEOUT=5     # segundos que se espera una respuesta antes de dar la API por inaccesible


class ErrorAPI(Exception):
    """
    No se ha podido contactar con la API, o ha respondido con un codigo HTTP que no se esperaba
    """


class ClienteTienda:
    """
    Una funcion por endpoint de la API. Todas devuelven la tupla (codigo_http, json_de_la_respuesta)
    """

    def __init__(self,base_url:str,timeout:float=TIMEOUT):
        self.base_url=base_url.rstrip("/")
        self.timeout=timeout

    def _peticion(self,metodo:str,ruta:str,esperado:tuple,**kwargs):
        """
        Envia la peticion, comprueba que el codigo HTTP sea uno de los esperados y devuelve (codigo, json)
        """
        url=f"{self.base_url}{ruta}"
        try:
            r=requests.request(metodo,url,timeout=self.timeout,**kwargs)
        except requests.exceptions.ConnectionError:
            raise ErrorAPI(f"No se puede conectar con {self.base_url}. Comprobar que la API esta arrancada, que la direccion es correcta y, si es otro equipo, el firewall y que uvicorn use --host 0.0.0.0") from None
        except requests.exceptions.Timeout:
            raise ErrorAPI(f"La API en {self.base_url} no ha respondido en {self.timeout} segundos") from None

        print(f"\t{metodo:<6} {ruta:<42} -> HTTP {r.status_code}")
        try:
            cuerpo=r.json() if r.content else None
        except ValueError:                  # la respuesta no era JSON
            cuerpo={"detail":r.text[:200]}
        if r.status_code not in esperado:
            detalle=cuerpo.get("detail") if isinstance(cuerpo,dict) else cuerpo
            raise ErrorAPI(f"{metodo} {ruta}: se esperaba {list(esperado)} y la API respondio {r.status_code} ({detalle})")
        return r.status_code,cuerpo

    # Usuarios
    def crear_usuario(self,nombre,email,tipo="cliente",direccion_postal=None):
        """
        POST /usuarios
        """
        datos={"nombre":nombre,"email":email,"tipo":tipo}
        if direccion_postal is not None:
            datos["direccion_postal"]=direccion_postal
        return self._peticion("POST","/usuarios",(201,),json=datos)

    def listar_usuarios(self):
        """
        GET /usuarios
        """
        return self._peticion("GET","/usuarios",(200,))

    def obtener_usuario(self,usuario_id,esperado=(200,)):
        """
        GET /usuarios/{usuario_id}
        """
        return self._peticion("GET",f"/usuarios/{usuario_id}",esperado)

    # Productos
    def crear_producto(self, datos: dict, esperado=(200, 201)):
        """
        POST /productos  (201 = producto nuevo; 200 = ya existia y se ha sumado el stock)
        """
        return self._peticion("POST","/productos",esperado,json=datos)

    def listar_productos(self):
        """
        GET /productos
        """
        return self._peticion("GET","/productos",(200,))

    # Pedidos
    def crear_pedido(self,cliente_id,items:list,esperado=(201,)):
        """
        POST /pedidos   items = [{"producto_id": ..., "cantidad": ...}, ...]
        """
        return self._peticion("POST","/pedidos",esperado,json={"cliente_id":cliente_id,"items":items})

    def listar_pedidos_usuario(self,cliente_id):
        """
        GET /usuarios/{cliente_id}/pedidos
        """
        return self._peticion("GET",f"/usuarios/{cliente_id}/pedidos",(200,))


def corto(identificador:str)->str:
    """
    Acorta los uuid (36 caracteres) para que las listas se lean bien; el resto de ids se dejan tal cual
    """
    return identificador[:8]+"..." if len(identificador)==36 else identificador


def paso(titulo:str)->None:
    print(f"\n{titulo}")


def ejecutar_flujo(api: ClienteTienda)->None:
    paso("1. Crear un usuario")
    _,usuario=api.crear_usuario("Ada Lovelace","ada@ejemplo.com","cliente","Calle Algoritmo 1, Madrid")
    print(f"    creado: {usuario['nombre']} <{usuario['email']}>  id={usuario['id']}")

    paso("2. Consultar la lista de usuarios")
    _,usuarios=api.listar_usuarios()
    for u in usuarios:
        print(f"\t- {u['nombre']:<22} {'admin' if u['es_admin'] else 'cliente':<8} id={corto(u['id'])}")
    if usuario["id"] not in [u["id"] for u in usuarios]:
        raise ErrorAPI("El usuario recien creado no aparece en GET /usuarios")
    print(f"\t{len(usuarios)} usuario(s); el recien creado esta en la lista")

    paso("3. Crear productos")
    productos_nuevos=[
        {"tipo":"generico","nombre":"Auriculares Bluetooth","precio":29.90,"stock":10},
        {"tipo":"electronico","nombre":"Teclado mecanico","precio":79.00,"stock":10,"meses_garantia":24},
        {"tipo":"ropa","nombre":"Sudadera Python","precio":39.95,"stock":10,"talla":"M","color":"Negro"},
    ]
    creados=[]
    for datos in productos_nuevos:
        codigo,producto=api.crear_producto(datos)
        accion="creado" if codigo==201 else "ya existia: stock sumado"
        print(f"\t{accion}: {producto['nombre']} (stock ahora {producto['stock']})")
        creados.append(producto)

    paso("4. Consultar la lista de productos")
    _,productos=api.listar_productos()
    for p in productos:
        print(f"\t- {p['nombre'][:34]:<34} {p['tipo']:<12} {p['precio']:>9.2f} EUR  stock {p['stock']:<4} id={corto(p['id'])}")

    paso("5. Crear un pedido")
    auriculares,_teclado,sudadera=creados
    items=[{"producto_id":auriculares["id"],"cantidad":2},{"producto_id":sudadera["id"],"cantidad":1}]
    _,pedido=api.crear_pedido(usuario["id"], items)
    print(f"\tpedido {corto(pedido['id'])} para {pedido['cliente']['nombre']}, total {pedido['total']:.2f} EUR")
    for linea in pedido["items"]:
        print(f"\t{linea['cantidad']} x {linea['nombre']} = {linea['subtotal']:.2f} EUR")

    paso("6. Consultar los pedidos del usuario")
    _,pedidos=api.listar_pedidos_usuario(usuario["id"])
    for p in pedidos:
        print(f"\t- {p['fecha_pedido'][:16].replace('T',' ')}  {p['total']:.2f} EUR  ({len(p['items'])} linea(s))")
    if pedido["id"] not in [p["id"] for p in pedidos]:
        raise ErrorAPI("El pedido recien creado no aparece en el historial del usuario")
    print("\tel pedido recien creado esta en el historial")

    paso("7. Comprobar los errores esperados")
    codigo,cuerpo=api.obtener_usuario("id-que-no-existe",esperado=(404,))
    print(f"\tusuario inexistente        -> {codigo}: {cuerpo['detail']}")
    codigo,cuerpo=api.crear_pedido(usuario["id"],[{"producto_id":auriculares["id"],"cantidad":999999}],esperado=(409,))
    print(f"\tpedido sin stock suficiente -> {codigo}: {cuerpo['detail']}")
    codigo,cuerpo=api.crear_producto({"tipo":"ropa","nombre":"Sin color","precio":10,"stock":1,"talla":"M"},esperado=(422,))
    print(f"    producto con datos invalidos -> {codigo}: {cuerpo['detail'][0]['msg']}")


def main()->None:
    base_url=sys.argv[1] if len(sys.argv)>1 else BASE_URL
    api=ClienteTienda(base_url)
    print(f"Cliente de la tienda online -> API en {api.base_url}")
    try:
        ejecutar_flujo(api)
    except ErrorAPI as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    print("\nFlujo completado correctamente.")


if __name__=="__main__":
    main()
