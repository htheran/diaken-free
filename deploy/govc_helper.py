"""
Helper functions for VMware operations using govc CLI
"""
import subprocess
import os
import logging
from security_fixes.sanitization_helpers import InputSanitizer

# Configure logger
logger = logging.getLogger('deploy.govc_helper')


def change_vm_network_govc(vcenter_host, vcenter_user, vcenter_password, vm_name, network_name):
    """
    Change VM network using govc CLI
    
    Args:
        vcenter_host: vCenter hostname or IP
        vcenter_user: vCenter username
        vcenter_password: vCenter password
        vm_name: Name of the VM (will be sanitized)
        network_name: Name of the target network (will be sanitized)
        
    Returns:
        tuple: (success: bool, message: str)
    
    Raises:
        ValueError: If inputs contain invalid characters
    """
    # SECURITY: Sanitize inputs to prevent command injection
    try:
        vm_name = InputSanitizer.sanitize_vm_name(vm_name)
        network_name = InputSanitizer.sanitize_network_name(network_name)
    except ValueError as e:
        error_msg = f'Input validation failed: {e}'
        logger.error(f'GOVC: {error_msg}')
        return False, error_msg
    
    logger.info(f'GOVC: Iniciando cambio de red con govc...')
    logger.info(f'GOVC: VM: {vm_name}')
    logger.info(f'GOVC: Red destino: {network_name}')
    logger.info(f'GOVC: vCenter: {vcenter_host}')
    
    # Configurar variables de entorno para govc
    govc_env = os.environ.copy()
    govc_env['GOVC_URL'] = vcenter_host
    govc_env['GOVC_USERNAME'] = vcenter_user
    govc_env['GOVC_PASSWORD'] = vcenter_password
    govc_env['GOVC_INSECURE'] = 'true'
    govc_env['HOME'] = '/tmp'
    govc_env['GOVC_HOME'] = '/tmp/.govmomi'
    
    try:
        # PASO 1: Verificar que la VM existe
        logger.info(f'GOVC: Verificando que la VM existe...')
        vm_info_cmd = ['/usr/local/bin/govc', 'vm.info', vm_name]
        vm_info_result = subprocess.run(
            vm_info_cmd,
            env=govc_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if vm_info_result.returncode != 0:
            error_msg = f'VM "{vm_name}" no encontrada en vCenter\nstdout: {vm_info_result.stdout}\nstderr: {vm_info_result.stderr}'
            logger.error(f'GOVC: ❌ {error_msg}')
            return False, error_msg
        
        logger.info(f'GOVC: ✅ VM encontrada: {vm_name}')
        
        # PASO 2: Listar las redes disponibles para verificar que existe
        logger.info(f'GOVC: Verificando que la red existe...')
        net_ls_cmd = ['/usr/local/bin/govc', 'ls', 'network']
        net_ls_result = subprocess.run(
            net_ls_cmd,
            env=govc_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if net_ls_result.returncode == 0:
            available_networks = net_ls_result.stdout
            logger.info(f'GOVC: Redes disponibles:\n{available_networks}')
            
            # Verificar si la red objetivo está en la lista
            if network_name not in available_networks:
                logger.warning(f'GOVC: ⚠️ Red "{network_name}" no encontrada en la lista de redes')
                logger.warning(f'GOVC: Intentando cambiar de todas formas...')
        else:
            logger.warning(f'GOVC: No se pudo listar las redes: {net_ls_result.stderr}')
        
        # PASO 3: Obtener información actual de la red de la VM
        logger.info(f'GOVC: Obteniendo información de red actual de la VM...')
        vm_net_info_cmd = ['/usr/local/bin/govc', 'device.info', '-vm', vm_name, 'ethernet-0']
        vm_net_info_result = subprocess.run(
            vm_net_info_cmd,
            env=govc_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if vm_net_info_result.returncode == 0:
            logger.info(f'GOVC: Red actual de la VM:\n{vm_net_info_result.stdout}')
        else:
            logger.warning(f'GOVC: No se pudo obtener info de red actual: {vm_net_info_result.stderr}')
        
        # PASO 4: Cambiar la red de la VM usando govc
        logger.info(f'GOVC: Ejecutando cambio de red...')
        logger.info(f'GOVC: Comando: /usr/local/bin/govc vm.network.change -vm {vm_name} -net {network_name} ethernet-0')
        govc_cmd = [
            '/usr/local/bin/govc', 'vm.network.change',
            '-vm', vm_name,
            '-net', network_name,
            'ethernet-0'  # Primera NIC
        ]
        
        result = subprocess.run(
            govc_cmd,
            env=govc_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        logger.info(f'GOVC: Return code: {result.returncode}')
        logger.info(f'GOVC: STDOUT: {result.stdout}')
        logger.info(f'GOVC: STDERR: {result.stderr}')
        
        if result.returncode == 0:
            logger.info(f'GOVC: ✅ Red cambiada exitosamente a: {network_name}')
            
            # PASO 5: Verificar el cambio
            logger.info(f'GOVC: Verificando el cambio de red...')
            verify_cmd = ['/usr/local/bin/govc', 'device.info', '-vm', vm_name, 'ethernet-0']
            verify_result = subprocess.run(
                verify_cmd,
                env=govc_env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if verify_result.returncode == 0:
                logger.info(f'GOVC: Red después del cambio:\n{verify_result.stdout}')
            
            return True, f'Red cambiada exitosamente a: {network_name}'
        else:
            error_msg = f'Error cambiando red con govc (return code: {result.returncode})\nstdout: {result.stdout}\nstderr: {result.stderr}'
            logger.error(f'GOVC: ❌ {error_msg}')
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = 'Timeout ejecutando govc (>30s)'
        logger.error(f'GOVC: ❌ {error_msg}')
        return False, error_msg
    except Exception as e:
        error_msg = f'Excepción ejecutando govc: {str(e)}'
        logger.error(f'GOVC: ❌ {error_msg}')
        return False, error_msg


def configure_vm_ip_govc(vcenter_host, vcenter_user, vcenter_password, vm_name, vm_user, vm_password, 
                         interface, ip_address, gateway, netmask='255.255.255.0'):
    """
    Configure IP address inside VM using govc guest operations
    
    Args:
        vcenter_host: vCenter hostname or IP
        vcenter_user: vCenter username
        vcenter_password: vCenter password
        vm_name: Name of the VM (will be sanitized)
        vm_user: VM guest username (e.g. root)
        vm_password: VM guest password
        interface: Network interface name (will be sanitized)
        ip_address: New IP address (will be sanitized)
        gateway: Gateway IP (will be sanitized)
        netmask: Netmask (default: 255.255.255.0)
        
    Returns:
        tuple: (success: bool, message: str)
    
    Raises:
        ValueError: If inputs contain invalid characters
    """
    # SECURITY: Sanitize inputs to prevent command injection
    try:
        vm_name = InputSanitizer.sanitize_vm_name(vm_name)
        ip_address = InputSanitizer.sanitize_ip_address(ip_address)
        gateway = InputSanitizer.sanitize_ip_address(gateway)
        # Sanitize interface name (only alphanumeric and basic characters)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', interface):
            raise ValueError(f"Invalid interface name: {interface}")
    except ValueError as e:
        error_msg = f'Input validation failed: {e}'
        logger.error(f'GOVC: {error_msg}')
        return False, error_msg
    
    
    # Configurar variables de entorno para govc
    govc_env = os.environ.copy()
    govc_env['GOVC_URL'] = vcenter_host
    govc_env['GOVC_USERNAME'] = vcenter_user
    govc_env['GOVC_PASSWORD'] = vcenter_password
    govc_env['GOVC_INSECURE'] = 'true'
    govc_env['GOVC_GUEST_LOGIN'] = f'{vm_user}:{vm_password}'
    govc_env['HOME'] = '/tmp'
    govc_env['GOVC_HOME'] = '/tmp/.govmomi'
    
    try:
        # Comando nmcli para cambiar IP
        nmcli_cmd = f'nmcli connection modify {interface} ipv4.addresses {ip_address}/24 ipv4.gateway {gateway} ipv4.method manual && nmcli connection reload'
        
        logger.debug(f'GOVC: Ejecutando comando en VM: {nmcli_cmd}')
        govc_cmd = [
            '/usr/local/bin/govc', 'guest.run',
            '-vm', vm_name,
            '-l', f'{vm_user}:{vm_password}',
            '/bin/bash', '-c', nmcli_cmd
        ]
        
        result = subprocess.run(
            govc_cmd,
            env=govc_env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.debug(f'GOVC: ✅ IP configurada exitosamente: {ip_address}')
            return True, f'IP configurada exitosamente: {ip_address}'
        else:
            error_msg = f'Error configurando IP con govc\nstdout: {result.stdout}\nstderr: {result.stderr}'
            logger.debug(f'GOVC: ❌ {error_msg}')
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = 'Timeout ejecutando govc guest.run (>30s)'
        logger.debug(f'GOVC: ❌ {error_msg}')
        return False, error_msg
    except Exception as e:
        error_msg = f'Excepción ejecutando govc guest.run: {str(e)}'
        logger.debug(f'GOVC: ❌ {error_msg}')
        return False, error_msg
