FROM python:3.12-slim
# No generar .pyc y mostrar los logs al instante
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# Usuario sin privilegios para ejecutar la app
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Codigo fuente con permisos para appuser
COPY --chown=appuser:appuser Tienda_API/ ./Tienda_API/
USER appuser
WORKDIR /app/Tienda_API
EXPOSE 8000
# Comando de inicio. 0.0.0.0 para ser accesible desde fuera del docker
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]