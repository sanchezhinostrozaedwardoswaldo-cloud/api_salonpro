import os
from dotenv import load_dotenv
import libsql_client
from sqlalchemy.orm import declarative_base
from sqlalchemy import inspect, text
from sqlalchemy.sql import operators
import datetime

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
        self._pending = []  # instancias a insertar
        self._dirty = []    # instancias a actualizar
        self._deleted = []  # instancias a borrar

    def query(self, model):
        return QueryHelper(self.client, model)

    def add(self, instance):
        self._pending.append(instance)

    def commit(self):
        # Ejecuta inserts
        for instance in self._pending:
            self._do_insert(instance)
        self._pending.clear()

        # Ejecuta updates
        for instance in self._dirty:
            self._do_update(instance)
        self._dirty.clear()

        # Ejecuta deletes
        for instance in self._deleted:
            self._do_delete(instance)
        self._deleted.clear()

    def refresh(self, instance):
        table = instance.__tablename__
        pk = _get_primary_key(instance)
        sql = f"SELECT * FROM {table} WHERE id = ? LIMIT 1"
        res = self.client.execute(sql, [pk])
        if not res.rows:
            return
        row = res.rows[0]
        mapped = _map_row_to_model(type(instance), row)
        # Copiar atributos al instance existente
        for col in inspect(type(instance)).mapper.column_attrs:
            setattr(instance, col.key, getattr(mapped, col.key, None))

    def delete(self, instance):
        self._deleted.append(instance)

    def close(self):
        pass

    def _do_insert(self, instance):
        table = instance.__tablename__
        mapper = inspect(type(instance))
        cols = []
        vals = []
        for col in mapper.mapper.column_attrs:
            if col.key == 'id':
                continue  # asumimos autoincrement
            val = getattr(instance, col.key, None)
            if val is not None:
                cols.append(col.key)
                vals.append(val)
        placeholders = ','.join('?' for _ in vals)
        col_names = ','.join(cols)
        sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) RETURNING *"
        res = self.client.execute(sql, vals)
        if res.rows:
            mapped = _map_row_to_model(type(instance), res.rows[0])
            for col in mapper.mapper.column_attrs:
                setattr(instance, col.key, getattr(mapped, col.key, None))

    def _do_update(self, instance):
        table = instance.__tablename__
        mapper = inspect(type(instance))
        pk = _get_primary_key(instance)
        sets = []
        vals = []
        for col in mapper.mapper.column_attrs:
            if col.key == 'id':
                continue
            val = getattr(instance, col.key, None)
            # Manejar expresiones SQLAlchemy como func.datetime(...)
            if hasattr(val, 'compile'):
                compiled = str(val.compile(compile_kwargs={"literal_binds": True}))
                sets.append(f"{col.key} = {compiled}")
            else:
                sets.append(f"{col.key} = ?")
                vals.append(val)
        if not sets:
            return
        vals.append(pk)
        sql = f"UPDATE {table} SET {', '.join(sets)} WHERE id = ? RETURNING *"
        res = self.client.execute(sql, vals)
        if res.rows:
            mapped = _map_row_to_model(type(instance), res.rows[0])
            for col in mapper.mapper.column_attrs:
                setattr(instance, col.key, getattr(mapped, col.key, None))

    def _do_delete(self, instance):
        table = instance.__tablename__
        pk = _get_primary_key(instance)
        sql = f"DELETE FROM {table} WHERE id = ?"
        self.client.execute(sql, [pk])


def _get_primary_key(instance):
    mapper = inspect(type(instance))
    pk_cols = mapper.mapper.primary_key
    if pk_cols:
        return getattr(instance, pk_cols[0].name, None)
    return getattr(instance, 'id', None)


def _map_row_to_model(model, row):
    """Mapea una fila de Turso a un modelo SQLAlchemy usando introspección."""
    mapper = inspect(model).mapper
    data = {}
    col_names = [col.name for col in mapper.columns]
    for i, name in enumerate(col_names):
        if i < len(row):
            data[name] = row[i]
    return model(**data)


class QueryHelper:
    def __init__(self, client, model):
        self.client = client
        self.model = model
        self.table = model.__tablename__
        self._filters = []
        self._filter_val = None

    def filter(self, condition):
        self._filters.append(condition)
        # Mantener compatibilidad con el login original
        try:
            self._filter_val = condition.right.value
        except AttributeError:
            self._filter_val = condition
        return self

    def first(self):
        sql, params = self._build_sql(limit=1)
        res = self.client.execute(sql, params)
        if not res.rows:
            return None
        return _map_row_to_model(self.model, res.rows[0])

    def all(self):
        sql, params = self._build_sql()
        res = self.client.execute(sql, params)
        return [_map_row_to_model(self.model, row) for row in res.rows]

    def _build_sql(self, limit=None):
        params = []
        where_clauses = []

        for condition in self._filters:
            clause, vals = self._compile_condition(condition)
            if clause:
                where_clauses.append(clause)
                params.extend(vals)

        sql = f"SELECT * FROM {self.table}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(f"({c})" for c in where_clauses)
        if limit:
            sql += f" LIMIT {limit}"

        return sql, params

    def _compile_condition(self, condition):
        """Compila condiciones SQLAlchemy a SQL string y parámetros."""
        # Caso simple: BinaryExpression (Column == value)
        if hasattr(condition, 'left') and hasattr(condition, 'right') and hasattr(condition, 'operator'):
            left = condition.left
            right = condition.right
            op = condition.operator

            # Obtener nombre de columna
            col_name = None
            if hasattr(left, 'name'):
                col_name = left.name
            elif hasattr(left, 'key'):
                col_name = left.key

            # Obtener valor
            val = None
            if hasattr(right, 'value'):
                val = right.value
            elif hasattr(right, 'compile'):
                val = str(right.compile(compile_kwargs={"literal_binds": True}))
            else:
                val = right

            if not col_name:
                return None, []

            # Operadores
            if op == operators.eq:
                return f"{col_name} = ?", [val]
            elif op == operators.ne:
                return f"{col_name} != ?", [val]
            elif op == operators.lt:
                return f"{col_name} < ?", [val]
            elif op == operators.gt:
                return f"{col_name} > ?", [val]
            elif op == operators.le:
                return f"{col_name} <= ?", [val]
            elif op == operators.ge:
                return f"{col_name} >= ?", [val]
            elif op == operators.like_op or op == operators.ilike_op:
                return f"{col_name} LIKE ?", [val]
            elif op == operators.contains:
                return f"{col_name} LIKE ?", [f"%{val}%"]

        # Caso OR: sqlalchemy.or_
        if hasattr(condition, 'clauses'):
            or_parts = []
            or_vals = []
            for clause in condition.clauses:
                part, vals = self._compile_condition(clause)
                if part:
                    or_parts.append(part)
                    or_vals.extend(vals)
            if or_parts:
                return " OR ".join(f"({p})" for p in or_parts), or_vals

        # Fallback: si es un string o valor simple, asumir WHERE id = ?
        if self._filter_val is not None:
            return "id = ?", [self._filter_val]

        return None, []


def get_db():
    db = TursoSession(client)
    try:
        yield db
    finally:
        db.close()