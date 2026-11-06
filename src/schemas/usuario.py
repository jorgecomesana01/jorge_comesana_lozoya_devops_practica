# Esquemas Pydantic de usuario
# Autor: Jorge Comesaña Lozoya

from enum import Enum
from pydantic import BaseModel,ConfigDict,EmailStr,Field,model_validator
from models.usuario import Usuario


class TipoUsuario(str,Enum):
    """
    Tipos de usuario que acepta la API (los mismos que entiende TiendaService.registrar_usuario)
    """
    cliente="cliente"
    admin="admin"


class UsuarioCreate(BaseModel):
    """
    Datos que envia el cliente de la API para crear un usuario
    """
    model_config=ConfigDict(str_strip_whitespace=True,json_schema_extra={
            "examples": [
                {"nombre":"Pedro Picapiedra","email":"pedro@piedradura.com","tipo":"cliente","direccion_postal":"Calle Triceratops 64, Piedradura"},
                {"nombre":"Jorge Comesaña","email":"jorge@tienda.com","tipo":"admin"},]},)

    nombre:str=Field(min_length=1,max_length=100,description="Nombre completo del usuario")
    email:EmailStr=Field(description="Correo electrónico con formato válido")
    tipo:TipoUsuario=Field(description="'cliente' o 'admin'")
    direccion_postal:str|None=Field(default=None,min_length=1,max_length=200,description="Obligatoria para clientes. Los admins no tienen dirección postal")

    @model_validator(mode="after")
    def validar_direccion_segun_tipo(self):
        if self.tipo==TipoUsuario.cliente and self.direccion_postal is None:
            raise ValueError("Un cliente necesita 'direccion_postal'")
        if self.tipo==TipoUsuario.admin and self.direccion_postal is not None:
            raise ValueError("Un admin no tiene 'direccion_postal'")
        return self


class UsuarioRead(BaseModel):
    """
    Datos de un usuario que devuelve la API
    """
    id:str
    nombre:str
    email:str
    es_admin:bool

    @classmethod
    def desde_dominio(cls,usuario:Usuario)->"UsuarioRead":
        return cls(id=usuario.id,nombre=usuario.nombre,email=usuario.email,es_admin=usuario.is_admin())
