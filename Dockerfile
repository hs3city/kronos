ARG PYTHON_VERSION=3.10.9

FROM python:$PYTHON_VERSION-slim

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    curl=7.74.0-1.3+deb11u7 \
    gcc=4:10.2.1-1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser
USER appuser

WORKDIR /home/appuser/bot

ENV PYTHONPATH=/home/appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
CMD ["python", "bot.py"]
