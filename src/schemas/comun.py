# Esquemas comunes a toda la API
# Autor: Jorge Comesaña Lozoya

from pydantic import BaseModel


class ErrorRead(BaseModel):
    """
    Formato de las respuestas de error (el mismo que usa FastAPI con HTTPException)
    """

    detail:str
