# 📦 Análisis de Dependencias - Diaken Project

## 📋 Dependencias Actuales

```txt
asgiref==3.9.2
certifi==2025.10.5
cffi==2.0.0
charset-normalizer==3.4.3
cryptography==46.0.2
Django==5.2.6
idna==3.10
pycparser==2.23
pyspnego==0.12.0
pytz==2025.2
pyvmomi==9.0.0.0
pywinrm==0.5.0
PyYAML==6.0.3
requests==2.32.5
requests-credssp==2.0.0
requests_ntlm==1.3.0
sqlparse==0.5.3
urllib3==2.5.0
xmltodict==1.0.2
```

## ✅ Estado de Seguridad

### Dependencias Seguras (Actualizadas)
- ✅ **Django 5.2.6** - Versión reciente (liberada 2024)
- ✅ **cryptography 46.0.2** - Última versión estable
- ✅ **requests 2.32.5** - Actualizada y segura
- ✅ **urllib3 2.5.0** - Versión reciente
- ✅ **PyYAML 6.0.3** - Safe loader por defecto
- ✅ **pyvmomi 9.0.0.0** - Última versión vSphere SDK

### ⚠️ Atención Requerida
- ⚠️ **pywinrm 0.5.0** - Última versión de 2023, funcional pero podría actualizarse
- ⚠️ **pytz 2025.2** - Considerar migrar a `zoneinfo` (built-in Python 3.9+)

## 🔧 Dependencias Faltantes Recomendadas

### Seguridad
```txt
django-ratelimit==4.1.0        # Rate limiting para prevenir brute force
django-otp==1.3.0              # Two-factor authentication
qrcode==7.4.2                  # QR codes para 2FA
django-csp==3.8                # Content Security Policy
```

### Base de Datos
```txt
psycopg2-binary==2.9.9         # PostgreSQL adapter (recomendado para producción)
```

### Servidor de Producción
```txt
gunicorn==21.2.0               # WSGI HTTP Server
whitenoise==6.6.0              # Servir archivos estáticos eficientemente
```

### Caché y Performance
```txt
django-redis==5.4.0            # Redis cache backend
redis==5.0.1                   # Redis client
hiredis==2.3.2                 # Redis parser (performance boost)
```

### Monitoreo y Logging
```txt
sentry-sdk==1.40.0             # Error tracking y monitoring
python-json-logger==2.0.7      # Structured logging
```

### Testing
```txt
pytest==7.4.3                  # Testing framework
pytest-django==4.7.0           # Django plugin para pytest
pytest-cov==4.1.0              # Coverage reporting
factory-boy==3.3.0             # Test fixtures
```

### Seguridad y Auditoría
```txt
safety==3.0.1                  # Dependency vulnerability scanner
bandit==1.7.5                  # Security linter para Python
```

### Utilidades
```txt
python-dotenv==1.0.0           # Manejo de variables de entorno
celery==5.3.4                  # Task queue (para tareas asíncronas)
```

## 📝 Archivo requirements.txt Actualizado

```txt
# Core Django
Django==5.2.6
asgiref==3.9.2
sqlparse==0.5.3

# Cryptography
cryptography==46.0.2
cffi==2.0.0
pycparser==2.23

# VMware vSphere
pyvmomi==9.0.0.0

# Windows Management
pywinrm==0.5.0
pyspnego==0.12.0
requests-credssp==2.0.0
requests_ntlm==1.3.0

# HTTP Requests
requests==2.32.5
urllib3==2.5.0
certifi==2025.10.5
charset-normalizer==3.4.3
idna==3.10

# Data Processing
PyYAML==6.0.3
xmltodict==1.0.2

# Timezone
pytz==2025.2

# Security Enhancements
django-ratelimit==4.1.0
django-otp==1.3.0
qrcode==7.4.2
django-csp==3.8

# Database (Production)
psycopg2-binary==2.9.9

# WSGI Server
gunicorn==21.2.0
whitenoise==6.6.0

# Cache
django-redis==5.4.0
redis==5.0.1
hiredis==2.3.2

# Monitoring
sentry-sdk==1.40.0
python-json-logger==2.0.7

# Environment
python-dotenv==1.0.0

# Task Queue (Opcional)
# celery==5.3.4
# kombu==5.3.4

# Development/Testing
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
safety==3.0.1
bandit==1.7.5
```

## 🔄 Migración de Dependencias

### Paso 1: Crear requirements-production.txt
```bash
# Separar dependencias de desarrollo y producción
cat > requirements-production.txt << 'EOF'
Django==5.2.6
cryptography==46.0.2
pyvmomi==9.0.0.0
pywinrm==0.5.0
requests==2.32.5
PyYAML==6.0.3
django-ratelimit==4.1.0
django-otp==1.3.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
django-redis==5.4.0
redis==5.0.1
sentry-sdk==1.40.0
python-dotenv==1.0.0
EOF
```

### Paso 2: Crear requirements-dev.txt
```bash
cat > requirements-dev.txt << 'EOF'
-r requirements-production.txt
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
safety==3.0.1
bandit==1.7.5
ipython==8.18.1
django-debug-toolbar==4.2.0
EOF
```

### Paso 3: Actualizar Instalación
```bash
# Crear nuevo venv
python3.12 -m venv venv-new
source venv-new/bin/activate

# Instalar dependencias actualizadas
pip install -r requirements-production.txt

# Verificar que todo funciona
python manage.py check

# Si todo OK, reemplazar venv antiguo
deactivate
mv venv venv-old
mv venv-new venv
```

## 🔍 Auditoría de Seguridad

### Verificar Vulnerabilidades
```bash
# Instalar safety
pip install safety

# Escanear dependencias
safety check --json

# Escanear con output detallado
safety check --full-report
```

### Escanear Código con Bandit
```bash
# Instalar bandit
pip install bandit

# Escanear proyecto
bandit -r . -f json -o bandit-report.json

# Ver issues de alta severidad
bandit -r . -ll
```

## 📊 Análisis de Compatibilidad

### Python 3.12 Compatibility
Todas las dependencias listadas son compatibles con Python 3.12.

### Django 5.2 Compatibility
- ✅ Todas las dependencias soportan Django 5.2
- ⚠️ Verificar plugins third-party antes de actualizar Django en el futuro

### Sistema Operativo
- ✅ Linux (Oracle Linux 9 / RedHat 9)
- ✅ Ubuntu 22.04+
- ⚠️ **cryptography** requiere compiladores C (gcc, libffi-dev)

## 🚀 Mejoras de Performance

### 1. Hiredis para Redis
```bash
pip install hiredis
```
Proporciona 10x mejora en performance para operaciones Redis.

### 2. ujson para JSON
```bash
pip install ujson
```
Parser JSON más rápido que el estándar.

### 3. Optimizaciones Django
```python
# settings.py
CONN_MAX_AGE = 600  # Connection pooling
DEBUG = False
TEMPLATE_DEBUG = False
```

## ⚠️ Advertencias y Precauciones

### 1. pytz → zoneinfo
Django 5.x recomienda usar `zoneinfo` (built-in Python 3.9+):
```python
# settings.py
USE_TZ = True
# pytz se mantiene por compatibilidad pero considerar migración
```

### 2. SQLite → PostgreSQL
```bash
# Instalar PostgreSQL
sudo dnf install postgresql-server postgresql-contrib

# Python adapter
pip install psycopg2-binary
```

### 3. Cryptography Build Requirements
```bash
# Oracle Linux / RHEL
sudo dnf install gcc libffi-devel python3-devel openssl-devel

# Ubuntu
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
```

## 📈 Roadmap de Actualizaciones

### Inmediato (Esta semana)
1. ✅ Agregar django-ratelimit
2. ✅ Agregar python-dotenv
3. ✅ Instalar safety para auditorías

### Corto Plazo (Este mes)
4. ✅ Migrar a PostgreSQL
5. ✅ Implementar django-otp (2FA)
6. ✅ Configurar Gunicorn para producción

### Mediano Plazo (2-3 meses)
7. ✅ Implementar Redis cache
8. ✅ Agregar Sentry monitoring
9. ✅ Setup de Celery para tareas asíncronas

### Largo Plazo (6+ meses)
10. ✅ Considerar migración completa a microservicios
11. ✅ Implementar GraphQL API
12. ✅ Containerización completa con Kubernetes

## 🔗 Referencias

- [Django Packages](https://djangopackages.org/)
- [PyPI Security Advisories](https://pypi.org/security/)
- [Python Safety Database](https://github.com/pyupio/safety-db)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
