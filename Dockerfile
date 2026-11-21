# Custom image for Assignment 04 - displays the Kubernetes pod name.
# Small official Python base image (Debian slim).
FROM python:3.12-slim

# Don't write .pyc files, flush logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app
COPY app/app.py .

# Run as an unprivileged user (security best practice)
RUN useradd --uid 10001 --no-create-home appuser
USER 10001

EXPOSE 8080

# Lets Docker itself check the container is healthy
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1

CMD ["python", "app.py"]
