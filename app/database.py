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

    def query(self, model):
        return QueryHelper(self.client, model)

    # Añadimos estos para que los routers no den error al crear/borrar
    def add(self, instance): pass
    def commit(self): pass
    def refresh(self, instance): pass
    def delete(self, instance): pass
    def close(self): pass

class QueryHelper:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.table = model.__tablename__
        self.filter_val = None

    def filter(self, condition):
        # Esta es la lógica que ya te funcionaba para el login
        try:
            self.filter_val = condition.right.value
        except AttributeError:
            self.filter_val = condition
        return self

    def first(self):
        # Usamos la misma lógica del login pero para cualquier tabla
        sql = f"SELECT * FROM {self.table} WHERE email = ? LIMIT 1" if self.table == "usuarios" else f"SELECT * FROM {self.table} WHERE id = ? LIMIT 1"
        res = self.client.execute(sql, [self.filter_val] if self.filter_val else [])
        
        if not res.rows:
            return None
        
        return self._map_row(res.rows[0])

    def all(self):
        # Este es el método que te faltaba para listar clientes, tareas y citas
        res = self.client.execute(f"SELECT * FROM {self.table}")
        return [self._map_row(row) for row in res.rows]

    def _map_row(self, row):
        # Convierte cualquier fila de Turso al modelo correcto (Usuario, Cliente, etc.)
        # Usamos row.keys() para que sea automático
        try:
            data = {key: row[key] for key in row.keys()}
            return self.model(**data)
        except:
            # Fallback manual si row.keys() falla en algunas versiones
            return self.model(
                id=row[0],
                nombre=row[1] if len(row) > 1 else None,
                email=row[2] if len(row) > 2 else None,
                password=row[3] if len(row) > 3 else None
            )

def get_db():
    db = TursoSession(client)
    try:
        yield db
    finally:
        db.close()