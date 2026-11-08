# API de gestion d'un atelier de couture

API REST (FastAPI + PostgreSQL) pour l'atelier de Mamadou, tailleur à Dakar : clients, mesures,
commandes, paiements, livraisons et statistiques. Projet final du module « Développement d'API
avec FastAPI et PostgreSQL ».

## Architecture

```
app/
  routers/    un fichier par domaine : vérifient les droits, appellent un service, valident la transaction
  services/   toute la logique métier (règles de gestion), testable séparément
  models/     modèles SQLAlchemy 2 (Mapped, mapped_column)
  schemas/    schémas Pydantic distincts : création, modification, lecture
  deps.py     authentification JWT et contrôle des rôles
  security.py hachage Argon2 et jetons JWT
  seed.py     premier administrateur et catalogue de départ
alembic/      migrations : le schéma se crée avec « alembic upgrade head »
tests/        tests pytest (TestClient, SQLite en mémoire)
```

Les modèles SQLAlchemy et les schémas Pydantic sont séparés : le hash du mot de passe n'est
jamais renvoyé par l'API.

## Prérequis

- Python 3.11 ou plus
- PostgreSQL 16 (ou Docker, voir plus bas)

## Installation et lancement en local

```bash
git clone https://github.com/fatoufall737/api-atelier-couture.git
cd api-atelier-couture
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

1. Créez une base et un utilisateur PostgreSQL :

   ```sql
   CREATE USER atelier WITH PASSWORD 'votre-mot-de-passe';
   CREATE DATABASE atelier OWNER atelier;
   ```

2. Copiez `.env.example` en `.env` et renseignez les valeurs (jamais de secret dans Git) :

   ```bash
   cp .env.example .env               # Windows : copy .env.example .env
   ```

   Générez la clé secrète avec :
   `python -c "import secrets; print(secrets.token_hex(32))"`

3. Créez le schéma, l'administrateur et le catalogue, puis lancez l'API :

   ```bash
   alembic upgrade head
   python -m app.seed
   uvicorn app.main:app --reload
   ```

L'API est disponible sur http://127.0.0.1:8000 et la documentation interactive (Swagger) sur
http://127.0.0.1:8000/docs.

## Lancement avec Docker

```bash
cp .env.example .env               # puis renseignez les valeurs, dont POSTGRES_*
docker compose up --build
```

Le conteneur applique les migrations, exécute le seed, puis démarre l'API sur
http://localhost:8000. Pour repartir d'une base vide : `docker compose down -v`.

## Tests

```bash
pytest
```

Les tests utilisent SQLite en mémoire : ils ne touchent pas à votre base PostgreSQL.

## Comptes de test

Le compte **admin** est créé par `python -m app.seed` avec `ADMIN_EMAIL` et `ADMIN_PASSWORD` du `.env`.

Créez ensuite les deux autres rôles avec l'admin (Swagger : bouton *Authorize*, puis
`POST /api/v1/utilisateurs`) :

| Rôle | E-mail suggéré | Mot de passe |
|------|----------------|--------------|
| accueil | accueil@atelier.sn | à choisir (8 caractères minimum) |
| tailleur | tailleur@atelier.sn | à choisir (8 caractères minimum) |

Connexion : `POST /api/v1/auth/login` (champ `username` = e-mail). Dans Swagger, laissez
`client_id` et `client_secret` vides.

## Droits par rôle

| Rôle | Droits |
|------|--------|
| admin | tout faire (comptes, catalogue, suppression de clients, statistiques) |
| accueil | clients, commandes, paiements, livraisons |
| tailleur | mesures, avancement de la production |

Tout utilisateur connecté peut consulter. Sans jeton valide : 401. Rôle insuffisant : 403.

## Routes réalisées

Toutes les routes sont préfixées par `/api/v1`, sauf `/health`.

| N° | Méthode et chemin | Rôle | État |
|----|-------------------|------|------|
| 1 | POST /auth/login | public | fait |
| 2 | GET /auth/me | connecté | fait |
| 3 | POST /utilisateurs | admin | fait |
| 4 | GET /utilisateurs | admin | fait |
| 5 | GET /utilisateurs/{id} | admin | fait |
| 6 | PATCH /utilisateurs/{id} | admin | fait |
| 7 | POST /clients | tous | fait |
| 8 | GET /clients | tous | fait |
| 9 | GET /clients/{id} | tous | fait |
| 10 | PATCH /clients/{id} | tous | fait |
| 11 | DELETE /clients/{id} | admin | fait |
| 12-13 | GET /clients/{id}/commandes, /resume | tous | fait |
| 14 | POST /catalogue | admin | fait |
| 15 | GET /catalogue | tous | fait |
| 16 | GET /catalogue/{id} | tous | fait |
| 17 | PATCH /catalogue/{id} | admin | fait |
| 18-23 | Mesures | tailleur / tous | fait |
| 24-31 | Commandes | accueil / tous | fait |
| 32-34 | Paiements | accueil / admin | fait |
| 35-38 | Livraisons | accueil / tous | fait |
| 39-43 | Statistiques | admin | fait |
| 44 | GET /health | public | fait |

## Conventions

- Erreurs : `{"detail": "message en français"}`.
- Listes paginées : `{"items": [...], "total": n, "limit": n, "offset": n}` (limit 20 par défaut, 100 au maximum).
- Les montants sont des entiers en FCFA, les mesures des nombres en centimètres.
- Authentification : jetons JWT signés avec expiration ; un compte désactivé est refusé immédiatement.
