# 📚 Diaken Documentation

Documentation for Diaken - Automated VM Deployment and Infrastructure Management System.

## 📖 Available Documentation

### Installation & Setup
- **[INSTALLER_README.md](INSTALLER_README.md)** - Complete installation guide
  - System requirements
  - Installation options (nginx vs standalone)
  - Step-by-step instructions
  - Post-installation configuration

### Operations
- **[PROVISIONING_EXPLAINED.md](PROVISIONING_EXPLAINED.md)** - How VM provisioning works
  - Provisioning workflow
  - Playbook structure
  - Network configuration
  - Troubleshooting provisioning

### Troubleshooting
- **[TROUBLESHOOTING_SSH.md](TROUBLESHOOTING_SSH.md)** - SSH connection issues
  - Common SSH problems
  - Connection diagnostics
  - Key management
  - Solutions and workarounds

### Reference
- **[COMPONENTS.md](COMPONENTS.md)** - Installed components inventory
  - System dependencies
  - Python packages
  - Services and daemons
  - Directory structure

## 🚀 Quick Start

1. Download installer:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/htheran/diaken-free/main/install-diaken-nginx.sh -o install-diaken-nginx.sh
   chmod +x install-diaken-nginx.sh
   ```

2. Run installation:
   ```bash
   sudo ./install-diaken-nginx.sh
   ```

3. Access Diaken:
   ```
   https://your-server-ip/
   ```

## 📝 Additional Resources

- **GitHub Repository:** https://github.com/htheran/diaken-free
- **Issues:** https://github.com/htheran/diaken-free/issues

## 🤝 Contributing

Documentation improvements are welcome! Please submit pull requests or open issues for:
- Corrections
- Clarifications
- Additional examples
- New guides

---

**Version:** 2.2.3  
**Last Updated:** 2025-11-30
