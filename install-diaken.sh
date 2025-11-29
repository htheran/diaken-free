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
    if [ -f /etc/redhat-release ]; then
        OS_VERSION=$(cat /etc/redhat-release)
        print_success "Detected: $OS_VERSION"
    else
        print_error "This script is designed for RedHat/CentOS/Rocky Linux"
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

create_directories() {
    print_header "Creating Application Directories"
    
    cd "$INSTALL_DIR"
    
    local dirs=("logs" "media/playbooks" "media/scripts" "media/ssh" "media/ssl")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created directory: $dir"
        else
            print_info "Directory already exists: $dir"
        fi
    done
    
    # Set proper permissions
    chmod -R 755 media logs
    print_success "Directories created and permissions set"
}

run_migrations() {
    print_header "Running Database Migrations"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    print_info "Running migrations..."
    python manage.py migrate
    
    print_success "Database migrations completed"
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
    
    echo -e "\n${YELLOW}Please provide credentials for the Django admin user:${NC}\n"
    
    read -p "Username: " DJANGO_USER
    
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
    
    read -p "Email (optional, press Enter to skip): " DJANGO_EMAIL
    
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

configure_firewall() {
    print_header "Configuring Firewall"
    
    # Check if firewalld is installed
    if ! command -v firewall-cmd &> /dev/null; then
        print_warning "firewalld not found, installing..."
        sudo dnf install -y firewalld || sudo yum install -y firewalld
    fi
    
    # Start and enable firewalld
    print_info "Starting firewalld service..."
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    
    # Check if port is already open
    if sudo firewall-cmd --list-ports | grep -q "${PORT}/tcp"; then
        print_success "Port $PORT is already open"
    else
        print_info "Opening port $PORT..."
        sudo firewall-cmd --permanent --add-port=${PORT}/tcp
        sudo firewall-cmd --reload
        print_success "Port $PORT opened permanently"
    fi
    
    print_info "Current firewall ports:"
    sudo firewall-cmd --list-ports
}

create_systemd_service() {
    print_header "Creating Systemd Service (Optional)"
    
    read -p "Do you want to create a systemd service to auto-start Diaken? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Skipping systemd service creation"
        return 0
    fi
    
    print_info "Creating systemd service file..."
    
    cat > /etc/systemd/system/diaken.service << EOF
[Unit]
Description=Diaken Django Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/manage.py runserver 0.0.0.0:$PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable diaken.service
    
    print_success "Systemd service created: diaken.service"
    print_info "You can start it with: sudo systemctl start diaken"
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
  • Database: ${GREEN}SQLite (db.sqlite3)${NC}
  • Port: ${GREEN}$PORT${NC}
  • Admin User: ${GREEN}$DJANGO_USER${NC}

${BLUE}To Start the Application:${NC}

  1. Navigate to the installation directory:
     ${YELLOW}cd $INSTALL_DIR${NC}

  2. Activate the virtual environment:
     ${YELLOW}source venv/bin/activate${NC}

  3. Start the development server:
     ${YELLOW}python manage.py runserver 0.0.0.0:$PORT${NC}

${BLUE}Access the Application:${NC}
  • URL: ${GREEN}http://$(hostname -I | awk '{print $1}'):$PORT${NC}
  • Admin: ${GREEN}http://$(hostname -I | awk '{print $1}'):$PORT/admin${NC}

${BLUE}Useful Commands:${NC}
  • Check firewall status: ${YELLOW}sudo firewall-cmd --list-all${NC}
  • View logs: ${YELLOW}tail -f $INSTALL_DIR/logs/*.log${NC}
  • Restart firewall: ${YELLOW}sudo systemctl restart firewalld${NC}

${BLUE}Production Deployment:${NC}
  For production, consider using:
  • Gunicorn or uWSGI instead of runserver
  • Nginx as reverse proxy
  • PostgreSQL instead of SQLite
  • Systemd service for auto-start

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
    echo -e "${YELLOW}GitHub repository: $GITHUB_REPO${NC}\n"
    
    read -p "Do you want to continue? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    # Run installation steps
    check_root
    check_os
    install_epel
    install_dependencies
    check_python
    clone_repository
    setup_virtual_environment
    install_python_packages
    create_directories
    run_migrations
    collect_static
    create_superuser
    configure_firewall
    create_systemd_service
    print_completion_message
    
    print_success "Installation completed successfully!"
}

# Run main function
main "$@"
