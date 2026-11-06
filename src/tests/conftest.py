# Tests de configuracion
# Autor: Jorge Comesaña Lozoya


import pytest
from fastapi.testclient import TestClient
from main import app,get_servicio
from services.tienda_service import TiendaService


@pytest.fixture     # Con fixture la siguiente funcion es una preparcion para test, por lo que cuando se ejecute un test antes se ejecutará la funcion con fixture, preparando, en este caso, un servicio nuevo para cada test
def servicio():
    """
    Un servicio vacio por test, para que no se mezclen datos entre pruebas
    """
    return TiendaService()


# Aqui aprovecho el Depends de ServicioDep del main para que los endpoints usen el servicio del test (que está vacio por la def anterior)
@pytest.fixture
def client(servicio):
    app.dependency_overrides[get_servicio]=lambda:servicio
    with TestClient(app) as c:
        yield c          # 'yield' funciona como un return pero con pausa. Le entrega c al test, el test se ejecuta, y cuando acaba el codigo se sigue ejecutando enla linea siguiente de yield
    app.dependency_overrides.clear()        # aqui limpio, quitando las sustituciones para que no afecte a otros test


# Ayudas para preparar datos a traves de la propia API
def crear_cliente(client,nombre="Pedro Picapiedra",email="pedro@piedradura.com"):
    r=client.post("/usuarios",json={"nombre":nombre,"email":email,"tipo":"cliente","direccion_postal":"Calle Triceratops 64"})
    assert r.status_code==201,r.text
    return r.json()


def crear_admin(client,nombre="Jorge",email="jorge@tienda.com"):
    r=client.post("/usuarios",json={"nombre":nombre,"email":email,"tipo":"admin"})
    assert r.status_code==201,r.text
    return r.json()


def crear_producto(client,**datos):
    base={"tipo":"generico","nombre":"Gafas eclipse","precio":15.95,"stock":24}
    base.update(datos)
    r=client.post("/productos",json=base)
    assert r.status_code in (200,201),r.text
    return r.json()
