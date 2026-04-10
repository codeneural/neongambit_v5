---
name: new-feature
description: Implementa una nueva feature usando TDD. Ejecuta el ciclo completo:
             spec review → tests → implementación → browser verification.
---

# Procedimiento /new-feature

## Inputs requeridos
Cuando este workflow sea invocado, preguntar:
1. ¿Cuál es el nombre de la feature? (ej: "neural-drill", "glitch-report")
2. ¿Ya existe el archivo specs/feature-[name].md? Si no, DETENER.

## Fase 1 — Spec Review (no escribir código)
1. Leer specs/feature-[name].md completamente
2. Leer las secciones relevantes del Master Guide
3. Leer DESIGN.md para contexto visual
4. Generar Implementation Plan artifact con:
   - Lista de archivos a crear/modificar
   - Dependencias entre archivos
   - Riesgos identificados
   - Preguntas de aclaración si las hay
5. ESPERAR aprobación del usuario antes de continuar

## Fase 2 — Tests Primero (TDD)
1. Crear /backend/tests/test_[feature].py con todos los tests del spec
2. Todos los tests deben FALLAR (sin implementación aún)
3. Ejecutar: cd backend && pytest tests/test_[feature].py -v
4. Confirmar que todos fallan y mostrar output al usuario
5. Crear /frontend/lib/[module].test.ts si hay lógica de frontend a testear
6. Ejecutar: cd frontend && npx vitest run [module].test.ts
7. Confirmar fallos

## Fase 3 — Implementación Backend
1. Implementar schema Pydantic en /backend/app/schemas/
2. Implementar modelo SQLAlchemy si se necesita tabla nueva
3. Crear migración Alembic: alembic revision --autogenerate -m "add [feature]"
4. Revisar migración generada — NO ejecutar aún
5. Implementar service en /backend/app/services/
6. Implementar router en /backend/app/api/v1/
7. Registrar router en /backend/app/api/v1/__init__.py
8. Ejecutar: cd backend && pytest tests/test_[feature].py -v
9. Todos los tests deben PASAR — si no, debug hasta que pasen

## Fase 4 — Migración de Base de Datos
1. Mostrar el contenido de la migración al usuario
2. ESPERAR confirmación explícita para ejecutar
3. Si confirmado: alembic upgrade head
4. Verificar tablas creadas: describir tablas en Neon

## Fase 5 — Implementación Frontend
1. Crear Zustand store si se necesita estado nuevo
2. Crear módulo en /frontend/lib/api/ para los endpoints
3. Implementar componentes React (bottom-up: atoms → molecules → screen)
4. Usar DESIGN.md como referencia visual en cada componente
5. Ejecutar: cd frontend && npm run dev
6. Browser Agent: navegar a la pantalla e tomar screenshot
7. Comparar screenshot contra DESIGN.md — anotar diferencias

## Fase 6 — Integration Testing
1. Ejecutar test suite completo: cd backend && pytest
2. Ejecutar: cd frontend && npx vitest run
3. Verificar coverage: pytest --cov=app/services/[service] --cov-report=term-missing
4. Coverage debe ser >= 80% para el servicio nuevo

## Fase 7 — Commit y PR
1. git add [archivos específicos de esta feature]
2. git commit -m "feat: implement [feature-name]"
3. git push origin feature/[feature-name]
4. Crear PR: feature/[feature-name] → develop
5. Generar Walkthrough artifact con: qué se implementó, cómo probarlo
