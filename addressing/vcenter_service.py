"""
Servicio para conectar a vCenter y obtener información de VMs.
Usa PyVmomi para interactuar con la API de vCenter.
"""

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import atexit
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class VCenterService:
    """Servicio para consultar información de VMs desde vCenter"""
    
    def __init__(self, host: str, port: int, user: str, pwd: str, disable_ssl_verification: bool = True):
        """
        Inicializa el servicio de vCenter.
        
        Args:
            host: IP o hostname del vCenter
            port: Puerto de conexión (usualmente 443)
            user: Usuario para autenticación
            pwd: Contraseña del usuario
            disable_ssl_verification: Si se debe deshabilitar verificación SSL
        """
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.disable_ssl_verification = disable_ssl_verification
        self.si = None
    
    def connect(self):
        """Establece conexión con vCenter"""
        try:
            # Crear contexto SSL
            if self.disable_ssl_verification:
                context = ssl._create_unverified_context()
            else:
                context = ssl.create_default_context()
            
            # Conectar a vCenter
            self.si = SmartConnect(
                host=self.host,
                user=self.user,
                pwd=self.pwd,
                port=self.port,
                sslContext=context
            )
            
            # Registrar desconexión al salir
            atexit.register(Disconnect, self.si)
            
            return True
        except Exception as e:
            raise Exception(f"Error al conectar a vCenter {self.host}: {str(e)}")
    
    def disconnect(self):
        """Desconecta de vCenter"""
        if self.si:
            try:
                Disconnect(self.si)
            except:
                pass
    
    def get_all_vms(self) -> List[Dict]:
        """
        Obtiene información de todas las VMs en el vCenter.
        
        Returns:
            Lista de diccionarios con información de cada VM
        """
        if not self.si:
            raise Exception("No hay conexión activa a vCenter")
        
        vms_data = []
        
        try:
            # Obtener el contenido del vCenter
            content = self.si.RetrieveContent()
            
            # Obtener todas las VMs
            container = content.rootFolder
            viewType = [vim.VirtualMachine]
            recursive = True
            
            containerView = content.viewManager.CreateContainerView(
                container, viewType, recursive
            )
            
            vms = containerView.view
            
            for vm in vms:
                try:
                    vm_info = self._extract_vm_info(vm)
                    if vm_info:
                        vms_data.append(vm_info)
                except Exception as e:
                    # Si falla una VM, continuar con las demás
                    logger.warning(f"Error procesando VM: {str(e)}")
                    continue
            
            containerView.Destroy()
            
        except Exception as e:
            raise Exception(f"Error al obtener VMs: {str(e)}")
        
        return vms_data
    
    def _extract_vm_info(self, vm) -> Optional[Dict]:
        """
        Extrae información relevante de una VM.
        
        Args:
            vm: Objeto VirtualMachine de PyVmomi
            
        Returns:
            Diccionario con información de la VM o None si no tiene datos relevantes
        """
        try:
            # Información básica
            vm_name = vm.summary.config.name if vm.summary.config else "Unknown"
            guest_os = vm.summary.config.guestFullName if vm.summary.config else "Unknown"
            power_state = vm.runtime.powerState if vm.runtime else "Unknown"
            
            # Obtener IPs, MACs y redes
            ips = []
            macs = []
            hostnames = []
            networks = []
            
            # Intentar obtener desde guest
            if vm.guest and vm.guest.net:
                for nic in vm.guest.net:
                    # MACs
                    if nic.macAddress:
                        macs.append(nic.macAddress)
                    
                    # Red/VLAN
                    if nic.network:
                        if nic.network not in networks:
                            networks.append(nic.network)
                    
                    # IPs
                    if nic.ipAddress:
                        for ip in nic.ipAddress:
                            # Filtrar IPs locales y IPv6 link-local
                            if not ip.startswith('fe80') and not ip.startswith('169.254'):
                                ips.append(ip)
            
            # Hostname
            if vm.guest and vm.guest.hostName:
                hostnames.append(vm.guest.hostName)
            
            # Si no hay información de red, intentar desde config
            if not macs and vm.config and vm.config.hardware:
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        if hasattr(device, 'macAddress') and device.macAddress:
                            macs.append(device.macAddress)
            
            # Si no hay IPs ni MACs, no retornar esta VM
            if not ips and not macs:
                return None
            
            return {
                'vm_name': vm_name,
                'hostname': hostnames[0] if hostnames else vm_name,
                'ips': ips,
                'macs': macs,
                'networks': networks,
                'network_primary': networks[0] if networks else 'Unknown',
                'os': guest_os,
                'power_state': power_state,
                'ip_primary': ips[0] if ips else '',
                'mac_primary': macs[0] if macs else '',
            }
            
        except Exception as e:
            logger.warning(f"Error extrayendo info de VM: {str(e)}")
            return None
    
    def search_vms(self, query: str, search_field: str = 'all') -> List[Dict]:
        """
        Busca VMs por IP, MAC o hostname.
        
        Args:
            query: Texto a buscar
            search_field: Campo donde buscar ('ip', 'mac', 'hostname', 'all')
            
        Returns:
            Lista de VMs que coinciden con la búsqueda
        """
        all_vms = self.get_all_vms()
        
        if not query:
            return all_vms
        
        query = query.lower().strip()
        results = []
        
        for vm in all_vms:
            match = False
            
            if search_field in ['ip', 'all']:
                # Buscar en IPs
                for ip in vm.get('ips', []):
                    if query in ip.lower():
                        match = True
                        break
            
            if not match and search_field in ['mac', 'all']:
                # Buscar en MACs
                for mac in vm.get('macs', []):
                    if query in mac.lower().replace(':', '').replace('-', ''):
                        match = True
                        break
            
            if not match and search_field in ['hostname', 'all']:
                # Buscar en hostname
                hostname = vm.get('hostname', '').lower()
                if query in hostname:
                    match = True
            
            if match:
                results.append(vm)
        
        return results


def get_vcenter_vms(vcenter_config: Dict, search_query: str = '', search_field: str = 'all') -> List[Dict]:
    """
    Función helper para obtener VMs de un vCenter.
    
    Args:
        vcenter_config: Diccionario con configuración del vCenter
        search_query: Texto de búsqueda (opcional)
        search_field: Campo donde buscar (opcional)
        
    Returns:
        Lista de VMs
    """
    service = VCenterService(
        host=vcenter_config['host'],
        port=vcenter_config['port'],
        user=vcenter_config['user'],
        pwd=vcenter_config['pwd'],
        disable_ssl_verification=vcenter_config.get('disableSslCertValidation', True)
    )
    
    try:
        service.connect()
        
        if search_query:
            vms = service.search_vms(search_query, search_field)
        else:
            vms = service.get_all_vms()
        
        return vms
    finally:
        service.disconnect()
