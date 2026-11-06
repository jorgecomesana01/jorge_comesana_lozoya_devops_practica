# Esquemas Pydantic de producto
# Autor: Jorge Comesaña Lozoya

from enum import Enum
from pydantic import BaseModel,ConfigDict,Field,model_validator
from models.producto import Producto,ProductoElectronico,ProductoRopa,ProductoLibro


class TipoProducto(str,Enum):
    """
    Tipos de producto que acepta la API
    """
    generico="generico"
    electronico="electronico"
    ropa="ropa"
    libro="libro"


# Atributos propios de cada tipo. Sirve para validar que llegan todos los necesarios y ninguno diferente del tipo
ATRIBUTOS_POR_TIPO:dict[TipoProducto, tuple[str, ...]]={
    TipoProducto.generico:(),
    TipoProducto.electronico:("meses_garantia",),
    TipoProducto.ropa:("talla","color"),
    TipoProducto.libro:("autor","edicion"),}
TODOS_LOS_ATRIBUTOS=("meses_garantia","talla","color","autor","edicion")


class ProductoCreate(BaseModel):
    """
    Datos que envia el cliente de la API para crear un producto. Los atributos extra dependen del tipo
    """
    model_config=ConfigDict(str_strip_whitespace=True,json_schema_extra={
        "examples": [
                {"tipo":"generico","nombre":"Gafas eclipse","precio":15.95,"stock":24},
                {"tipo":"electronico","nombre":"GPU QueNvidia A100","precio":24999.99,"stock":6,"meses_garantia":48},
                {"tipo":"ropa","nombre":"Camiseta de España 2 estrellas","precio":25.0,"stock":50,"talla":"M","color":"Blanco"},
                {"tipo":"libro","nombre":"Clean Code","precio":43.72,"stock":17,"autor":"Robert C. Martin","edicion":"1ª"},]},)

    tipo:TipoProducto
    nombre:str=Field(min_length=1,max_length=150)
    precio:float=Field(gt=0,description="Precio unitario en euros")
    stock:int=Field(ge=0,description="Unidades disponibles")
    meses_garantia:int|None=Field(default=None,gt=0,description="Solo electrónicos")      # Mayor que 0
    talla:str|None=Field(default=None,min_length=1,max_length=20,description="Solo ropa")   
    color:str|None=Field(default=None,min_length=1,max_length=50,description="Solo ropa")
    autor:str|None=Field(default=None,min_length=1,max_length=100,description="Solo libros")
    edicion:str|None=Field(default=None,min_length=1,max_length=50,description="Solo libros")

    @model_validator(mode="after")
    def validar_atributos_segun_tipo(self):
        esperados=ATRIBUTOS_POR_TIPO[self.tipo]
        faltan=[a for a in esperados if getattr(self,a) is None]
        sobran=[a for a in TODOS_LOS_ATRIBUTOS if a not in esperados and getattr(self,a) is not None]
        if faltan:
            raise ValueError(f"Un producto de tipo '{self.tipo.value}' necesita: {', '.join(faltan)}")
        if sobran:
            raise ValueError(f"Un producto de tipo '{self.tipo.value}' no admite: {', '.join(sobran)}")
        return self

    def a_dominio(self)->Producto:
        """
        Construye el objeto de dominio que corresponde al tipo (reutiliza las clases ya existentes)
        """
        if self.tipo==TipoProducto.electronico:
            return ProductoElectronico(self.nombre,self.precio,self.stock,self.meses_garantia)
        if self.tipo==TipoProducto.ropa:
            return ProductoRopa(self.nombre,self.precio,self.stock,self.talla,self.color)
        if self.tipo==TipoProducto.libro:
            return ProductoLibro(self.nombre,self.precio,self.stock,self.autor,self.edicion)
        return Producto(self.nombre,self.precio,self.stock)


class ProductoRead(BaseModel):
    """
    Datos de un producto que devuelve la API. Los atributos que no aplican al tipo salen como None (los endpoints usan response_model_exclude_none para no mostrarlos)
    """
    id:str
    tipo:TipoProducto
    nombre:str
    precio:float
    stock:int
    meses_garantia:int|None=None
    talla:str|None=None
    color:str|None=None
    autor:str|None=None
    edicion:str|None=None

    @classmethod
    def desde_dominio(cls,producto:Producto)->"ProductoRead":
        if isinstance(producto,ProductoElectronico):
            tipo=TipoProducto.electronico
        elif isinstance(producto,ProductoRopa):
            tipo=TipoProducto.ropa
        elif isinstance(producto,ProductoLibro):
            tipo=TipoProducto.libro
        else:
            tipo=TipoProducto.generico
        extras={a:getattr(producto,a) for a in ATRIBUTOS_POR_TIPO[tipo]}
        return cls(id=producto.id,tipo=tipo,nombre=producto.nombre,precio=producto.precio,stock=producto.stock,**extras)
