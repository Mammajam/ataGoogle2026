FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
# Deploy script copies repo fixtures/ → agent/bundled_fixtures before `gcloud run deploy --source`.
ENV GREENCHAIN_FIXTURES=/app/bundled_fixtures
ENV GREENCHAIN_STORE=file
ENV GOOGLE_GENAI_USE_VERTEXAI=TRUE
ENV GOOGLE_CLOUD_LOCATION=us-central1
ENV GEMINI_MODEL=gemini-3.5-flash
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
