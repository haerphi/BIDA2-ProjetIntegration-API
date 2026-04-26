# Application de réservation de terrain dans un club de tennis

Pouvoir avoir le contexte de l'application, veuillez vous référer au repository : https://github.com/haerphi/BIDA2-ProjetIntegration.

## Prérequis

- Python 3.13
- Poetry
- Base de données PostgreSQL

## Installation

```bash
poetry install --no-root
```

## Configuration

```bash
cp .env.example .env
```

## Migration

```bash
poetry run python src/manage.py migrate --settings=core.settings.local
```

## Create superuser

Le superuser sera nécessaire pour accéder à l'admin de l'application (ce qui est nécessaire pour activer les membres et les terrains...).

Si Environnement Docker:

```bash
  docker compose -p tennis-club exec -e DJANGO_SUPERUSER_PASSWORD="Test1234=" api python src/manage.py createsuperuser --affiliation_number admin --email admin@example.com --first_name Admin --last_name Admin --noinput
```

Si environnement Linux:

TODO

## Lancement

```bash
poetry run python src/manage.py runserver --settings=core.settings.local
```

## Tests

```bash
poetry run python src/manage.py test
```

## Swagger

```bash
http://localhost:8000/api/docs/
```

et

```bash
http://localhost:8000/api/redoc/
```
