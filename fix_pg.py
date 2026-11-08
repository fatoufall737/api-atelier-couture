import psycopg
c = psycopg.connect(host="localhost", user="postgres", dbname="postgres", autocommit=True)
if c.execute("SELECT 1 FROM pg_roles WHERE rolname='atelier'").fetchone():
    c.execute("ALTER ROLE atelier WITH LOGIN PASSWORD '12345'")
    print("Utilisateur atelier : mot de passe change en 12345")
else:
    c.execute("CREATE ROLE atelier WITH LOGIN PASSWORD '12345'")
    print("Utilisateur atelier cree avec le mot de passe 12345")
if not c.execute("SELECT 1 FROM pg_database WHERE datname='atelier'").fetchone():
    c.execute("CREATE DATABASE atelier OWNER atelier")
    print("Base atelier creee")
else:
    c.execute("ALTER DATABASE atelier OWNER TO atelier")
    print("Base atelier existante")
