# Application de réservation de terrain dans un club de tennis

## Contextes

Pour pouvoir réserver un terrain, il faut être membre du club c’est-à-dire être en ordre de cotisation pour la saison courante.

Une saison va du 1er janvier au 31 décembre.

Les réservations se font par heure. Un membre peut réserver un terrain pendant une heure en choisissant un partenaire parmi les membres du club en ordre de cotisation (réservation en simple) ou bien il peut réserver un terrain pendant deux heures d’affilés en choisissant trois partenaires parmi les membres du club en ordre de cotisation (réservation en double).

Par semaine (du dimanche matin au samedi soir), un membre peut avoir soit:

- au maximum deux heures de réservation en simple
- au maximum quatre heures de réservation en double
- une heure de réservation en simple ou deux heures de réservation en double.

Un membre se connecte via son numéro d’affiliation et un mot de passe. Seuls les membres du club
ont accès à l’application. Si le membre se connecte pour la première fois, il devra encoder un mot de
passe (deux fois pour vérification).
Un membre peut supprimer une réservation 24h avant.
Un membre peut modifier ses propres coordonnées et son mot de passe.
La plage de réservation des terrain est de 9h à 22h.
Les administrateurs qui sont également membres du club, peuvent activer les membres en ordre de
cotisation ou désactiver les membres en fin de saison.
Les administrateurs peuvent « bloquer » des terrains pour interclubs, tournois, cours, travaux, …
Les administrateurs peuvent ajouter, supprimer un terrain.
Les administrateurs peuvent modifier les coordonnées des membres, ajouter un membre, réserver un
terrain pour un membre, supprimer un membre.
Les membres peuvent afficher la liste des membres, la liste des membres pour une catégorie donnée,
la liste des membres pour un classement donné, la liste des membres triés par ordre alphabétique
et/ou par ordre de classement, ses réservations, la liste des terrains avec les réservations
Un terrain est identifié par un numéro
Un membre est identifié par son numéro d’affiliation à l’AFT (association fédéral de Tennis) et
caractérisé par un nom, prénom, adresse, numéro de téléphone, e-mail, date de naissance, sexe,
classement.
Les classements possibles sont : A, B-15.4 ; B-15.2 ; B-15.1, B15, B-4/6, B-2/6 ; B0 ; B+2/6 ; B+4/6 ; C15 ;
C15.1 ; C15.2 ; ;C15.3, c15.4 ; C30 ; C30.1, c30.2 ;C30.3 ;C30.4 ; C30.5, N.C
Le numéro d’affiliation est composé de 7 chiffres et peut pas commencer par 0.

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
