---
name: test
description: Ejecuta el test suite completo y reporta coverage.
---

# Procedimiento /test

## Backend
1. cd backend
2. pytest --cov=app --cov-report=term-missing -v
3. Mostrar: tests passed, tests failed, coverage %
4. Si coverage < 80% en algún servicio: identificar líneas sin cobertura
5. Si hay tests fallando: mostrar el traceback completo

## Frontend
1. cd frontend
2. npx vitest run --coverage
3. Mostrar: tests passed, tests failed, coverage %

## Reporte
Generar artifact con:
- Total: X passed / Y failed
- Coverage por módulo
- Archivos sin tests (si los hay)
- Próximos tests recomendados
