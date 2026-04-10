---
name: deploy-frontend
description: Verifica el estado del deploy en Vercel (auto-deploy desde GitHub).
---

# Procedimiento /deploy-frontend

## Nota: Vercel hace auto-deploy desde GitHub
El deploy ocurre automáticamente cuando hay un push a main.
Este workflow verifica que el deploy fue exitoso.

## Verificación post-deploy
1. Abrir Browser Agent en: https://neongambit.com
2. Verificar: página carga sin errores de consola
3. Verificar: POST /auth/guest funciona (guest session se crea)
4. Verificar: PWA manifest accesible en /manifest.json
5. Lighthouse audit: PWA score debe ser > 90
6. Screenshot: tomar y comparar con DESIGN.md

## Si el deploy falló
1. Verificar build logs en Vercel dashboard
2. Buscar errores TypeScript o de módulos
3. Correr localmente: npm run build — debe pasar
