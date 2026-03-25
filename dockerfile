FROM python:3.13.2-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/www/api
COPY requirements.txt ./
RUN apt-get install poppler-utils
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . .