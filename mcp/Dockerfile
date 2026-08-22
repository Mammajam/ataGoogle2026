FROM python:3.12-slim

WORKDIR /app
COPY mcp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY agent/ /app/agent
COPY mcp/ /app/mcp
COPY fixtures/ /fixtures
ENV GREENCHAIN_FIXTURES=/fixtures
ENV PYTHONPATH=/app/agent
ENV PORT=8081
EXPOSE 8081
CMD ["python", "mcp/server.py"]
