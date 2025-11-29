"""
Security Helper Functions for Diaken Project
Sanitization and validation utilities to prevent injection attacks
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize user inputs to prevent command injection and other attacks"""
    
    @staticmethod
    def sanitize_vm_name(vm_name: str) -> str:
        """
        Sanitize VM name to prevent command injection
        
        Args:
            vm_name: VM name from user input
            
        Returns:
            Sanitized VM name
            
        Raises:
            ValueError: If VM name contains invalid characters
        """
        if not vm_name:
            raise ValueError("VM name cannot be empty")
        
        # Permitir caracteres alfanuméricos, guiones, guiones bajos y puntos
        # Longitud máxima de 63 caracteres (estándar DNS)
        # Puntos permitidos para versiones (ej: PLANTILLA9.6)
        if not re.match(r'^[a-zA-Z0-9._-]{1,63}$', vm_name):
            raise ValueError(
                f"Invalid VM name: '{vm_name}'. "
                "Only alphanumeric characters, dots, hyphens and underscores allowed (max 63 chars)"
            )
        
        return vm_name
    
    @staticmethod
    def sanitize_hostname(hostname: str) -> str:
        """Sanitize hostname according to RFC 1123"""
        if not hostname:
            raise ValueError("Hostname cannot be empty")
        
        hostname = hostname.lower()
        
        if len(hostname) > 253:
            raise ValueError(f"Hostname too long: {len(hostname)} chars (max 253)")
        
        labels = hostname.split('.')
        for label in labels:
            if not label:
                raise ValueError("Empty label in hostname")
            if len(label) > 63:
                raise ValueError(f"Label too long: {label} (max 63 chars)")
            if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$', label):
                raise ValueError(f"Invalid label: {label}")
        
        return hostname
    
    @staticmethod
    def sanitize_network_name(network_name: str) -> str:
        """Sanitize network name for vCenter operations"""
        if not network_name:
            raise ValueError("Network name cannot be empty")
        
        if not re.match(r'^[a-zA-Z0-9 _.-]{1,80}$', network_name):
            raise ValueError(f"Invalid network name: '{network_name}'")
        
        if '  ' in network_name:
            raise ValueError("Network name cannot contain consecutive spaces")
        
        return network_name.strip()
    
    @staticmethod
    def sanitize_ip_address(ip_address: str) -> str:
        """Validate and sanitize IP address"""
        if not ip_address:
            raise ValueError("IP address cannot be empty")
        
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip_address)
        
        if not match:
            raise ValueError(f"Invalid IP address format: {ip_address}")
        
        octets = [int(x) for x in match.groups()]
        for octet in octets:
            if octet < 0 or octet > 255:
                raise ValueError(f"Invalid IP address: {ip_address}")
        
        if octets[0] in [0, 127, 255]:
            raise ValueError(f"Reserved IP address: {ip_address}")
        
        return ip_address
