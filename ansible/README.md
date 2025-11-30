# Ansible - Playbooks CORE de Provisioning

⚠️ **IMPORTANTE:** Estos son los playbooks CORE de Diaken para provisioning inicial de VMs.

## Archivos CORE

- `provision_vm.yml` - RedHat/CentOS/Rocky
- `provision_debian_vm.yml` - Debian/Ubuntu  
- `provision_windows_vm.yml` - Windows
- `verify_reboot.yml` - Verificación post-reboot

## Diferencia con media/playbooks/

| Aspecto | ansible/ (CORE) | media/playbooks/ |
|---------|-----------------|------------------|
| **Propósito** | Provisioning inicial | Post-deployment |
| **Cuándo** | Automático | Opcional |
| **Modificable** | ❌ NO | ✅ SÍ |

Ver: [media/playbooks/README.md](../media/playbooks/README.md)
