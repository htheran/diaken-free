#!/bin/bash
################################################################################
# Diaken Installer for RedHat/CentOS/Rocky Linux
# Automated installation script for Diaken project
# 
# This script will:
# - Install all required dependencies
# - Clone project from GitHub
# - Configure Python virtual environment
# - Setup database and run migrations
# - Create Django superuser
# - Configure firewall
# - Provide instructions to start the application
#
# Usage: sudo bash install-diaken.sh
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="diaken"
GITHUB_REPO="https://github.com/htheran/diaken-free.git"
INSTALL_DIR="/opt/diaken"
PYTHON_VERSION="3.12"
PORT="9090"
# System user for Diaken (like nginx, postgresql, redis)
INSTALL_USER="diaken"
INSTALL_GROUP="diaken"
INSTALL_USER_HOME=$(eval echo ~$INSTALL_USER)

# Dynamic paths (no hardcoded usernames)
LOG_DIR="/var/log/${PROJECT_NAME}"
RUN_DIR="/var/run/${PROJECT_NAME}"
CELERY_LOG_DIR="${LOG_DIR}/celery"
CELERY_PID_DIR="${RUN_DIR}/celery"
DJANGO_LOG_DIR="${LOG_DIR}/django"
ANSIBLE_LOG_DIR="${LOG_DIR}/ansible"
REDIS_LOG_DIR="${LOG_DIR}/redis"

# Database configuration (will be set during installation)
DB_TYPE=""
DB_HOST=""
DB_PORT=""
DB_NAME=""
DB_USER=""
DB_PASSWORD=""

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
    print_success "Running as root"
}

check_os() {

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
    if [ -f /etc/redhat-release ]; then

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
        OS_VERSION=$(cat /etc/redhat-release)

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
        print_success "Detected: $OS_VERSION"

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
    else

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
        print_error "This script is designed for RedHat/CentOS/Rocky Linux"

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
        exit 1

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
    fi

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}
}

create_system_user() {
    print_header "Creating System User for Diaken"
    
    # Check if user already exists
    if id "$INSTALL_USER" &>/dev/null; then
        print_info "User '$INSTALL_USER' already exists"
    else
        print_info "Creating system user '$INSTALL_USER'..."
        # Create system user without home directory, no login shell
        # Similar to nginx, postgresql, redis users
        sudo useradd --system --create-home --shell /sbin/nologin --comment "Diaken Application User" "$INSTALL_USER"
        # Create .ssh directory for SSH operations (known_hosts)
        sudo mkdir -p "/home/$INSTALL_USER/.ssh"
        sudo chown -R "$INSTALL_USER":"$INSTALL_USER" "/home/$INSTALL_USER"
        sudo chmod 700 "/home/$INSTALL_USER/.ssh"
        print_success "System user '$INSTALL_USER' created"
    fi
    
    # Verify user was created
    if id "$INSTALL_USER" &>/dev/null; then
        print_success "User '$INSTALL_USER' verified"
    else
        print_error "Failed to create user '$INSTALL_USER'"
        exit 1
    fi
}

################################################################################
# Installation Functions
################################################################################

install_epel() {
    print_header "Installing EPEL Repository"
    
    if rpm -qa | grep -q epel-release; then
        print_success "EPEL repository already installed"
    else
        print_info "Installing EPEL repository..."
        sudo dnf install -y epel-release || sudo yum install -y epel-release
        print_success "EPEL repository installed"
    fi
}

install_dependencies() {
    print_header "Installing System Dependencies"
    
    print_info "Updating package cache..."
    sudo dnf update -y || sudo yum update -y
    
    print_info "Installing required packages..."
    
    # Core dependencies
    local packages=(
        "git"
        "python${PYTHON_VERSION}"
        "python${PYTHON_VERSION}-pip"
        "python${PYTHON_VERSION}-devel"
        "gcc"
        "openssl-devel"
        "bzip2-devel"
        "libffi-devel"
        "wget"
        "curl"
        "vim"
        "firewalld"
        "redis"
        "openssh-clients"
    )
    
    # Try dnf first, fallback to yum
    if command -v dnf &> /dev/null; then
        sudo dnf install -y "${packages[@]}" || {
            print_warning "Some packages failed with dnf, trying alternative names..."
            sudo dnf install -y git python3 python3-pip python3-devel gcc openssl-devel bzip2-devel libffi-devel wget curl vim firewalld
        }
    else
        sudo yum install -y "${packages[@]}" || {
            print_warning "Some packages failed with yum, trying alternative names..."
            sudo yum install -y git python3 python3-pip python3-devel gcc openssl-devel bzip2-devel libffi-devel wget curl vim firewalld
        }
    fi
    
    print_success "System dependencies installed"
}

check_python() {
    print_header "Checking Python Installation"
    
    # Try different Python command variations
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher"
        exit 1
    fi
    
    PYTHON_VER=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python detected: $PYTHON_VER (using $PYTHON_CMD)"
    
    # Export for later use
    export PYTHON_CMD
}

clone_repository() {
    print_header "Cloning Diaken Repository"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists"
        read -p "Do you want to remove it and clone fresh? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Removing existing directory..."
            rm -rf "$INSTALL_DIR"
        else
            print_info "Using existing directory"
            return 0
        fi
    fi
    
    print_info "Cloning from $GITHUB_REPO ..."
    git clone "$GITHUB_REPO" "$INSTALL_DIR"
    print_success "Repository cloned to $INSTALL_DIR"
}

setup_virtual_environment() {
    print_header "Setting Up Python Virtual Environment"
    
    cd "$INSTALL_DIR"
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
    else
        print_info "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    fi
    
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment ready"
}

install_python_packages() {
    print_header "Installing Python Dependencies"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        print_info "Installing packages from requirements.txt..."
        pip install -r requirements.txt
        print_success "Python packages installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

install_govc() {
    print_header "Installing govc (VMware CLI)"
    
    # Check if govc is already installed
    if command -v govc &> /dev/null; then
        local current_version=$(govc version 2>/dev/null | head -1)
        print_info "govc is already installed: $current_version"
        return 0
    fi
    
    print_info "Downloading and installing govc..."
    
    # Download and install govc
    if curl -L -o - "https://github.com/vmware/govmomi/releases/latest/download/govc_$(uname -s)_$(uname -m).tar.gz" | sudo tar -C /usr/local/bin -xvzf - govc 2>&1 | grep -q "govc"; then
        sudo chmod +x /usr/local/bin/govc
        local installed_version=$(govc version 2>/dev/null | head -1)
        print_success "govc installed successfully: $installed_version"
    else
        print_error "Failed to install govc"
        print_warning "You can install it manually later with:"
        print_warning "curl -L https://github.com/vmware/govmomi/releases/latest/download/govc_\$(uname -s)_\$(uname -m).tar.gz | sudo tar -C /usr/local/bin -xvzf - govc"
    fi
}

create_directories() {
    print_header "Creating Application Directories"
    
    cd "$INSTALL_DIR"
    
    # Base directories
    local dirs=("logs" "media/ssh" "media/ssl")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        else
            print_info "Directory already exists: $dir"
        fi
    done
    
    # Playbooks directory structure (RedHat, Debian, Windows)
    print_info "Creating playbooks directory structure..."
    local playbook_dirs=(
        "media/playbooks/redhat/host"
        "media/playbooks/redhat/group"
        "media/playbooks/debian/host"
        "media/playbooks/debian/group"
        "media/playbooks/windows/host"
        "media/playbooks/windows/group"
    )
    
    for dir in "${playbook_dirs[@]}"; do
        mkdir -p "$dir"
        print_success "Created: $dir"
    done
    
    # Scripts directory structure (RedHat, Debian, Windows)
    print_info "Creating scripts directory structure..."
    local script_dirs=(
        "media/scripts/redhat/host"
        "media/scripts/redhat/group"
        "media/scripts/debian/host"
        "media/scripts/debian/group"
        "media/scripts/windows/host"
        "media/scripts/windows/group"
    )
    
    for dir in "${script_dirs[@]}"; do
        mkdir -p "$dir"
        print_success "Created: $dir"
    done
    
    # Jinja2 templates directory structure
    print_info "Creating Jinja2 templates directory structure..."
    local j2_dirs=(
        "media/j2/host"
        "media/j2/group"
    )
    
    for dir in "${j2_dirs[@]}"; do
        mkdir -p "$dir"
        print_success "Created: $dir"
    done
    
    # Set proper permissions
    chmod -R 755 media logs
    print_success "Directories created and permissions set"
    
    # Create centralized log directories
    print_info "Creating centralized log directories..."
    sudo mkdir -p "${CELERY_LOG_DIR}" "${DJANGO_LOG_DIR}" "${ANSIBLE_LOG_DIR}" "${REDIS_LOG_DIR}"
    sudo mkdir -p "${CELERY_PID_DIR}"
    sudo chown -R ${INSTALL_USER}:${INSTALL_USER} "${LOG_DIR}" "${RUN_DIR}"
    print_success "Centralized log directories created at ${LOG_DIR}"
}

configure_database() {
    print_header "Database Configuration"
    
    # Check if running in unattended mode
    if [ -n "${DB_TYPE}" ]; then
        print_info "Using pre-configured database type: ${DB_TYPE}"
    else
        print_info "Select database type:"
        echo "  1) SQLite3 (Recommended for development/small deployments)"
        echo "  2) MariaDB/MySQL"
        echo "  3) PostgreSQL"
        echo ""
        read -p "Enter choice [1-3] (default: 1): " db_choice
        db_choice=${db_choice:-1}
        
        case $db_choice in
            1)
                DB_TYPE="sqlite3"
                ;;
            2)
                DB_TYPE="mariadb"
                ;;
            3)
                DB_TYPE="postgresql"
                ;;
            *)
                print_warning "Invalid choice. Using SQLite3."
                DB_TYPE="sqlite3"
                ;;
        esac
    fi
    
    print_info "Database type: ${DB_TYPE}"
    
    # Configure based on database type
    if [ "$DB_TYPE" = "sqlite3" ]; then
        print_success "SQLite3 selected - no additional configuration needed"
        print_info "Database will be created at: ${INSTALL_DIR}/db.sqlite3"
        
        # Create .env file for SQLite
        cat > "${INSTALL_DIR}/.env" << EOF
# Diaken Environment Configuration
# Generated on $(date)

# Database Configuration
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=${INSTALL_DIR}/db.sqlite3

# Celery Configuration  
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Logging
DJANGO_LOG_DIR=${DJANGO_LOG_DIR}
ANSIBLE_LOG_DIR=${ANSIBLE_LOG_DIR}
EOF
        
    elif [ "$DB_TYPE" = "mariadb" ] || [ "$DB_TYPE" = "postgresql" ]; then
        # Get database connection details
        if [ -z "${DB_HOST}" ]; then
            read -p "Database Host (IP or hostname): " DB_HOST
        fi
        
        if [ -z "${DB_PORT}" ]; then
            if [ "$DB_TYPE" = "mariadb" ]; then
                read -p "Database Port (default: 3306): " DB_PORT
                DB_PORT=${DB_PORT:-3306}
            else
                read -p "Database Port (default: 5432): " DB_PORT
                DB_PORT=${DB_PORT:-5432}
            fi
        fi
        
        if [ -z "${DB_NAME}" ]; then
            read -p "Database Name: " DB_NAME
        fi
        
        if [ -z "${DB_USER}" ]; then
            read -p "Database User: " DB_USER
        fi
        
        if [ -z "${DB_PASSWORD}" ]; then
            read -sp "Database Password: " DB_PASSWORD
            echo ""
        fi
        
        # Install database client
        if [ "$DB_TYPE" = "mariadb" ]; then
            print_info "Installing MariaDB client..."
            sudo dnf install -y mariadb-devel || sudo yum install -y mariadb-devel
            
            # Install Python MySQL client
            cd "${INSTALL_DIR}"
            source venv/bin/activate
            pip install mysqlclient
            
            DB_ENGINE="django.db.backends.mysql"
            
        elif [ "$DB_TYPE" = "postgresql" ]; then
            print_info "Installing PostgreSQL client..."
            sudo dnf install -y postgresql-devel || sudo yum install -y postgresql-devel
            
            # Install Python PostgreSQL client
            cd "${INSTALL_DIR}"
            source venv/bin/activate
            pip install psycopg2-binary
            
            DB_ENGINE="django.db.backends.postgresql"
        fi
        
        # Test database connection
        print_info "Testing database connection..."
        if [ "$DB_TYPE" = "mariadb" ]; then
            if mysql -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" -e "USE ${DB_NAME};" 2>/dev/null; then
                print_success "Database connection successful!"
            else
                print_error "Failed to connect to database. Please check your credentials."
                print_warning "Continuing with installation, but database configuration may need to be fixed."
            fi
        elif [ "$DB_TYPE" = "postgresql" ]; then
            if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" >/dev/null 2>&1; then
                print_success "Database connection successful!"
            else
                print_error "Failed to connect to database. Please check your credentials."
                print_warning "Continuing with installation, but database configuration may need to be fixed."
            fi
        fi
        
        # Create .env file
        cat > "${INSTALL_DIR}/.env" << EOF
# Diaken Environment Configuration
# Generated on $(date)

# Database Configuration
DB_ENGINE=${DB_ENGINE}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Logging
DJANGO_LOG_DIR=${DJANGO_LOG_DIR}
ANSIBLE_LOG_DIR=${ANSIBLE_LOG_DIR}
EOF
        
        print_success "Database configured: ${DB_TYPE}"
        print_info "Connection: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    fi
    
    # Set permissions for .env file
    chmod 600 "${INSTALL_DIR}/.env"
    chown ${INSTALL_USER}:${INSTALL_USER} "${INSTALL_DIR}/.env"
    print_success ".env file created with secure permissions (600)"
}

run_migrations() {
    print_header "Running Database Migrations"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    print_info "Running migrations..."
    python manage.py migrate
    
    # Fix database permissions (critical for SQLite to avoid "readonly database" error)
    print_info "Setting correct database permissions..."
    if [ -f "${INSTALL_DIR}/db.sqlite3" ]; then
        sudo chown ${INSTALL_USER}:${INSTALL_GROUP} "${INSTALL_DIR}/db.sqlite3"
        sudo chmod 664 "${INSTALL_DIR}/db.sqlite3"
        print_success "Database permissions set: ${INSTALL_USER}:${INSTALL_GROUP} (664)"
    fi
    
    # Ensure directory permissions are correct
    sudo chown -R ${INSTALL_USER}:${INSTALL_GROUP} "${INSTALL_DIR}"
    sudo chmod 755 "${INSTALL_DIR}"
    
    print_success "Database migrations completed"
}

initialize_default_settings() {
    print_header "Initializing Default Settings"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    print_info "Creating default system settings..."
    python manage.py init_default_settings
    
    print_success "Default settings initialized"
}

collect_static() {
    print_header "Collecting Static Files"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    print_info "Collecting static files..."
    python manage.py collectstatic --noinput
    
    print_success "Static files collected"
}

create_superuser() {
    print_header "Creating Django Superuser"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Use environment variables if set, otherwise use defaults or prompt
    if [ -z "$DJANGO_SUPERUSER_USERNAME" ]; then
        echo -e "\n${YELLOW}Please provide credentials for the Django admin user:${NC}"
        echo -e "${YELLOW}(Press Enter to use default: admin)${NC}\n"
        read -p "Username [admin]: " DJANGO_USER
        DJANGO_USER=${DJANGO_USER:-admin}
    else
        DJANGO_USER="$DJANGO_SUPERUSER_USERNAME"
        print_info "Using username from environment: $DJANGO_USER"
    fi
    
    if [ -z "$DJANGO_SUPERUSER_PASSWORD" ]; then
        while true; do
            read -s -p "Password: " DJANGO_PASS
            echo
            read -s -p "Password (again): " DJANGO_PASS2
            echo
            
            if [ "$DJANGO_PASS" = "$DJANGO_PASS2" ]; then
                break
            else
                print_error "Passwords don't match. Please try again."
            fi
        done
    else
        DJANGO_PASS="$DJANGO_SUPERUSER_PASSWORD"
        print_info "Using password from environment"
    fi
    
    if [ -z "$DJANGO_SUPERUSER_EMAIL" ]; then
        read -p "Email (optional, press Enter to skip): " DJANGO_EMAIL
    else
        DJANGO_EMAIL="$DJANGO_SUPERUSER_EMAIL"
        print_info "Using email from environment: $DJANGO_EMAIL"
    fi
    
    print_info "Creating superuser..."
    
    # Create superuser using Django shell
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='${DJANGO_USER}').exists():
    User.objects.create_superuser(
        username='${DJANGO_USER}',
        email='${DJANGO_EMAIL}' if '${DJANGO_EMAIL}' else None,
        password='${DJANGO_PASS}'
    )
    print('Superuser created successfully')
else:
    print('User already exists')
EOF
    
    print_success "Django superuser created: $DJANGO_USER"
}


configure_nginx() {
    print_header "Configuring Nginx Reverse Proxy"
    
    # Install nginx if not already installed
    if ! command -v nginx &> /dev/null; then
        print_info "Installing nginx..."
        if command -v dnf &> /dev/null; then
            sudo dnf install -y nginx
        elif command -v yum &> /dev/null; then
            sudo yum install -y nginx
        else
            print_error "Package manager not found. Please install nginx manually."
            return 1
        fi
    else
        print_info "Nginx already installed"
    fi
    
    # Generate self-signed SSL certificates
    print_info "Generating self-signed SSL certificates..."
    sudo mkdir -p /etc/nginx/ssl
    if [ ! -f /etc/nginx/ssl/diaken.crt ]; then
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/diaken.key \
            -out /etc/nginx/ssl/diaken.crt \
            -subj "/C=US/ST=State/L=City/O=Diaken/CN=diaken.local" \
            &> /dev/null
        print_success "SSL certificates generated"
    else
        print_info "SSL certificates already exist"
    fi
    
    # Create nginx configuration
    print_info "Creating nginx configuration..."
    sudo tee /etc/nginx/conf.d/diaken.conf > /dev/null << NGINX_EOF
# Diaken - Nginx Reverse Proxy Configuration
# Optimized for security and long-running Ansible playbooks

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;
    
    # SSL certificates (self-signed for development)
    ssl_certificate /etc/nginx/ssl/diaken.crt;
    ssl_certificate_key /etc/nginx/ssl/diaken.key;
    
    # Optimized SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Max file size (for uploads)
    client_max_body_size 100M;
    
    # Optimized buffers
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
    
    # Timeouts for long-running Ansible playbooks
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    send_timeout 600s;
    client_body_timeout 300s;
    client_header_timeout 300s;
    keepalive_timeout 65s;
    
    # Logs
    access_log /var/log/nginx/diaken_access.log;
    error_log /var/log/nginx/diaken_error.log;
    
    # Django static files
    location /static/ {
        alias ${INSTALL_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias ${INSTALL_DIR}/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Proxy to Django/Gunicorn
    location / {
        proxy_pass http://127.0.0.1:9090;
        proxy_http_version 1.1;
        
        # Django proxy headers
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # WebSocket support
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Disable buffering for real-time responses
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_redirect off;
    }
    
    # Deny access to sensitive files
    location ~ /\.(?!well-known) {
        deny all;
    }
    
    location ~ /\.(env|git) {
        deny all;
    }
}
NGINX_EOF
    
    # Add proxy configuration to Django settings
    print_info "Adding proxy configuration to Django settings..."
    if ! grep -q "NGINX REVERSE PROXY CONFIGURATION" "${INSTALL_DIR}/diaken/settings.py"; then
        cat >> "${INSTALL_DIR}/diaken/settings.py" << 'DJANGO_EOF'

# ============================================================
# NGINX REVERSE PROXY CONFIGURATION
# ============================================================
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
DJANGO_EOF
        print_success "Proxy configuration added to settings.py"
    else
        print_info "Proxy configuration already exists in settings.py"
    fi
    
    # Enable and start nginx
    print_info "Enabling and starting nginx..."
    sudo systemctl enable nginx
    sudo systemctl restart nginx
    
    # Verify nginx is running
    if sudo systemctl is-active --quiet nginx; then
        print_success "Nginx configured and running"
        print_info "Access Diaken at: https://$(hostname -I | awk '{print $1}')"
        print_warning "Using self-signed SSL certificate - browser will show security warning"
    else
        print_error "Nginx failed to start. Check logs with: sudo journalctl -u nginx -n 50"
        return 1
    fi
}

configure_firewall() {
    print_header "Configuring Firewall"
    
    # Check if firewalld is installed
    if ! command -v firewall-cmd &> /dev/null; then
        print_warning "firewalld not found, skipping firewall configuration..."
        print_info "Please configure firewall manually if needed"
        return 0
    fi
    
    # Check if firewalld is running
    if ! sudo systemctl is-active --quiet firewalld; then
        print_info "Starting firewalld service..."
        sudo systemctl start firewalld
        sudo systemctl enable firewalld
    fi
    
    # Open HTTP and HTTPS ports for nginx
    print_info "Opening HTTP (80) and HTTPS (443) ports for nginx..."
    sudo firewall-cmd --permanent --add-service=http 2>/dev/null || true
    sudo firewall-cmd --permanent --add-service=https 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    
    # Reload firewall
    sudo firewall-cmd --reload
    
    print_success "Firewall configured"
    print_info "Open ports: HTTP (80), HTTPS (443)"
    print_info "Current firewall status:"
    sudo firewall-cmd --list-services 2>/dev/null || true
}

configure_redis() {
    print_header "Configuring Redis"
    
    # Configure Redis to use centralized log directory
    print_info "Configuring Redis logs..."
    sudo sed -i "s|^logfile.*|logfile ${REDIS_LOG_DIR}/redis-server.log|" /etc/redis/redis.conf 2>/dev/null || 
        sudo sed -i "s|^logfile.*|logfile ${REDIS_LOG_DIR}/redis-server.log|" /etc/redis.conf 2>/dev/null || true
    
    # Create log file with proper permissions
    sudo touch "${REDIS_LOG_DIR}/redis-server.log"
    sudo chown redis:redis "${REDIS_LOG_DIR}/redis-server.log"
    sudo chmod 640 "${REDIS_LOG_DIR}/redis-server.log"
    
    print_info "Starting and enabling Redis service..."
    sudo systemctl restart redis
    sudo systemctl enable redis
    
    # Wait a moment for Redis to start
    sleep 2
    
    # Test Redis connection
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running and responding"
        print_info "Redis logs: ${REDIS_LOG_DIR}/redis-server.log"
    else
        print_error "Redis failed to start properly"
        print_info "Check Redis logs: sudo journalctl -u redis"
    fi
}

configure_celery() {
    print_header "Configuring Celery Worker"
    
    # Create log and pid directories with dynamic paths
    print_info "Creating Celery directories..."
    sudo mkdir -p "${CELERY_LOG_DIR}" "${CELERY_PID_DIR}"
    sudo chown -R "${INSTALL_USER}:${INSTALL_USER}" "${LOG_DIR}" "${RUN_DIR}"
    print_success "Celery directories created"
    
    # Create systemd service for Celery
    print_info "Creating Celery systemd service..."
    
    sudo tee /etc/systemd/system/celery.service > /dev/null << EOF
[Unit]
Description=Celery Service for Diaken
After=network.target redis.service

[Service]
Type=forking
User=${INSTALL_USER}
Group=${INSTALL_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=${INSTALL_DIR}/venv/bin/celery -A ${PROJECT_NAME} worker --loglevel=info --detach --logfile=${CELERY_LOG_DIR}/worker.log --pidfile=${CELERY_PID_DIR}/worker.pid
PIDFile=${CELERY_PID_DIR}/worker.pid
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Celery service file created"
    
    # Reload systemd and enable Celery
    print_info "Enabling Celery service..."
    sudo systemctl daemon-reload
    sudo systemctl enable celery
    sudo systemctl start celery
    
    # Wait a moment for Celery to start
    sleep 3
    
    # Check Celery status
    if sudo systemctl is-active --quiet celery; then
        print_success "Celery worker is running"
    else
        print_error "Celery worker failed to start"
        print_info "Check logs: sudo journalctl -u celery"
        print_info "Or: sudo tail -f ${CELERY_LOG_DIR}/worker.log"
    fi
}

create_systemd_service() {
    print_header "Creating Systemd Service for Diaken"
    
    print_info "Creating systemd service file..."
    
    # With nginx, Django should listen only on localhost
    # Without nginx, it can listen on all interfaces
    local LISTEN_ADDRESS="127.0.0.1:${PORT}"
    
    sudo tee /etc/systemd/system/diaken.service > /dev/null << EOF
[Unit]
Description=Diaken Django Application
After=network.target redis.service celery.service nginx.service

[Service]
Type=simple
User=${INSTALL_USER}
Group=${INSTALL_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/manage.py runserver ${LISTEN_ADDRESS}
Restart=always
RestartSec=10

# Logs
StandardOutput=append:${DJANGO_LOG_DIR}/server.log
StandardError=append:${DJANGO_LOG_DIR}/server_error.log

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable diaken.service
    sudo systemctl start diaken.service
    
    print_success "Systemd service created and started: diaken.service"
    print_info "Django listening on ${LISTEN_ADDRESS} (behind nginx proxy)"
}

configure_crontab() {
    print_header "Configuring Automated Cleanup Tasks (Crontab)"
    
    # Make scripts executable
    chmod +x "${INSTALL_DIR}/sc/cleanup_stuck_deployments.sh" 2>/dev/null
    chmod +x "${INSTALL_DIR}/sc/cleanup_snapshots.sh" 2>/dev/null
    
    # Check if crontab entries already exist
    if crontab -l 2>/dev/null | grep -q "cleanup_stuck_deployments.sh"; then
        print_info "Crontab entries already exist, skipping..."
        return 0
    fi
    
    print_info "Adding crontab entries for automated cleanup tasks..."
    
    # Create temporary crontab file
    TEMP_CRON=$(mktemp)
    
    # Get existing crontab (if any)
    crontab -l 2>/dev/null > "$TEMP_CRON" || true
    
    # Add cleanup tasks
    cat >> "$TEMP_CRON" << EOF

# Diaken Automated Cleanup Tasks
# Clean up stuck deployments every 6 hours
0 */6 * * * ${INSTALL_DIR}/sc/cleanup_stuck_deployments.sh >> ${LOG_DIR}/cleanup_stuck_deployments.log 2>&1

# Clean up expired snapshots daily at 2 AM
0 2 * * * ${INSTALL_DIR}/sc/cleanup_snapshots.sh >> ${LOG_DIR}/cleanup_snapshots.log 2>&1

# Diaken Scheduled Tasks - Run every minute
* * * * * cd ${INSTALL_DIR} && ${INSTALL_DIR}/venv/bin/python manage.py run_scheduled_tasks >> ${LOG_DIR}/scheduler.log 2>&1
EOF
    
    # Install new crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    print_success "Crontab configured successfully"
    print_info "Cleanup tasks scheduled:"
    print_info "  • Stuck deployments: Every 6 hours"
    print_info "  • Expired snapshots: Daily at 2 AM"
    print_info "  • Scheduled tasks: Every minute"
    print_info "  • Logs: ${LOG_DIR}/cleanup_*.log and ${LOG_DIR}/scheduler.log"
}

print_completion_message() {
    print_header "Installation Complete! 🎉"
    
    cat << EOF
${GREEN}
╔════════════════════════════════════════════════════════════════╗
║                   Diaken Installation Complete                 ║
╚════════════════════════════════════════════════════════════════╝
${NC}

${BLUE}Installation Details:${NC}
  • Installation Directory: ${GREEN}$INSTALL_DIR${NC}
  • Database: ${GREEN}${DB_TYPE^^}${NC}$([ "$DB_TYPE" != "sqlite3" ] && echo " (${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME})" || echo " (${INSTALL_DIR}/db.sqlite3)")
  • Django Port: ${GREEN}$PORT${NC} (internal)
  • Nginx: ${GREEN}HTTP (80) → HTTPS (443)${NC}
  • SSL: ${YELLOW}Self-signed certificate${NC}
  • Admin User: ${GREEN}$DJANGO_USER${NC}
  • Install User: ${GREEN}$INSTALL_USER${NC}
  • Redis: ${GREEN}Running on localhost:6379${NC}
  • Celery Worker: ${GREEN}Running as systemd service${NC}
  • govc (VMware CLI): ${GREEN}$(govc version 2>/dev/null | head -1 || echo 'Not installed')${NC}
  • Crontab: ${GREEN}Configured for automated cleanup${NC}
  • Centralized Logs: ${GREEN}${LOG_DIR}${NC}

${BLUE}To Start the Application:${NC}

  1. Navigate to the installation directory:
     ${YELLOW}cd $INSTALL_DIR${NC}

  2. Activate the virtual environment:
     ${YELLOW}source venv/bin/activate${NC}

  3. Start the development server:
     ${YELLOW}python manage.py runserver 0.0.0.0:$PORT${NC}

${BLUE}Access the Application:${NC}
  • URL: ${GREEN}https://$(hostname -I | awk '{print $1}')${NC}
  • Admin: ${GREEN}https://$(hostname -I | awk '{print $1}')/admin${NC}
  • ${YELLOW}Note: Your browser will show a security warning due to self-signed certificate${NC}
  • ${YELLOW}For production, replace with a valid SSL certificate${NC}

${BLUE}Useful Commands:${NC}
  • Check Nginx status: ${YELLOW}sudo systemctl status nginx${NC}
  • Restart Nginx: ${YELLOW}sudo systemctl restart nginx${NC}
  • Test Nginx config: ${YELLOW}sudo nginx -t${NC}
  • View Nginx logs: ${YELLOW}sudo tail -f /var/log/nginx/diaken_*.log${NC}
  • Check firewall status: ${YELLOW}sudo firewall-cmd --list-all${NC}
  • Check Redis status: ${YELLOW}sudo systemctl status redis${NC}
  • Check Celery status: ${YELLOW}sudo systemctl status celery${NC}
  • Restart Celery: ${YELLOW}sudo systemctl restart celery${NC}
  • View crontab: ${YELLOW}crontab -l${NC}
  
${BLUE}Centralized Logs (${GREEN}${LOG_DIR}${BLUE}):${NC}
  • All logs: ${YELLOW}tail -f ${LOG_DIR}/**/*.log${NC}
  • Celery logs: ${YELLOW}tail -f ${CELERY_LOG_DIR}/worker.log${NC}
  • Django logs: ${YELLOW}tail -f ${DJANGO_LOG_DIR}/*.log${NC}
  • Ansible logs: ${YELLOW}tail -f ${ANSIBLE_LOG_DIR}/*.log${NC}
  • Redis logs: ${YELLOW}tail -f ${REDIS_LOG_DIR}/*.log${NC}
  • Cleanup logs: ${YELLOW}tail -f ${LOG_DIR}/cleanup_*.log${NC}

${BLUE}Production Deployment:${NC}
  • ${GREEN}✓${NC} Nginx configured as reverse proxy with HTTPS
  • ${GREEN}✓${NC} Redis and Celery running as systemd services
  • ${GREEN}✓${NC} Automated cleanup tasks via crontab
  • ${GREEN}✓${NC} Centralized logging
  
For enhanced production:
  • Replace self-signed SSL with Let's Encrypt or commercial certificate
  • Consider Gunicorn for Django (instead of runserver)
  • Use PostgreSQL/MariaDB instead of SQLite for high load
  • Set up automated backups

${GREEN}Thank you for installing Diaken!${NC}
${BLUE}Documentation: https://github.com/htheran/diaken-free${NC}

EOF
}

################################################################################
# Main Installation Process
################################################################################

main() {
    clear
    
    cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                  DIAKEN INSTALLER v1.0                         ║
║         Automated VM Deployment & Management System            ║
║                                                                ║
║              RedHat / CentOS / Rocky Linux                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
    
    echo -e "\n${YELLOW}This script will install Diaken and all its dependencies.${NC}"
    echo -e "${YELLOW}Installation directory: $INSTALL_DIR${NC}"
    echo -e "${YELLOW}GitHub repository: $GITHUB_REPO${NC}"
    echo -e "${YELLOW}Install user: $INSTALL_USER${NC}\n"
    
    echo -e "${BLUE}For unattended installation, set these environment variables:${NC}"
    echo -e "  ${GREEN}DJANGO_SUPERUSER_USERNAME${NC}=admin"
    echo -e "  ${GREEN}DJANGO_SUPERUSER_PASSWORD${NC}=yourpassword"
    echo -e "  ${GREEN}DJANGO_SUPERUSER_EMAIL${NC}=admin@example.com\n"
    
    # Check if running in unattended mode
    if [ -n "$UNATTENDED" ] || [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        print_info "Running in unattended mode..."
    else
        read -p "Do you want to continue? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Installation cancelled"
            exit 0
        fi
    fi
    
    # Run installation steps
    check_root
    check_os
    create_system_user
    install_epel
    install_dependencies
    check_python
    clone_repository
    setup_virtual_environment
    install_python_packages
    install_govc
    create_directories
    configure_database
    run_migrations
    collect_static
    initialize_default_settings
    create_superuser
    configure_nginx
    configure_firewall
    configure_redis
    configure_celery
    create_systemd_service
    configure_crontab
    print_completion_message
    
    print_success "Installation completed successfully!"
}

# Run main function
main "$@"
