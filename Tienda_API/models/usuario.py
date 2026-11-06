# Clase Usuario
# Autor: Jorge Comesaña Lozoya

import uuid


class Usuario:
    """
    Clase de cualquier usuario de la tienda
    """


    def __init__(self,nombre:str,email:str):
        self.id:str=str(uuid.uuid4())
        self.nombre:str=nombre
        self.email:str=email


    def is_admin(self)->bool:
        """
        Determina si el usuario es o no es admin. Por defecto está en false y ya se cambiará en el user que sea admin
        """

        return False



class Cliente(Usuario):
    """
    Subclase que representa a un cliente
    """


    def __init__(self,nombre:str,email:str,direccion_postal:str):
        super().__init__(nombre,email)
        self.direccion_postal:str=direccion_postal



class Admin(Usuario):
    """
    Subclase para los admin de la tienda
    """


    def __init__(self,nombre:str,email:str):
        super().__init__(nombre,email)


    def is_admin(self)->bool:
        """
        Sobreescribe el metodo base para cambiar a rol de admin
        """

        return True
    