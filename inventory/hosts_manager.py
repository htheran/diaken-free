"""
Helper functions to manage /etc/hosts file for Diaken managed hosts.
"""
import os
import logging
import subprocess
from django.conf import settings

logger = logging.getLogger('inventory.hosts_manager')

HOSTS_FILE = '/etc/hosts'
MARKER_START = '# --- Diaken Managed Hosts ---'
MARKER_END = '# --- End Diaken Managed Hosts ---'


def update_hosts_file():
    """
    Update /etc/hosts file with all hosts from inventory.
    This function reads all hosts from the database and updates the managed section.
    """
    from inventory.models import Host
    
    try:
        # Get all active hosts from inventory
        hosts = Host.objects.filter(active=True).order_by('name')
        
        # Read current /etc/hosts content
        with open(HOSTS_FILE, 'r') as f:
            lines = f.readlines()
        
        # Find markers
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if MARKER_START in line:
                start_idx = i
            elif MARKER_END in line:
                end_idx = i
                break
        
        # Build new managed section
        managed_section = [MARKER_START + '\n']
        for host in hosts:
            # Use IP address for connection, but include hostname for reference
            managed_section.append(f"{host.ip}    {host.name}\n")
        managed_section.append(MARKER_END + '\n')
        
        # Reconstruct file
        if start_idx is not None and end_idx is not None:
            # Replace existing managed section
            new_lines = lines[:start_idx] + managed_section + lines[end_idx+1:]
        else:
            # Add managed section at the end
            new_lines = lines + ['\n'] + managed_section
        
        # Write to temporary file in /tmp (writable by diaken user)
        import tempfile
        import subprocess
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='diaken_hosts_')
        temp_file.writelines(new_lines)
        temp_file.close()
        
        # Move temporary file to /etc/hosts using sudo (atomic operation)
        # The diaken user needs sudo permissions for this specific command
        try:
            # Use full path to sudo since Django/Gunicorn may have limited PATH
            sudo_path = '/usr/bin/sudo'
            if not os.path.exists(sudo_path):
                sudo_path = '/bin/sudo'
            
            result = subprocess.run(
                [sudo_path, 'mv', temp_file.name, HOSTS_FILE],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                error_msg = f'Failed to move temp file to /etc/hosts: {result.stderr}'
                logger.error(f'HOSTS_FILE: {error_msg}')
                # Clean up temp file
                try:
                    os.remove(temp_file.name)
                except:
                    pass
                return False, error_msg
            
            logger.info(f'HOSTS_FILE: Updated /etc/hosts with {hosts.count()} hosts')
            return True, f'Successfully updated /etc/hosts with {hosts.count()} hosts'
            
        except subprocess.TimeoutExpired:
            error_msg = 'Timeout updating /etc/hosts'
            logger.error(f'HOSTS_FILE: {error_msg}')
            try:
                os.remove(temp_file.name)
            except:
                pass
            return False, error_msg
        
    except Exception as e:
        logger.error(f'HOSTS_FILE: Error updating /etc/hosts: {str(e)}', exc_info=True)
        return False, f'Error updating /etc/hosts: {str(e)}'


def add_host_to_hosts_file(hostname, ip_address):
    """
    Add a single host to /etc/hosts file.
    This is a convenience function that calls update_hosts_file().
    
    Args:
        hostname: Hostname of the server
        ip_address: IP address of the server
    """
    logger.info(f'HOSTS_FILE: Adding {hostname} ({ip_address}) to /etc/hosts')
    return update_hosts_file()


def remove_host_from_hosts_file(hostname):
    """
    Remove a single host from /etc/hosts file.
    This is a convenience function that calls update_hosts_file().
    
    Args:
        hostname: Hostname of the server to remove
    """
    logger.info(f'HOSTS_FILE: Removing {hostname} from /etc/hosts')
    return update_hosts_file()


def verify_hosts_file():
    """
    Verify that /etc/hosts file is properly formatted and accessible.
    """
    try:
        with open(HOSTS_FILE, 'r') as f:
            content = f.read()
        
        has_markers = MARKER_START in content and MARKER_END in content
        
        return True, {
            'accessible': True,
            'has_markers': has_markers,
            'size': len(content),
        }
    except Exception as e:
        return False, str(e)
