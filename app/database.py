import os
from dotenv import load_dotenv
import libsql_client
from sqlalchemy.orm import declarative_base

load_dotenv()

URL = os.getenv("TURSO_DATABASE_URL")
TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if URL.startswith("libsql://"):
    URL = URL.replace("libsql://", "https://")

# Cliente nativo de Turso
client = libsql_client.create_client_sync(url=URL, auth_token=TOKEN)

Base = declarative_base()

# Creamos un objeto engine vacío para que main.py no de error al importar
engine = None 

class TursoSession:
    def __init__(self, client):
        self.client = client

    def query(self, model):
        class QueryHelper:
            def __init__(self, client, model):
                self.client = client
                self.model = model
            
            def filter(self, condition):
                # Extraemos el valor del filtro de forma segura
                try:
                    email = condition.right.value
                except AttributeError:
                    email = condition # Fallback por si la condición llega distinta
                
                res = self.client.execute("SELECT * FROM usuarios WHERE email = ?", [email])
                self.result = res.rows[0] if res.rows else None
                return self

            def first(self):
                if not hasattr(self, 'result') or not self.result:
                    return None
                
                row = self.result
                
                # Intentamos convertir a diccionario usando una forma más compatible
                try:
                    # Algunos objetos Row permiten dict(row)
                    row_dict = dict(row)
                except (TypeError, ValueError):
                    # Si lo anterior falla, accedemos por nombre directamente
                    # basándonos en tu modelo de Usuario
                    row_dict = {
                        "id": row[0], # O row["id"] si el driver lo permite por nombre
                        "nombre": row[1],
                        "email": row[2],
                        "password": row[3],
                        "rol": row[4] if len(row) > 4 else "empleado",
                        "activo": row[5] if len(row) > 5 else 1
                    }

                # Si row["id"] funciona pero row.keys() no, esta es la mejor forma:
                return self.model(
                    id=row["id"],
                    nombre=row["nombre"],
                    email=row["email"],
                    password=row["password"],
                    rol=row["rol"] if "rol" in row else "empleado",
                    activo=row["activo"] if "activo" in row else 1
                )
        return QueryHelper(self.client, model)

    def close(self):
        pass

def get_db():
    db = TursoSession(client)
    try:
        yield db
    finally:
        db.close()