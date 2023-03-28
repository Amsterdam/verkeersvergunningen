FROM python:3.9-buster as app
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR=off

RUN apt-get update \
 && apt-get dist-upgrade -y \
 && apt-get install --no-install-recommends -y \
        gdal-bin \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --upgrade pip \
 && pip install uwsgi \
 && useradd --user-group --system datapunt

WORKDIR /app/install
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY deploy /app/deploy

WORKDIR /app/src
COPY src .

ARG SECRET_KEY=not-used
ARG CLEOPATRA_BASIC_AUTH_USER=not-used
ARG CLEOPATRA_BASIC_AUTH_PASS=not-used
RUN python manage.py collectstatic --no-input

USER datapunt

CMD ["/app/deploy/docker-run.sh"]


# stage 2, dev
FROM app as dev

USER root
WORKDIR /app/install
ADD requirements_dev.txt requirements_dev.txt
RUN pip install -r requirements_dev.txt

WORKDIR /app/src
USER datapunt

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME /tmp

CMD ["./manage.py", "runserver", "0.0.0.0:8000"]


# stage 3, tests
FROM dev as tests

USER datapunt
WORKDIR /app/tests
ADD tests .
COPY pyproject.toml /app/.

ENV COVERAGE_FILE=/tmp/.coverage
ENV PYTHONPATH=/app/src

CMD ["sleep 1000"]
