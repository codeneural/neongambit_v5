---
name: code-review
description: Analiza el diff del branch actual contra develop.
             Usa Claude Opus 4.6 para máxima calidad de review.
---

# Procedimiento /code-review

## Usar modelo: Claude Opus 4.6

## Análisis del diff
1. git diff develop...[current-branch] — mostrar todos los cambios
2. Analizar cada archivo modificado:

### Checklist de seguridad
- [ ] No hay secretos hardcodeados
- [ ] Autenticación correcta en todos los endpoints nuevos
- [ ] SQL injection imposible (SQLAlchemy siempre, no strings raw)
- [ ] Input validation en todos los schemas

### Checklist de arquitectura
- [ ] Lógica de negocio está en services, no en routers
- [ ] Frontend no hace validación chess como fuente de verdad
- [ ] Stores Zustand son flat (sin nesting profundo)
- [ ] No hay imports circulares

### Checklist de tests
- [ ] Tests cubren happy path Y error cases
- [ ] No hay tests que dependan de orden de ejecución
- [ ] Fixtures no usan datos de producción

### Checklist de performance
- [ ] Queries tienen índices en columnas usadas en WHERE
- [ ] No hay N+1 queries (eager loading donde corresponde)
- [ ] Cache usada para Lichess Explorer calls
- [ ] Stockfish NEVER called server-side during sparring (client WASM only)
- [ ] Gemini/LLM NEVER called during sparring gameplay (templates only)
- [ ] All user-facing strings use next-intl translation keys

## Output
Generar artifact de review con:
- Issues críticos (deben corregirse antes del merge)
- Issues menores (mejoras recomendadas)
- Puntos positivos del código
