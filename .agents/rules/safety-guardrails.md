# Safety Guardrails

## NUNCA hacer esto sin confirmación explícita del usuario

### Base de Datos
- NUNCA ejecutar alembic upgrade head sin mostrar el contenido de la migración primero
- NUNCA hacer DROP TABLE o DELETE en producción
- NUNCA modificar migraciones ya ejecutadas
- NUNCA acceder a DATABASE_URL de producción desde el entorno local

### Secrets y Credenciales
- NUNCA hardcodear API keys, tokens, o passwords en código
- NUNCA commitear archivos .env
- NUNCA loggear JWT tokens o Firebase credentials
- NUNCA exponer STRIPE_SECRET_KEY en logs o responses

### Git y Deployment
- NUNCA hacer push directamente a main
- NUNCA hacer force push en branches públicos
- NUNCA hacer deploy sin que los tests estén pasando

### Infraestructura
- NUNCA modificar configuración de PM2 o nginx en el VPS sin documentarlo
- NUNCA cambiar configuración de CORS para permitir * en producción
- NUNCA deshabilitar rate limiting
- NUNCA ejecutar Stockfish server-side durante sesiones de sparring (solo para Glitch Report)
- NUNCA llamar Gemini/LLM durante gameplay en tiempo real (solo templates)

## En caso de duda
Parar, mostrar el plan al usuario, y esperar confirmación explícita.
Mejor preguntar y perder 5 minutos que romper producción.
