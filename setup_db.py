import getpass, os
from dotenv import load_dotenv
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

load_dotenv()
u = make_url(os.environ["DATABASE_URL"])
mdp = getpass.getpass("Mot de passe de postgres : ")
with psycopg.connect(host=u.host or "localhost", port=u.port or 5432, user="postgres", password=mdp, dbname="postgres", autocommit=True) as c:
    if c.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (u.username,)).fetchone():
        c.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(sql.Identifier(u.username), sql.Literal(u.password)))
        print("Utilisateur existant : mot de passe aligne sur le .env")
    else:
        c.execute(sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(sql.Identifier(u.username), sql.Literal(u.password)))
        print("Utilisateur cree")
    if not c.execute("SELECT 1 FROM pg_database WHERE datname=%s", (u.database,)).fetchone():
        c.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(u.database), sql.Identifier(u.username)))
        print("Base creee")
    else:
        c.execute(sql.SQL("ALTER DATABASE {} OWNER TO {}").format(sql.Identifier(u.database), sql.Identifier(u.username)))
        print("Base existante")
