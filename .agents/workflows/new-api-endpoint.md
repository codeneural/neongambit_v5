---
name: new-endpoint
description: Agrega un nuevo endpoint API con schema, implementación y tests.
             Para endpoints simples que no requieren nuevo servicio.
---

# Procedimiento /new-endpoint

## Inputs: pedir al usuario
- Método HTTP y path (ej: "GET /drill/queue/count")
- Request body schema (si aplica)
- Response schema exacto
- Autenticación requerida (yes/no/pro-only)
- Rate limiting (yes/no)

## Pasos
1. Crear test de integración PRIMERO en tests/test_[router].py
   - Test: request sin auth → 401
   - Test: request válido → schema correcto
   - Test: request inválido → error correcto
2. Ejecutar tests → deben fallar
3. Agregar schema Pydantic en /backend/app/schemas/
4. Implementar función en router existente o crear nuevo router
5. Ejecutar tests → deben pasar
6. Verificar en Swagger: http://localhost:8000/docs
7. Commit: "feat: add [METHOD] [path] endpoint"
