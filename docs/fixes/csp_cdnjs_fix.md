# Fix: Content-Security-Policy para cdnjs.cloudflare.com

**Fecha:** 20 Oct 2025 11:25 AM

## Problema

Font Awesome desde `cdnjs.cloudflare.com` estaba bloqueado por CSP:

```
Content-Security-Policy: La configuración de la página bloqueó la ejecución de un script (script-src-elem) 
en https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js 
porque viola la siguiente directiva: "script-src 'self' 'unsafe-inline' 'unsafe-eval' 
https://cdn.jsdelivr.net https://code.jquery.com"
```

## Causa

El CSP en `/etc/httpd/conf.d/diaken-ssl.conf` permitía `cdnjs.cloudflare.com` para:
- ✅ `style-src` (CSS)
- ✅ `font-src` (fuentes)
- ❌ `script-src` (JavaScript) - **FALTABA**

## Solución

Agregar `https://cdnjs.cloudflare.com` a `script-src`:

### Antes:
```apache
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com
```

### Después:
```apache
script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com
```

## Comando Aplicado

```bash
sudo sed -i 's|script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\'' https://cdn.jsdelivr.net https://code.jquery.com|script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\'' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com|g' /etc/httpd/conf.d/diaken-ssl.conf

sudo systemctl restart httpd
```

## Verificación

```bash
# Ver CSP actual
grep "Content-Security-Policy" /etc/httpd/conf.d/diaken-ssl.conf

# Probar en navegador
# Abrir: https://diaken-pdn.upb.edu.co/deploy/test-sse/
# Verificar consola (F12) - No debe haber errores de CSP
```

## CSP Completo Actual

```apache
Content-Security-Policy: 
  default-src 'self'; 
  script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; 
  style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; 
  img-src 'self' data: https:; 
  font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com; 
  connect-src 'self'; 
  frame-ancestors 'self';
```

## Dominios Permitidos

### script-src (JavaScript):
- ✅ `'self'` - Scripts del mismo origen
- ✅ `'unsafe-inline'` - Scripts inline
- ✅ `'unsafe-eval'` - eval() y similares
- ✅ `https://cdn.jsdelivr.net` - jsDelivr CDN
- ✅ `https://code.jquery.com` - jQuery CDN
- ✅ `https://cdnjs.cloudflare.com` - Cloudflare CDN (Font Awesome)

### style-src (CSS):
- ✅ `'self'`
- ✅ `'unsafe-inline'`
- ✅ `https://cdn.jsdelivr.net`
- ✅ `https://cdnjs.cloudflare.com`
- ✅ `https://fonts.googleapis.com`

### font-src (Fuentes):
- ✅ `'self'`
- ✅ `https://cdn.jsdelivr.net`
- ✅ `https://cdnjs.cloudflare.com`
- ✅ `https://fonts.gstatic.com`

## Impacto

✅ Font Awesome ahora carga correctamente desde cdnjs.cloudflare.com
✅ Iconos visibles en toda la aplicación
✅ Sin errores de CSP en consola
✅ Seguridad mantenida (solo dominios confiables)

## Estado

✅ RESUELTO - Apache reiniciado, CSP actualizado
