FROM python:3.11-slim

WORKDIR /app

# Dependencias del servicio.
COPY services/academico/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo compartido y codigo del servicio.
COPY shared ./shared
COPY services/academico/app ./app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
