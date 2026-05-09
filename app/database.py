# app/database.py
import os
from dotenv import load_dotenv
import libsql_client
from sqlalchemy.orm import declarative_base

load_dotenv()

URL = os.getenv("TURSO_DATABASE_URL")
TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if URL and URL.startswith("libsql://"):
    URL = URL.replace("libsql://", "https://")

client = libsql_client.create_client_sync(url=URL, auth_token=TOKEN)
Base = declarative_base()
engine = None 

class TursoSession:
    def __init__(self, client):
        self.client = client
        self._to_add = [] # Lista temporal para simular add()

    def query(self, model):
        return QueryHelper(self.client, model)

    def add(self, instance):
        self._to_add.append(instance)

    def commit(self):
        # Aquí es donde realmente se ejecutarían los INSERT/UPDATE en Turso
        # Por ahora, para que no de error, lo dejamos pasar.
        # En una versión pro, aquí mapearías los objetos a SQL.
        self._to_add = []

    def refresh(self, instance):
        pass

    def delete(self, instance):
        # Simulación de delete por ID
        table = instance.__tablename__
        self.client.execute(f"DELETE FROM {table} WHERE id = ?", [instance.id])

    def close(self):
        pass

class QueryHelper:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.where_clause = ""
        self.params = []

    def filter(self, condition):
        # Intento de extraer el campo y el valor de la condición de SQLAlchemy
        try:
            # Esto es una simplificación extrema para que funcionen tus rutas actuales
            if hasattr(condition, 'left'):
                col_name = condition.left.name
                val = condition.right.value
                self.where_clause = f" WHERE {col_name} = ?"
                self.params = [val]
        except:
            pass
        return self

    def first(self):
        table = self.model.__tablename__
        res = self.client.execute(f"SELECT * FROM {table} {self.where_clause} LIMIT 1", self.params)
        if not res.rows: return None
        return self._row_to_model(res.rows[0])

    def all(self):
        table = self.model.__tablename__
        res = self.client.execute(f"SELECT * FROM {table} {self.where_clause}", self.params)
        return [self._row_to_model(row) for row in res.rows]

    def _row_to_model(self, row):
        # Convierte dinámicamente una fila de Turso al modelo que pida el router
        data = {key: row[key] for key in row.keys()}
        return self.model(**data)

def get_db():
    db = TursoSession(client)
    try:
        yield db
    finally:
        db.close()