---
name: deploy-backend
description: Despliega el backend a Hostinger VPS via PM2 y verifica que esté funcionando.
---

# Procedimiento /deploy-backend

## Pre-deploy checklist (DEBE pasar todo)
1. pytest — todos los tests pasan
2. mypy app/ — sin errores de tipo
3. ruff check app/ — sin errores de lint
4. git status — sin cambios sin commitear
5. Confirmar que .env está actualizado en el VPS

## Deploy
1. SSH al VPS: ssh user@hostinger-ip
2. cd /var/www/neongambit/backend
3. git pull origin main
4. pip install -r requirements.txt --break-system-packages
5. alembic upgrade head (mostrar migración y esperar confirmación)
6. pm2 restart neongambit-api
7. Verificar logs: pm2 logs neongambit-api --lines 20

## Post-deploy verification
1. GET https://api.neongambit.com/health → debe retornar {"status": "ok", "version": "5.1.0"}
2. POST https://api.neongambit.com/v1/auth/guest → debe retornar token
3. Verificar Swagger: https://api.neongambit.com/docs → debe cargar
4. Verificar nginx: systemctl status nginx

## Rollback (si algo falla)
1. git log --oneline -5 → identificar commit anterior
2. git checkout [commit-hash]
3. pm2 restart neongambit-api
4. Verificar /health
