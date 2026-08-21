FROM python:3.13.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements/production.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install --requirement /tmp/requirements.txt

COPY --chown=app:app . /app

USER app

EXPOSE 8000

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]

