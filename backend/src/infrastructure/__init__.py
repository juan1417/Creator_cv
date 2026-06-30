"""Infrastructure layer: adapters a frameworks externos (Flask, SQLAlchemy, JWT).

Aquí vive TODO lo que depende de una tecnología específica:
- SQLAlchemyCVRepository / SQLAlchemyChatRepository: persistencia en Postgres/SQLite.
- Flask: expone los use cases como endpoints HTTP.
- local_auth: hashing de contraseñas (werkzeug) y JWT (PyJWT).
"""
