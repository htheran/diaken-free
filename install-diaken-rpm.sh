#!/bin/bash
################################################################################
# DIAKEN RPM INSTALLER - Interactive Installation Script
# Version: 2.3.6
# Description: Professional RPM-based installer for RedHat/CentOS/Rocky Linux
# Author: Diaken Team
# License: Proprietary
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Installation variables
INSTALL_DIR="/opt/diaken"
LOG_DIR="/var/log/diaken"
USER="diaken"
VENV_DIR="$INSTALL_DIR/venv"
DB_TYPE=""
DB_NAME="diaken_db"
DB_USER="diaken_user"
DB_PASSWORD=""
DB_HOST="localhost"
DB_PORT=""
ADMIN_USER="admin"
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
DOMAIN=""
USE_SSL="no"

# Progress tracking
TOTAL_STEPS=15
CURRENT_STEP=0

################################################################################
# UTILITY FUNCTIONS
################################################################################

print_header() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}     ${BOLD}DIAKEN RPM INSTALLER - Interactive Setup${NC}           ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}     Version 2.3.6                                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    local percentage=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    echo -e "\n${BLUE}[Step $CURRENT_STEP/$TOTAL_STEPS - $percentage%]${NC} ${BOLD}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))
    
    printf "\r${CYAN}Progress: [${NC}"
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "${CYAN}] ${BOLD}%3d%%${NC}" $percentage
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/redhat-release ]]; then
        print_error "This installer is for RedHat-based distributions only"
        exit 1
    fi
    
    local os_version=$(cat /etc/redhat-release)
    print_info "Detected OS: $os_version"
}

################################################################################
# USER INPUT FUNCTIONS
################################################################################

get_database_config() {
    print_header
    echo -e "${BOLD}DATABASE CONFIGURATION${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Database type
    echo -e "${BOLD}Select database type:${NC}"
    echo "  1) MariaDB (recommended)"
    echo "  2) PostgreSQL"
    echo "  3) SQLite (development only)"
    echo ""
    read -p "Enter choice [1-3]: " db_choice
    
    case $db_choice in
        1) DB_TYPE="mariadb"; DB_PORT="3306" ;;
        2) DB_TYPE="postgresql"; DB_PORT="5432" ;;
        3) DB_TYPE="sqlite"; return ;;
        *) print_error "Invalid choice"; exit 1 ;;
    esac
    
    echo ""
    read -p "Database name [$DB_NAME]: " input
    DB_NAME=${input:-$DB_NAME}
    
    read -p "Database user [$DB_USER]: " input
    DB_USER=${input:-$DB_USER}
    
    while true; do
        read -sp "Database password: " DB_PASSWORD
        echo ""
        if [[ -n "$DB_PASSWORD" ]]; then
            read -sp "Confirm password: " db_pass_confirm
            echo ""
            if [[ "$DB_PASSWORD" == "$db_pass_confirm" ]]; then
                break
            else
                print_error "Passwords do not match. Try again."
            fi
        else
            print_error "Password cannot be empty"
        fi
    done
    
    read -p "Database host [$DB_HOST]: " input
    DB_HOST=${input:-$DB_HOST}
    
    read -p "Database port [$DB_PORT]: " input
    DB_PORT=${input:-$DB_PORT}
}

get_admin_config() {
    print_header
    echo -e "${BOLD}ADMIN USER CONFIGURATION${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    read -p "Admin username [$ADMIN_USER]: " input
    ADMIN_USER=${input:-$ADMIN_USER}
    
    while true; do
        read -p "Admin email: " ADMIN_EMAIL
        if [[ "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            break
        else
            print_error "Invalid email format"
        fi
    done
    
    while true; do
        read -sp "Admin password: " ADMIN_PASSWORD
        echo ""
        if [[ ${#ADMIN_PASSWORD} -ge 8 ]]; then
            read -sp "Confirm password: " admin_pass_confirm
            echo ""
            if [[ "$ADMIN_PASSWORD" == "$admin_pass_confirm" ]]; then
                break
            else
                print_error "Passwords do not match. Try again."
            fi
        else
            print_error "Password must be at least 8 characters"
        fi
    done
}

get_network_config() {
    print_header
    echo -e "${BOLD}NETWORK CONFIGURATION${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    local default_ip=$(hostname -I | awk '{print $1}')
    read -p "Domain or IP address [$default_ip]: " input
    DOMAIN=${input:-$default_ip}
    
    echo ""
    read -p "Enable SSL/TLS? (yes/no) [no]: " input
    USE_SSL=${input:-no}
}

confirm_installation() {
    print_header
    echo -e "${BOLD}INSTALLATION SUMMARY${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Database:${NC}"
    echo "  Type: $DB_TYPE"
    if [[ "$DB_TYPE" != "sqlite" ]]; then
        echo "  Name: $DB_NAME"
        echo "  User: $DB_USER"
        echo "  Host: $DB_HOST:$DB_PORT"
    fi
    echo ""
    echo -e "${BOLD}Admin User:${NC}"
    echo "  Username: $ADMIN_USER"
    echo "  Email: $ADMIN_EMAIL"
    echo ""
    echo -e "${BOLD}Network:${NC}"
    echo "  Domain/IP: $DOMAIN"
    echo "  SSL/TLS: $USE_SSL"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    read -p "Proceed with installation? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        print_warning "Installation cancelled"
        exit 0
    fi
}

################################################################################
# INSTALLATION FUNCTIONS
################################################################################

install_dependencies() {
    print_step "Installing system dependencies"
    
    local packages=(
        "python3"
        "python3-pip"
        "python3-virtualenv"
        "python3-devel"
        "nginx"
        "redis"
        "git"
        "gcc"
        "openssl"
        "ansible-core"
    )
    
    if [[ "$DB_TYPE" == "mariadb" ]]; then
        packages+=("mariadb-server" "mariadb-devel")
    elif [[ "$DB_TYPE" == "postgresql" ]]; then
        packages+=("postgresql-server" "postgresql-devel")
    fi
    
    local total=${#packages[@]}
    local current=0
    
    for pkg in "${packages[@]}"; do
        current=$((current + 1))
        show_progress $current $total
        dnf install -y "$pkg" &>/dev/null || yum install -y "$pkg" &>/dev/null
    done
    echo ""
    print_success "Dependencies installed"
}

setup_database() {
    print_step "Setting up database"
    
    if [[ "$DB_TYPE" == "mariadb" ]]; then
        systemctl start mariadb
        systemctl enable mariadb
        
        # Secure installation
        mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'$DB_HOST' IDENTIFIED BY '$DB_PASSWORD';"
        mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'$DB_HOST';"
        mysql -e "FLUSH PRIVILEGES;"
        
        print_success "MariaDB configured"
        
    elif [[ "$DB_TYPE" == "postgresql" ]]; then
        postgresql-setup --initdb
        systemctl start postgresql
        systemctl enable postgresql
        
        sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
        
        print_success "PostgreSQL configured"
    else
        print_info "Using SQLite (no setup required)"
    fi
}

setup_virtualenv() {
    print_step "Setting up Python virtual environment"
    
    cd "$INSTALL_DIR"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    
    if [[ "$DB_TYPE" == "mariadb" ]]; then
        pip install mysqlclient
    elif [[ "$DB_TYPE" == "postgresql" ]]; then
        pip install psycopg2-binary
    fi
    
    print_success "Virtual environment configured"
}

configure_django() {
    print_step "Configuring Django application"
    
    cd "$INSTALL_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Generate secret key
    local secret_key=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    
    # Create .env file
    cat > .env << EOF
SECRET_KEY='$secret_key'
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.$([ "$DB_TYPE" == "mariadb" ] && echo "mysql" || echo "$DB_TYPE")
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECURE_SSL_REDIRECT=$([ "$USE_SSL" == "yes" ] && echo "True" || echo "False")
SESSION_COOKIE_SECURE=$([ "$USE_SSL" == "yes" ] && echo "True" || echo "False")
CSRF_COOKIE_SECURE=$([ "$USE_SSL" == "yes" ] && echo "True" || echo "False")
EOF
    
    chmod 600 .env
    chown $USER:$USER .env
    
    print_success "Django configured"
}

run_migrations() {
    print_step "Running database migrations"
    
    cd "$INSTALL_DIR"
    source "$VENV_DIR/bin/activate"
    
    python manage.py makemigrations
    python manage.py migrate
    
    print_success "Migrations completed"
}

create_superuser() {
    print_step "Creating admin superuser"
    
    cd "$INSTALL_DIR"
    source "$VENV_DIR/bin/activate"
    
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USER').exists():
    User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
EOF
    
    print_success "Admin user created"
}

collect_static() {
    print_step "Collecting static files"
    
    cd "$INSTALL_DIR"
    source "$VENV_DIR/bin/activate"
    
    python manage.py collectstatic --noinput
    
    print_success "Static files collected"
}

setup_services() {
    print_step "Configuring systemd services"
    
    systemctl daemon-reload
    systemctl enable diaken.service
    systemctl enable diaken-celery.service
    systemctl enable diaken-celery-beat.service
    systemctl enable redis
    systemctl enable nginx
    
    print_success "Services configured"
}

configure_nginx() {
    print_step "Configuring Nginx"
    
    if [[ "$USE_SSL" == "yes" ]]; then
        # Generate self-signed certificate
        mkdir -p /etc/nginx/ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/diaken.key \
            -out /etc/nginx/ssl/diaken.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        
        print_info "Self-signed SSL certificate generated"
    fi
    
    systemctl restart nginx
    print_success "Nginx configured"
}

configure_firewall() {
    print_step "Configuring firewall"
    
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        print_success "Firewall configured"
    else
        print_warning "Firewall not found, skipping"
    fi
}

setup_cron_jobs() {
    print_step "Setting up scheduled tasks"
    
    # Add cron jobs for cleanup scripts
    (crontab -u $USER -l 2>/dev/null; cat << EOF
# Diaken scheduled tasks
0 */6 * * * /opt/diaken/sc/cleanup_stuck_deployments.sh >> /var/log/diaken/cleanup.log 2>&1
0 2 * * * /opt/diaken/sc/cleanup_snapshots.sh >> /var/log/diaken/cleanup.log 2>&1
*/5 * * * * /opt/diaken/sc/run_scheduler.sh >> /var/log/diaken/scheduler.log 2>&1
EOF
    ) | crontab -u $USER -
    
    print_success "Cron jobs configured"
}

set_permissions() {
    print_step "Setting file permissions"
    
    chown -R $USER:$USER "$INSTALL_DIR"
    chown -R $USER:$USER "$LOG_DIR"
    
    chmod -R 755 "$INSTALL_DIR"
    chmod -R 755 "$LOG_DIR"
    
    # Secure sensitive files
    chmod 600 "$INSTALL_DIR/.env"
    chmod 600 "$INSTALL_DIR/diaken/settings.py"
    
    print_success "Permissions set"
}

start_services() {
    print_step "Starting services"
    
    systemctl start redis
    systemctl start diaken.service
    systemctl start diaken-celery.service
    systemctl start diaken-celery-beat.service
    systemctl restart nginx
    
    sleep 3
    
    # Check service status
    if systemctl is-active --quiet diaken.service; then
        print_success "Diaken service started"
    else
        print_error "Diaken service failed to start"
    fi
    
    if systemctl is-active --quiet diaken-celery.service; then
        print_success "Celery worker started"
    else
        print_error "Celery worker failed to start"
    fi
    
    if systemctl is-active --quiet nginx; then
        print_success "Nginx started"
    else
        print_error "Nginx failed to start"
    fi
}

show_completion() {
    print_header
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}     ${BOLD}INSTALLATION COMPLETED SUCCESSFULLY!${NC}                  ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Access Information:${NC}"
    echo -e "  URL: $([ "$USE_SSL" == "yes" ] && echo "https" || echo "http")://$DOMAIN"
    echo -e "  Username: ${BOLD}$ADMIN_USER${NC}"
    echo -e "  Password: ${BOLD}(as configured)${NC}"
    echo ""
    echo -e "${BOLD}Service Management:${NC}"
    echo -e "  Status:  ${CYAN}systemctl status diaken${NC}"
    echo -e "  Restart: ${CYAN}systemctl restart diaken${NC}"
    echo -e "  Logs:    ${CYAN}journalctl -u diaken -f${NC}"
    echo ""
    echo -e "${BOLD}Verification:${NC}"
    echo -e "  Run: ${CYAN}sudo bash /opt/diaken/sc/check_installation.sh${NC}"
    echo ""
    echo -e "${BOLD}Documentation:${NC}"
    echo -e "  https://github.com/htheran/diaken-free"
    echo ""
    print_success "Diaken is ready to use!"
}

################################################################################
# MAIN INSTALLATION FLOW
################################################################################

main() {
    check_root
    check_os
    
    print_header
    echo -e "${BOLD}Welcome to Diaken RPM Installer!${NC}"
    echo ""
    echo "This installer will guide you through the setup process."
    echo "Press Enter to continue..."
    read
    
    # Gather user input
    get_database_config
    get_admin_config
    get_network_config
    confirm_installation
    
    # Start installation
    print_header
    echo -e "${BOLD}Starting installation...${NC}"
    echo ""
    
    install_dependencies
    setup_database
    setup_virtualenv
    configure_django
    run_migrations
    create_superuser
    collect_static
    setup_services
    configure_nginx
    configure_firewall
    setup_cron_jobs
    set_permissions
    start_services
    
    show_completion
}

# Run main function
main "$@"
