# Usa la imagen base de Python
FROM python:3.10.16-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto
COPY . .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto (ajústalo si usas otro)
EXPOSE 5000

# Establece la variable de entorno para Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Comando para correr la app
CMD ["flask", "run", "--host=0.0.0.0"]
