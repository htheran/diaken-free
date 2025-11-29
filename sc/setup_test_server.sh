#!/bin/bash
#
# Script de Instalación Automática - Diaken Test Server
# Para Ubuntu/Debian con SQLite, Nginx, Redis y Celery
#
# Uso: sudo bash setup_test_server.sh
#

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Diaken Test Server Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Por favor ejecuta este script como root o con sudo${NC}"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
if [ "$ACTUAL_USER" = "root" ]; then
    echo -e "${RED}No ejecutes este script directamente como root.${NC}"
    echo -e "${YELLOW}Usa: sudo bash setup_test_server.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}Usuario detectado: $ACTUAL_USER${NC}"
echo ""

# Variables
PROJECT_DIR="/opt/www/app/diaken-pdn"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log"

# Step 1: Install system dependencies
echo -e "${GREEN}[1/15] Instalando dependencias del sistema...${NC}"
apt update
apt install -y python3.12 python3.12-venv python3.12-dev \
    nginx redis-server git \
    build-essential libssl-dev libffi-dev \
    sshpass ansible curl

# Step 2: Verify project directory
echo -e "${GREEN}[2/15] Verificando directorio del proyecto...${NC}"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Error: Directorio $PROJECT_DIR no existe${NC}"
    echo -e "${YELLOW}Copia el proyecto a $PROJECT_DIR primero${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

# Step 3: Create virtual environment
echo -e "${GREEN}[3/15] Creando entorno virtual...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    sudo -u $ACTUAL_USER python3.12 -m venv "$VENV_DIR"
fi

# Step 4: Install Python dependencies
echo -e "${GREEN}[4/15] Instalando dependencias de Python...${NC}"
sudo -u $ACTUAL_USER bash -c "source $VENV_DIR/bin/activate && pip install --upgrade pip"
sudo -u $ACTUAL_USER bash -c "source $VENV_DIR/bin/activate && pip install -r requirements.txt"
sudo -u $ACTUAL_USER bash -c "source $VENV_DIR/bin/activate && pip install gunicorn"

# Step 5: Configure environment variables
echo -e "${GREEN}[5/15] Configurando variables de entorno...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    SECRET_KEY=$(sudo -u $ACTUAL_USER bash -c "source $VENV_DIR/bin/activate && python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'")
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    cat > "$PROJECT_DIR/.env" << EOF
# Django Configuration
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://$SERVER_IP

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
EOF
    chown $ACTUAL_USER:$ACTUAL_USER "$PROJECT_DIR/.env"
    echo -e "${GREEN}Archivo .env creado${NC}"
else
    echo -e "${YELLOW}Archivo .env ya existe, omitiendo...${NC}"
fi

# Step 6: Run migrations
echo -e "${GREEN}[6/15] Ejecutando migraciones de base de datos...${NC}"
sudo -u $ACTUAL_USER bash -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py migrate"

# Step 7: Create superuser (if not exists)
echo -e "${GREEN}[7/15] Verificando superusuario...${NC}"
USER_EXISTS=$(sudo -u $ACTUAL_USER bash -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py shell -c \"from django.contrib.auth.models import User; print(User.objects.filter(username='admin').exists())\"" 2>/dev/null || echo "False")

if [ "$USER_EXISTS" = "False" ]; then
    echo -e "${YELLOW}Creando superusuario 'admin'...${NC}"
    sudo -u $ACTUAL_USER bash -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py createsuperuser --noinput --username admin --email admin@example.com" || true
    echo -e "${YELLOW}Establece la contraseña del admin:${NC}"
    sudo -u $ACTUAL_USER bash -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py changepassword admin"
else
    echo -e "${GREEN}Superusuario 'admin' ya existe${NC}"
fi

# Step 8: Collect static files
echo -e "${GREEN}[8/15] Recolectando archivos estáticos...${NC}"
sudo -u $ACTUAL_USER bash -c "cd $PROJECT_DIR && source $VENV_DIR/bin/activate && python manage.py collectstatic --noinput"

# Step 9: Create necessary directories
echo -e "${GREEN}[9/15] Creando directorios necesarios...${NC}"
mkdir -p "$PROJECT_DIR/media/playbooks/host"
mkdir -p "$PROJECT_DIR/media/playbooks/group"
mkdir -p "$PROJECT_DIR/media/scripts/linux"
mkdir -p "$PROJECT_DIR/media/scripts/windows"
chown -R $ACTUAL_USER:$ACTUAL_USER "$PROJECT_DIR/media"

mkdir -p "$LOG_DIR/celery"
mkdir -p "$LOG_DIR/scheduler"
mkdir -p "$LOG_DIR/gunicorn"
chown $ACTUAL_USER:$ACTUAL_USER "$LOG_DIR/celery"
chown $ACTUAL_USER:$ACTUAL_USER "$LOG_DIR/scheduler"
chown $ACTUAL_USER:$ACTUAL_USER "$LOG_DIR/gunicorn"

mkdir -p /var/run/celery
chown $ACTUAL_USER:$ACTUAL_USER /var/run/celery

# Step 10: Configure Redis
echo -e "${GREEN}[10/15] Configurando Redis...${NC}"
systemctl start redis
systemctl enable redis
echo -e "${GREEN}Redis configurado${NC}"

# Step 11: Configure Celery service
echo -e "${GREEN}[11/15] Configurando servicio Celery...${NC}"
cat > /etc/systemd/system/celery-diaken.service << EOF
[Unit]
Description=Celery Worker for Diaken
After=network.target redis.service

[Service]
Type=forking
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/celery -A diaken worker \\
    --loglevel=info \\
    --logfile=$LOG_DIR/celery/diaken-worker.log \\
    --pidfile=/var/run/celery/diaken-worker.pid \\
    --detach
ExecStop=/bin/kill -s TERM \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start celery-diaken
systemctl enable celery-diaken
echo -e "${GREEN}Celery configurado${NC}"

# Step 12: Configure scheduler cron
echo -e "${GREEN}[12/15] Configurando scheduler...${NC}"
cat > "$PROJECT_DIR/run_scheduler.sh" << 'EOF'
#!/bin/bash
cd /opt/www/app/diaken-pdn
source venv/bin/activate
python manage.py run_scheduled_tasks >> /var/log/scheduler/scheduler.log 2>&1
EOF
chmod +x "$PROJECT_DIR/run_scheduler.sh"
chown $ACTUAL_USER:$ACTUAL_USER "$PROJECT_DIR/run_scheduler.sh"

# Add to crontab if not exists
CRON_CMD="* * * * * $PROJECT_DIR/run_scheduler.sh"
(sudo -u $ACTUAL_USER crontab -l 2>/dev/null | grep -F "$PROJECT_DIR/run_scheduler.sh") || \
    (sudo -u $ACTUAL_USER crontab -l 2>/dev/null; echo "$CRON_CMD") | sudo -u $ACTUAL_USER crontab -

echo -e "${GREEN}Scheduler configurado${NC}"

# Step 13: Configure Gunicorn service
echo -e "${GREEN}[13/15] Configurando servicio Gunicorn...${NC}"
cat > /etc/systemd/system/gunicorn-diaken.service << EOF
[Unit]
Description=Gunicorn daemon for Diaken
After=network.target

[Service]
Type=notify
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 4 \\
    --bind 127.0.0.1:8000 \\
    --timeout 300 \\
    --access-logfile $LOG_DIR/gunicorn/access.log \\
    --error-logfile $LOG_DIR/gunicorn/error.log \\
    diaken.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl start gunicorn-diaken
systemctl enable gunicorn-diaken
echo -e "${GREEN}Gunicorn configurado${NC}"

# Step 14: Configure Nginx
echo -e "${GREEN}[14/15] Configurando Nginx...${NC}"
SERVER_IP=$(hostname -I | awk '{print $1}')

cat > /etc/nginx/sites-available/diaken << EOF
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name localhost $SERVER_IP;
    
    client_max_body_size 100M;
    
    access_log $LOG_DIR/nginx/diaken-access.log;
    error_log $LOG_DIR/nginx/diaken-error.log;
    
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/diaken /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx
systemctl enable nginx
echo -e "${GREEN}Nginx configurado${NC}"

# Step 15: Final verification
echo -e "${GREEN}[15/15] Verificando servicios...${NC}"
echo ""

services=("redis" "celery-diaken" "gunicorn-diaken" "nginx")
all_ok=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}✓ $service está corriendo${NC}"
    else
        echo -e "${RED}✗ $service NO está corriendo${NC}"
        all_ok=false
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Instalación Completada${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Accede a la aplicación en:${NC}"
echo -e "  http://localhost"
echo -e "  http://$SERVER_IP"
echo ""
echo -e "${YELLOW}Usuario admin:${NC}"
echo -e "  Username: admin"
echo -e "  Password: (la que configuraste)"
echo ""
echo -e "${YELLOW}Logs importantes:${NC}"
echo -e "  Celery:    tail -f $LOG_DIR/celery/diaken-worker.log"
echo -e "  Scheduler: tail -f $LOG_DIR/scheduler/scheduler.log"
echo -e "  Gunicorn:  tail -f $LOG_DIR/gunicorn/error.log"
echo -e "  Nginx:     tail -f $LOG_DIR/nginx/diaken-error.log"
echo ""
echo -e "${YELLOW}Comandos útiles:${NC}"
echo -e "  Reiniciar servicios: sudo systemctl restart celery-diaken gunicorn-diaken nginx"
echo -e "  Ver estado:          sudo systemctl status celery-diaken gunicorn-diaken nginx"
echo ""

if [ "$all_ok" = true ]; then
    echo -e "${GREEN}¡Todo está funcionando correctamente!${NC}"
else
    echo -e "${RED}Algunos servicios no están corriendo. Revisa los logs.${NC}"
fi
