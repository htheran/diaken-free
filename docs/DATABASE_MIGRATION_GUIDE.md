# Guía de Migración de Base de Datos MariaDB

## 📋 Objetivo
Migrar la base de datos de MariaDB local a un servidor MariaDB dedicado.

---

## 🎯 Información Requerida

Antes de comenzar, necesitas:
- **IP del servidor MariaDB nuevo**: `_______________`
- **Puerto MariaDB**: `3306` (por defecto)
- **Nombre de la base de datos**: `diaken_pdn`
- **Usuario de la base de datos**: `diaken_user`
- **Contraseña del usuario**: `_______________` (generar una segura)

---

## 📝 PASO 1: Preparar el Servidor MariaDB Remoto

### 1.1 Conectarse al servidor MariaDB nuevo

```bash
ssh root@IP_SERVIDOR_MARIADB
```

### 1.2 Crear la base de datos y usuario

```bash
# Conectar a MariaDB como root
mysql -u root -p

# Ejecutar estos comandos SQL:
CREATE DATABASE IF NOT EXISTS diaken_pdn CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'diaken_user'@'%' IDENTIFIED BY 'PASSWORD_SEGURO_AQUI';

GRANT ALL PRIVILEGES ON diaken_pdn.* TO 'diaken_user'@'%';

FLUSH PRIVILEGES;

-- Verificar
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User='diaken_user';

EXIT;
```

### 1.3 Configurar MariaDB para aceptar conexiones remotas

```bash
# Editar configuración
sudo vi /etc/my.cnf.d/mariadb-server.cnf

# Buscar y modificar/agregar:
[mysqld]
bind-address = 0.0.0.0

# Guardar y salir (:wq)

# Reiniciar MariaDB
sudo systemctl restart mariadb
sudo systemctl status mariadb
```

### 1.4 Configurar Firewall

```bash
# Abrir puerto 3306
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-ports
```

### 1.5 Probar conectividad desde el servidor de aplicación

```bash
# Desde el servidor de producción (diaken-pdn)
mysql -h IP_SERVIDOR_MARIADB -u diaken_user -p diaken_pdn

# Si conecta correctamente, escribir:
SHOW TABLES;
EXIT;
```

---

## 📝 PASO 2: Exportar Base de Datos Actual

### 2.1 Identificar configuración actual

**En el servidor de producción (diaken-pdn)**:

```bash
cd /opt/www/app/diaken-pdn

# Ver variables de entorno actuales
cat .env | grep DB_

# O si no existe .env, ver desde settings
source venv/bin/activate
python manage.py shell << 'EOF'
from django.conf import settings
db = settings.DATABASES['default']
print(f"Engine: {db['ENGINE']}")
print(f"Name: {db['NAME']}")
print(f"User: {db['USER']}")
print(f"Host: {db['HOST']}")
print(f"Port: {db['PORT']}")
EOF
```

### 2.2 Hacer backup de la base de datos actual

```bash
# Si usa MariaDB local
mysqldump -u root -p diaken_pdn > /tmp/diaken_pdn_backup_$(date +%Y%m%d_%H%M%S).sql

# Si usa SQLite (menos probable)
cp /opt/www/app/diaken-pdn/db.sqlite3 /tmp/db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# Verificar el backup
ls -lh /tmp/diaken_pdn_backup*
```

### 2.3 Comprimir el backup (opcional, para transferencia más rápida)

```bash
gzip /tmp/diaken_pdn_backup_*.sql
```

---

## 📝 PASO 3: Importar Datos al Servidor MariaDB Remoto

### 3.1 Transferir el backup al servidor MariaDB

```bash
# Desde el servidor de producción
scp /tmp/diaken_pdn_backup_*.sql.gz root@IP_SERVIDOR_MARIADB:/tmp/

# O sin comprimir
scp /tmp/diaken_pdn_backup_*.sql root@IP_SERVIDOR_MARIADB:/tmp/
```

### 3.2 Importar los datos

**En el servidor MariaDB**:

```bash
# Si está comprimido
gunzip /tmp/diaken_pdn_backup_*.sql.gz

# Importar
mysql -u root -p diaken_pdn < /tmp/diaken_pdn_backup_*.sql

# Verificar
mysql -u root -p diaken_pdn -e "SHOW TABLES;"
mysql -u root -p diaken_pdn -e "SELECT COUNT(*) FROM auth_user;"
```

---

## 📝 PASO 4: Configurar la Aplicación para Usar la Nueva Base de Datos

### 4.1 Detener servicios

**En el servidor de producción (diaken-pdn)**:

```bash
sudo systemctl stop httpd
sudo systemctl stop celery-diaken
```

### 4.2 Actualizar archivo .env

```bash
cd /opt/www/app/diaken-pdn

# Hacer backup del .env actual
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)

# Editar .env
sudo vi .env
```

**Agregar/modificar estas líneas**:

```bash
# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=diaken_pdn
DB_USER=diaken_user
DB_PASSWORD=PASSWORD_SEGURO_AQUI
DB_HOST=IP_SERVIDOR_MARIADB
DB_PORT=3306
# DB_SOCKET=  # Dejar vacío para conexión TCP/IP
```

### 4.3 Instalar cliente MySQL si no está instalado

```bash
# Verificar si está instalado
python -c "import MySQLdb" 2>/dev/null && echo "✅ MySQLdb instalado" || echo "❌ MySQLdb NO instalado"

# Si no está instalado:
cd /opt/www/app/diaken-pdn
source venv/bin/activate
pip install mysqlclient
```

### 4.4 Probar conexión desde Django

```bash
cd /opt/www/app/diaken-pdn
source venv/bin/activate

python manage.py shell << 'EOF'
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa a MariaDB: {version[0]}")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
EOF
```

---

## 📝 PASO 5: Ejecutar Migraciones (si es necesario)

```bash
cd /opt/www/app/diaken-pdn
source venv/bin/activate

# Ver estado de migraciones
python manage.py showmigrations

# Aplicar migraciones pendientes (si las hay)
python manage.py migrate

# Crear superusuario si es necesario
# python manage.py createsuperuser
```

---

## 📝 PASO 6: Verificar Integridad de Datos

```bash
cd /opt/www/app/diaken-pdn
source venv/bin/activate

python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from inventory.models import Host, Group, Environment
from playbooks.models import Playbook

print(f"Usuarios: {User.objects.count()}")
print(f"Hosts: {Host.objects.count()}")
print(f"Grupos: {Group.objects.count()}")
print(f"Ambientes: {Environment.objects.count()}")
print(f"Playbooks: {Playbook.objects.count()}")
EOF
```

---

## 📝 PASO 7: Reiniciar Servicios

```bash
# Reiniciar Apache
sudo systemctl start httpd
sudo systemctl status httpd

# Reiniciar Celery
sudo systemctl start celery-diaken
sudo systemctl status celery-diaken

# Verificar logs
sudo tail -f /var/log/httpd/error_log
sudo tail -f /var/log/celery/diaken-worker.log
```

---

## 📝 PASO 8: Pruebas Funcionales

### 8.1 Acceder a la aplicación web

```
http://IP_SERVIDOR_PRODUCCION/
```

### 8.2 Verificar funcionalidades:

- ✅ Login funciona
- ✅ Lista de hosts se muestra
- ✅ Lista de grupos se muestra
- ✅ Ejecución de playbooks funciona
- ✅ Historial de ejecuciones se muestra

---

## 🔄 ROLLBACK (Si algo sale mal)

### Opción 1: Volver a la base de datos local

```bash
# Detener servicios
sudo systemctl stop httpd celery-diaken

# Restaurar .env
cd /opt/www/app/diaken-pdn
cp .env.backup_TIMESTAMP .env

# Reiniciar servicios
sudo systemctl start httpd celery-diaken
```

### Opción 2: Restaurar backup en base de datos local

```bash
# Si necesitas restaurar los datos
mysql -u root -p diaken_pdn < /tmp/diaken_pdn_backup_TIMESTAMP.sql
```

---

## 📊 Checklist de Migración

```
☐ 1. Servidor MariaDB preparado
  ☐ Base de datos creada
  ☐ Usuario creado con permisos
  ☐ Configuración bind-address
  ☐ Firewall configurado
  ☐ Conectividad probada

☐ 2. Backup realizado
  ☐ Dump de base de datos actual
  ☐ Backup verificado

☐ 3. Datos importados
  ☐ Backup transferido
  ☐ Datos importados
  ☐ Tablas verificadas

☐ 4. Aplicación configurada
  ☐ Servicios detenidos
  ☐ .env actualizado
  ☐ MySQLdb instalado
  ☐ Conexión probada

☐ 5. Migraciones aplicadas
  ☐ Migraciones ejecutadas
  ☐ Sin errores

☐ 6. Datos verificados
  ☐ Conteo de registros correcto
  ☐ Datos accesibles

☐ 7. Servicios reiniciados
  ☐ Apache corriendo
  ☐ Celery corriendo
  ☐ Sin errores en logs

☐ 8. Pruebas funcionales
  ☐ Login funciona
  ☐ Hosts visibles
  ☐ Playbooks ejecutables
```

---

## ⚠️ Consideraciones Importantes

### Seguridad:
- ✅ Usar contraseñas fuertes
- ✅ Configurar firewall correctamente
- ✅ Considerar SSL/TLS para conexión a base de datos
- ✅ Restringir acceso por IP si es posible

### Performance:
- ✅ Configurar `max_connections` en MariaDB
- ✅ Ajustar `innodb_buffer_pool_size`
- ✅ Monitorear uso de recursos

### Backup:
- ✅ Configurar backups automáticos en el servidor MariaDB
- ✅ Probar restauración de backups periódicamente

### Monitoreo:
- ✅ Configurar alertas de disponibilidad
- ✅ Monitorear latencia de conexión
- ✅ Revisar logs regularmente

---

## 📞 Troubleshooting

### Error: "Can't connect to MySQL server"
```bash
# Verificar que MariaDB esté corriendo
sudo systemctl status mariadb

# Verificar firewall
sudo firewall-cmd --list-ports

# Probar conectividad
telnet IP_SERVIDOR_MARIADB 3306
```

### Error: "Access denied for user"
```bash
# Verificar permisos
mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='diaken_user';"
mysql -u root -p -e "SHOW GRANTS FOR 'diaken_user'@'%';"
```

### Error: "Too many connections"
```bash
# Aumentar max_connections en MariaDB
sudo vi /etc/my.cnf.d/mariadb-server.cnf
# Agregar:
# max_connections = 500

sudo systemctl restart mariadb
```

---

## 📝 Comandos Útiles

```bash
# Ver conexiones activas
mysql -u root -p -e "SHOW PROCESSLIST;"

# Ver tamaño de base de datos
mysql -u root -p -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)' FROM information_schema.TABLES WHERE table_schema = 'diaken_pdn';"

# Optimizar tablas
mysql -u root -p diaken_pdn -e "OPTIMIZE TABLE tabla_name;"

# Backup rápido
mysqldump -u root -p --single-transaction --quick diaken_pdn | gzip > backup.sql.gz
```

---

**Fecha de creación**: 2025-11-06
**Versión**: 1.0
**Autor**: Sistema Diaken-PDN
