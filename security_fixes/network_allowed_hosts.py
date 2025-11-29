"""
Network-based ALLOWED_HOSTS Middleware for Django

This middleware extends Django's ALLOWED_HOSTS functionality to support
CIDR network ranges (e.g., 10.104.10.0/24) in addition to individual IPs.

Security: This allows you to whitelist entire network segments instead of
individual IPs, making it easier to manage access from internal networks.

Usage:
    1. Add to MIDDLEWARE in settings.py
    2. Configure DJANGO_ALLOWED_NETWORKS in .env with CIDR ranges
    
Example .env:
    DJANGO_ALLOWED_NETWORKS=10.104.10.0/24,10.100.5.0/24,192.168.1.0/24
"""

import ipaddress
import logging
from django.core.exceptions import DisallowedHost
from django.http import HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class NetworkAllowedHostsMiddleware(MiddlewareMixin):
    """
    Middleware to validate requests against CIDR network ranges.
    
    This middleware checks if the incoming request's host header matches
    either:
    1. Standard ALLOWED_HOSTS (hostnames and individual IPs)
    2. ALLOWED_NETWORKS (CIDR ranges like 10.104.10.0/24)
    
    If neither matches, the request is rejected with HTTP 400.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_networks = []
        self._load_allowed_networks()
        super().__init__(get_response)
    
    def _load_allowed_networks(self):
        """
        Load and parse ALLOWED_NETWORKS from Django settings.
        
        Expected format: List of CIDR network strings
        Example: ['10.104.10.0/24', '10.100.5.0/24', '192.168.1.0/24']
        """
        from django.conf import settings
        
        networks = getattr(settings, 'ALLOWED_NETWORKS', [])
        
        for network_str in networks:
            try:
                network = ipaddress.ip_network(network_str, strict=False)
                self.allowed_networks.append(network)
                logger.info(f"Loaded allowed network: {network}")
            except ValueError as e:
                logger.error(f"Invalid network CIDR '{network_str}': {e}")
    
    def _is_ip_in_allowed_networks(self, ip_str):
        """
        Check if an IP address is within any of the allowed networks.
        
        Args:
            ip_str (str): IP address as string (e.g., '10.104.10.20')
        
        Returns:
            bool: True if IP is in any allowed network, False otherwise
        """
        try:
            ip = ipaddress.ip_address(ip_str)
            
            for network in self.allowed_networks:
                if ip in network:
                    return True
            
            return False
        except ValueError:
            # Not a valid IP address
            return False
    
    def _get_host_from_request(self, request):
        """
        Extract the host from the request.
        
        Args:
            request: Django HttpRequest object
        
        Returns:
            str: Host header value (may include port)
        """
        return request.get_host().split(':')[0]  # Remove port if present
    
    def process_request(self, request):
        """
        Process incoming request and validate host header.
        
        This method validates that the host is either:
        1. A valid hostname in Django's ALLOWED_HOSTS (excluding '*')
        2. An IP address within one of the ALLOWED_NETWORKS CIDR ranges
        
        Args:
            request: Django HttpRequest object
        
        Returns:
            None if request is allowed, HttpResponseBadRequest if rejected
        """
        from django.conf import settings
        
        if not self.allowed_networks:
            # No networks configured, skip this middleware
            return None
        
        try:
            host = self._get_host_from_request(request)
            
            # Check if host is an IP address in allowed networks
            if self._is_ip_in_allowed_networks(host):
                logger.info(f"Request from IP {host} allowed by network whitelist")
                request._network_validated = True
                return None
            
            # Check if host matches allowed hostnames (excluding wildcard)
            allowed_hosts = [h for h in settings.ALLOWED_HOSTS if h != '*']
            
            # Check exact match
            if host in allowed_hosts:
                return None
            
            # Check wildcard domains (e.g., '.example.com')
            for allowed in allowed_hosts:
                if allowed.startswith('.') and (host.endswith(allowed) or host.endswith(allowed[1:])):
                    return None
            
            # Not allowed - reject with 403 Forbidden
            logger.warning(f"Request from {host} REJECTED - not in allowed networks or hosts")
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden(
                f"<h1>403 Forbidden</h1>"
                f"<p>Access from host '{host}' is not allowed.</p>"
                f"<p>Contact the administrator if you believe this is an error.</p>"
            )
            
        except Exception as e:
            logger.error(f"Error in NetworkAllowedHostsMiddleware: {e}")
            # On error, reject for security
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("<h1>403 Forbidden</h1><p>Security validation error.</p>")


class NetworkAllowedHostsValidator:
    """
    Custom ALLOWED_HOSTS validator that works with network ranges.
    
    This class can be used to replace Django's default host validation
    to support both standard hostnames/IPs and CIDR network ranges.
    """
    
    def __init__(self, allowed_hosts, allowed_networks):
        """
        Initialize validator with allowed hosts and networks.
        
        Args:
            allowed_hosts (list): Standard ALLOWED_HOSTS list
            allowed_networks (list): List of CIDR network strings
        """
        self.allowed_hosts = allowed_hosts
        self.allowed_networks = []
        
        for network_str in allowed_networks:
            try:
                network = ipaddress.ip_network(network_str, strict=False)
                self.allowed_networks.append(network)
            except ValueError as e:
                logger.error(f"Invalid network CIDR '{network_str}': {e}")
    
    def __call__(self, host):
        """
        Validate if a host is allowed.
        
        Args:
            host (str): Host header value
        
        Returns:
            bool: True if host is allowed, False otherwise
        """
        # Remove port if present
        host = host.split(':')[0]
        
        # Check standard ALLOWED_HOSTS
        if host in self.allowed_hosts or f'.{host}' in self.allowed_hosts:
            return True
        
        # Check wildcard
        if '*' in self.allowed_hosts:
            return True
        
        # Check domain wildcards (e.g., '.example.com')
        for allowed in self.allowed_hosts:
            if allowed.startswith('.') and host.endswith(allowed[1:]):
                return True
        
        # Check if host is an IP in allowed networks
        try:
            ip = ipaddress.ip_address(host)
            for network in self.allowed_networks:
                if ip in network:
                    return True
        except ValueError:
            # Not an IP address
            pass
        
        return False
