Name:           diaken
Version:        2.3.6
Release:        1%{?dist}
Summary:        Diaken - Infrastructure Automation and Deployment Platform

License:        Proprietary
URL:            https://github.com/htheran/diaken-free
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.9
Requires:       python3-pip
Requires:       python3-virtualenv
Requires:       nginx
Requires:       redis
Requires:       git
Requires:       ansible-core >= 2.12
Requires:       mariadb-server
Requires:       mariadb-devel
Requires:       gcc
Requires:       python3-devel
Requires:       openssl

%description
Diaken is a comprehensive infrastructure automation and deployment platform
that provides VM deployment, configuration management, playbook execution,
and infrastructure monitoring capabilities.

Features:
- VM Deployment (VMware vCenter integration)
- Ansible Playbook Management and Execution
- Host and Group Inventory Management
- Scheduled Task Execution
- Security Fixes Management
- Snapshot Management
- User and Permission Management

%prep
%setup -q

%build
# No build needed for Python application

%install
rm -rf %{buildroot}

# Create directory structure
mkdir -p %{buildroot}/opt/diaken
mkdir -p %{buildroot}/etc/systemd/system
mkdir -p %{buildroot}/etc/nginx/conf.d
mkdir -p %{buildroot}/var/log/diaken
mkdir -p %{buildroot}/var/log/diaken/ansible
mkdir -p %{buildroot}/var/log/diaken/celery
mkdir -p %{buildroot}/usr/local/bin

# Copy application files
cp -r * %{buildroot}/opt/diaken/

# Copy systemd service files
install -m 644 packaging/diaken.service %{buildroot}/etc/systemd/system/
install -m 644 packaging/diaken-celery.service %{buildroot}/etc/systemd/system/
install -m 644 packaging/diaken-celery-beat.service %{buildroot}/etc/systemd/system/

# Copy nginx configuration
install -m 644 packaging/diaken-nginx.conf %{buildroot}/etc/nginx/conf.d/

# Copy installation script
install -m 755 install-diaken-nginx.sh %{buildroot}/usr/local/bin/diaken-install

%files
%defattr(-,root,root,-)
/opt/diaken
/etc/systemd/system/diaken.service
/etc/systemd/system/diaken-celery.service
/etc/systemd/system/diaken-celery-beat.service
/etc/nginx/conf.d/diaken-nginx.conf
/usr/local/bin/diaken-install
%dir /var/log/diaken
%dir /var/log/diaken/ansible
%dir /var/log/diaken/celery

%pre
# Create diaken user if it doesn't exist
if ! id -u diaken >/dev/null 2>&1; then
    useradd -r -s /bin/bash -d /opt/diaken -m diaken
fi

%post
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAKEN INSTALLATION - POST-INSTALL                       ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Diaken has been installed to /opt/diaken"
echo ""
echo "To complete the installation, run:"
echo "  sudo /usr/local/bin/diaken-install"
echo ""
echo "This will:"
echo "  • Configure the database"
echo "  • Set up virtual environment"
echo "  • Configure services"
echo "  • Set up SSL certificates"
echo "  • Start all services"
echo ""
echo "For more information, visit:"
echo "  https://github.com/htheran/diaken-free"
echo ""

%preun
if [ $1 -eq 0 ]; then
    # Stop services on uninstall
    systemctl stop diaken-celery-beat.service 2>/dev/null || true
    systemctl stop diaken-celery.service 2>/dev/null || true
    systemctl stop diaken.service 2>/dev/null || true
    systemctl disable diaken-celery-beat.service 2>/dev/null || true
    systemctl disable diaken-celery.service 2>/dev/null || true
    systemctl disable diaken.service 2>/dev/null || true
fi

%postun
if [ $1 -eq 0 ]; then
    # Remove user on uninstall
    userdel -r diaken 2>/dev/null || true
    # Remove log directory
    rm -rf /var/log/diaken
fi

%changelog
* Sat Nov 30 2024 Diaken Team <support@diaken.io> - 2.3.6-1
- Fix: AttributeError when deploy_env/deploy_group don't exist
- Feature: Bootstrap Icons implementation
- Feature: Improved dark mode (macOS style)
- Feature: Sidebar improvements
- Feature: Installation verification script
- Fix: Scheduler permissions
- Fix: UI animations removed
