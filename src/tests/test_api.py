# Test de funcionamiento de la API. El nombre lo dice todo y todos usan una lógica sencilla que no creo necesaria de comentar.
# Autor: Jorge Comesaña Lozoya

from tests.conftest import crear_admin,crear_cliente,crear_producto


# usuarios
def test_crear_cliente_devuelve_201_y_usuario_read(client):
    r=client.post("/usuarios",json={"nombre":"Pedro","email":"pedro@x.com","tipo":"cliente","direccion_postal":"Calle 1"})
    assert r.status_code==201
    cuerpo=r.json()
    assert set(cuerpo)=={"id","nombre","email","es_admin"}
    assert cuerpo["es_admin"] is False


def test_crear_admin_marca_es_admin(client):
    assert crear_admin(client)["es_admin"] is True


def test_cliente_sin_direccion_es_422(client):
    r=client.post("/usuarios",json={"nombre":"Pedro","email":"pedro@x.com","tipo":"cliente"})
    assert r.status_code==422


def test_admin_con_direccion_es_422(client):
    r=client.post("/usuarios",json={"nombre":"Ana","email":"ana@x.com","tipo":"admin","direccion_postal":"Calle 1"})
    assert r.status_code==422


def test_email_invalido_y_tipo_desconocido_son_422(client):
    base={"nombre":"Pedro","email":"pedro@x.com","tipo":"cliente","direccion_postal":"Calle 1"}
    assert client.post("/usuarios",json={**base,"email":"no-es-un-email"}).status_code==422
    assert client.post("/usuarios",json={**base,"tipo":"superadmin"}).status_code==422
    assert client.post("/usuarios",json={**base,"nombre":"   "}).status_code==422


def test_listar_y_obtener_usuarios(client):
    c=crear_cliente(client)
    a=crear_admin(client)
    r=client.get("/usuarios")
    assert r.status_code==200
    assert {u["id"] for u in r.json()}=={c["id"],a["id"]}
    assert client.get(f"/usuarios/{c['id']}").json()==c
    assert client.get("/usuarios/no-existe").status_code==404


# productos
def test_crear_cada_tipo_de_producto(client):
    gen=crear_producto(client)
    ele=crear_producto(client,tipo="electronico",nombre="GPU",precio=999.0,stock=6,meses_garantia=48)
    rop=crear_producto(client,tipo="ropa",nombre="Camiseta",precio=25.0,stock=50,talla="M",color="Blanco")
    lib=crear_producto(client,tipo="libro",nombre="Clean Code",precio=43.72,stock=17,autor="Robert C. Martin",edicion="1ª")
    assert gen["tipo"]=="generico" and ele["meses_garantia"]==48
    assert (rop["talla"],rop["color"])==("M","Blanco")
    assert (lib["autor"],lib["edicion"])==("Robert C. Martin","1ª")


def test_la_respuesta_omite_atributos_que_no_aplican_al_tipo(client):
    gen=crear_producto(client)
    assert set(gen)=={"id","tipo","nombre","precio","stock"}


def test_atributos_obligatorios_y_ajenos_al_tipo_son_422(client):
    base={"nombre":"X","precio":10.0,"stock":1}
    assert client.post("/productos",json={**base,"tipo":"electronico"}).status_code==422
    assert client.post("/productos",json={**base,"tipo":"ropa","talla":"M"}).status_code==422
    assert client.post("/productos",json={**base,"tipo":"libro","autor":"A"}).status_code==422
    assert client.post("/productos",json={**base,"tipo":"generico","talla":"M"}).status_code==422
    assert client.post("/productos",json={**base,"tipo":"ropa","talla":"M","color":"Rojo","autor":"A"}).status_code==422


def test_valores_numericos_invalidos_son_422(client):
    base={"tipo":"generico","nombre":"X","precio":10.0,"stock":1}
    assert client.post("/productos",json={**base,"precio":0}).status_code==422
    assert client.post("/productos", json={**base,"precio":-5}).status_code==422
    assert client.post("/productos",json={**base,"stock":-1}).status_code==422
    assert client.post("/productos",json={**base,"tipo":"electronico","meses_garantia":0}).status_code==422


def test_mismo_articulo_suma_stock_y_responde_200(client):
    primero=client.post("/productos",json={"tipo":"ropa","nombre":"Camiseta","precio":25.0,"stock":50,"talla":"M","color":"Blanco"})
    segundo=client.post("/productos",json={"tipo":"ropa","nombre":"Camiseta","precio":25.0,"stock":10,"talla":"M","color":"Blanco"})
    assert primero.status_code==201 and segundo.status_code==200
    assert segundo.json()["id"]==primero.json()["id"]
    assert segundo.json()["stock"]==60
    assert len(client.get("/productos").json())==1


def test_misma_ropa_con_otra_talla_o_color_es_otro_producto(client):
    crear_producto(client,tipo="ropa",nombre="Camiseta",precio=25.0,stock=50,talla="M",color="Blanco")
    r=client.post("/productos",json={"tipo":"ropa","nombre":"Camiseta","precio":25.0,"stock":40,"talla":"L","color":"Rojo"})
    assert r.status_code==201
    assert len(client.get("/productos").json())==2


def test_mismo_nombre_y_precio_de_distinto_tipo_no_se_fusiona(client):
    crear_producto(client,nombre="Pack",precio=10.0)
    r=client.post("/productos",json={"tipo":"electronico","nombre":"Pack","precio":10.0,"stock":3,"meses_garantia":12})
    assert r.status_code==201
    assert len(client.get("/productos").json())==2


def test_listar_obtener_y_eliminar_producto(client):
    p=crear_producto(client)
    assert client.get("/productos").json()==[p]
    assert client.get(f"/productos/{p['id']}").json()==p
    assert client.delete(f"/productos/{p['id']}").status_code==204
    assert client.get(f"/productos/{p['id']}").status_code==404
    assert client.delete(f"/productos/{p['id']}").status_code==404
    assert client.get("/productos/no-existe").status_code==404


# pedidos
def test_crear_pedido_calcula_total_y_descuenta_stock(client):
    cliente=crear_cliente(client)
    gafas=crear_producto(client,stock=10,precio=15.95)
    libro=crear_producto(client,tipo="libro",nombre="Clean Code",precio=43.72,stock=5,autor="Robert C. Martin",edicion="1ª")
    r=client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[{"producto_id":gafas["id"],"cantidad":2},{"producto_id":libro["id"],"cantidad":1}]})
    assert r.status_code==201
    pedido=r.json()
    assert pedido["cliente"]==cliente
    assert pedido["total"]==round(15.95*2+43.72,2)
    assert {i["producto_id"]:i["cantidad"] for i in pedido["items"]}=={gafas["id"]:2,libro["id"]:1}
    assert pedido["items"][0]["subtotal"]==round(15.95*2,2)
    assert client.get(f"/productos/{gafas['id']}").json()["stock"]==8
    assert client.get(f"/productos/{libro['id']}").json()["stock"]==4


def test_pedido_con_cliente_inexistente_o_admin_es_404(client):
    admin=crear_admin(client)
    p=crear_producto(client)
    for cliente_id in ("no-existe",admin["id"]):
        r=client.post("/pedidos",json={"cliente_id":cliente_id,"items":[{"producto_id":p["id"],"cantidad":1}]})
        assert r.status_code==404
    assert client.get(f"/productos/{p['id']}").json()["stock"]==24


def test_pedido_con_producto_inexistente_es_404_y_no_toca_el_stock(client):
    cliente=crear_cliente(client)
    p=crear_producto(client)
    r=client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[{"producto_id":p["id"],"cantidad":2},{"producto_id":"fantasma","cantidad":1}]})
    assert r.status_code==404
    assert "fantasma" in r.json()["detail"]
    assert client.get(f"/productos/{p['id']}").json()["stock"]==24


def test_stock_insuficiente_es_409_y_no_modifica_nada(client):
    cliente=crear_cliente(client)
    a=crear_producto(client,nombre="A",stock=5)
    b=crear_producto(client,nombre="B",stock=1)
    r=client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[{"producto_id":a["id"],"cantidad":3},{"producto_id":b["id"],"cantidad":2}]})
    assert r.status_code==409
    assert client.get(f"/productos/{a['id']}").json()["stock"]==5
    assert client.get(f"/productos/{b['id']}").json()["stock"]==1
    assert client.get(f"/usuarios/{cliente['id']}/pedidos").json()==[]


def test_lineas_repetidas_se_suman_antes_de_comprobar_stock(client):
    cliente=crear_cliente(client)
    p=crear_producto(client,stock=5)
    items=[{"producto_id":p["id"],"cantidad":3},{"producto_id":p["id"],"cantidad":3}]
    r=client.post("/pedidos",json={"cliente_id":cliente["id"],"items":items})
    assert r.status_code==409
    assert client.get(f"/productos/{p['id']}").json()["stock"]==5
    # y si caben, se unifican en una sola linea
    items=[{"producto_id":p["id"], "cantidad":2},{"producto_id":p["id"],"cantidad":3}]
    r=client.post("/pedidos",json={"cliente_id":cliente["id"],"items":items})
    assert r.status_code==201
    assert [(i["cantidad"]) for i in r.json()["items"]]==[5]
    assert client.get(f"/productos/{p['id']}").json()["stock"]==0


def test_pedido_mal_formado_es_422(client):
    cliente=crear_cliente(client)
    p=crear_producto(client)
    assert client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[]}).status_code==422
    for cantidad in (0,-2):
        r=client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[{"producto_id":p["id"],"cantidad":cantidad}]})
        assert r.status_code==422
    assert client.post("/pedidos",json={"items":[]}).status_code==422


def test_historial_de_pedidos_del_cliente(client):
    pedro=crear_cliente(client)
    otro=crear_cliente(client,nombre="Vegeta",email="vegeta@x.com")
    p=crear_producto(client)
    assert client.get(f"/usuarios/{pedro['id']}/pedidos").json()==[]
    for cliente,cantidad in ((pedro,1),(pedro,2),(otro,3)):
        client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[{"producto_id":p["id"],"cantidad":cantidad}]})
    historial=client.get(f"/usuarios/{pedro['id']}/pedidos").json()
    assert [h["items"][0]["cantidad"] for h in historial]==[1,2]
    assert all(h["cliente"]["id"]==pedro["id"] for h in historial)


def test_historial_de_cliente_inexistente_o_admin_es_404(client):
    admin=crear_admin(client)
    assert client.get("/usuarios/no-existe/pedidos").status_code==404
    assert client.get(f"/usuarios/{admin['id']}/pedidos").status_code==404


def test_el_pedido_conserva_sus_lineas_aunque_se_borre_el_producto(client):
    cliente=crear_cliente(client)
    p=crear_producto(client)
    client.post("/pedidos",json={"cliente_id":cliente["id"],"items":[{"producto_id":p["id"],"cantidad":1}]})
    client.delete(f"/productos/{p['id']}")
    historial=client.get(f"/usuarios/{cliente['id']}/pedidos").json()
    assert historial[0]["items"][0]["nombre"]=="Gafas eclipse"