FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=7860 GRADIO_ANALYTICS_ENABLED=false
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY . .
RUN python -m advisoriq.setup && useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 7860
CMD ["python", "app.py"]
