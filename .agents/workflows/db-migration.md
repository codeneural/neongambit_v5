---
name: migrate
description: Crea y aplica migraciones de base de datos de forma segura.
             SIEMPRE requiere revisión humana antes de ejecutar.
---

# Procedimiento /migrate

## Regla de Seguridad
NUNCA ejecutar alembic upgrade head sin confirmación explícita del usuario.
NUNCA modificar migraciones ya ejecutadas en producción.

## Pasos
1. Verificar estado actual: alembic current
2. Generar migración: alembic revision --autogenerate -m "[descripción]"
3. Abrir el archivo generado y mostrar su contenido completo al usuario
4. ESPERAR respuesta explícita "sí, aplicar" o "no, revisar"
5. Si aprobado: alembic upgrade head
6. Verificar: alembic current (debe mostrar nueva revisión)
7. Commit: "chore: add migration [descripción]"

## Verificaciones post-migración
- Tabla existe: SELECT tablename FROM pg_tables WHERE schemaname='public'
- Columnas correctas: \d [tablename] en psql
- Índices creados: \di en psql
