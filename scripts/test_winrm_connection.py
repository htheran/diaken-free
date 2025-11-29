#!/usr/bin/env python3
"""
Test WinRM connectivity to a Windows host
Usage: python test_winrm_connection.py <host> <username> <password> [auth_type]
"""

import sys
import winrm

def test_winrm(host, username, password, auth_type='ntlm', port=5985):
    """Test WinRM connection with different authentication methods"""
    
    print(f"\n{'='*60}")
    print(f"Testing WinRM Connection")
    print(f"{'='*60}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Username: {username}")
    print(f"Auth Type: {auth_type}")
    print(f"{'='*60}\n")
    
    # Build endpoint URL
    endpoint = f'http://{host}:{port}/wsman'
    print(f"Endpoint: {endpoint}\n")
    
    try:
        # Create session
        print(f"[1/3] Creating WinRM session with {auth_type} authentication...")
        session = winrm.Session(
            endpoint,
            auth=(username, password),
            transport=auth_type,
            server_cert_validation='ignore'
        )
        print("✓ Session created successfully\n")
        
        # Test simple command
        print("[2/3] Testing simple command (hostname)...")
        result = session.run_cmd('hostname')
        
        if result.status_code == 0:
            print(f"✓ Command executed successfully")
            print(f"  Output: {result.std_out.decode().strip()}")
            print(f"  Status Code: {result.status_code}\n")
        else:
            print(f"✗ Command failed")
            print(f"  Status Code: {result.status_code}")
            print(f"  Error: {result.std_err.decode()}\n")
            return False
        
        # Test PowerShell command
        print("[3/3] Testing PowerShell command...")
        result = session.run_ps('Get-ComputerInfo | Select-Object CsName, WindowsVersion')
        
        if result.status_code == 0:
            print(f"✓ PowerShell command executed successfully")
            print(f"  Output: {result.std_out.decode().strip()}\n")
        else:
            print(f"✗ PowerShell command failed")
            print(f"  Status Code: {result.status_code}")
            print(f"  Error: {result.std_err.decode()}\n")
            return False
        
        print(f"{'='*60}")
        print(f"✓ ALL TESTS PASSED - WinRM is working correctly!")
        print(f"{'='*60}\n")
        return True
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ CONNECTION FAILED")
        print(f"{'='*60}")
        print(f"Error: {e}")
        print(f"\nPossible causes:")
        print(f"  1. WinRM service not running on target")
        print(f"  2. Firewall blocking port {port}")
        print(f"  3. Wrong credentials")
        print(f"  4. Wrong authentication type (try: basic, ntlm, negotiate, credssp)")
        print(f"  5. WinRM listener not configured for Address=*")
        print(f"{'='*60}\n")
        return False

def test_all_auth_types(host, username, password, port=5985):
    """Test all authentication types"""
    auth_types = ['ntlm', 'basic', 'negotiate', 'credssp']
    
    print(f"\n{'#'*60}")
    print(f"Testing ALL authentication types")
    print(f"{'#'*60}\n")
    
    results = {}
    for auth_type in auth_types:
        print(f"\n--- Testing {auth_type.upper()} ---")
        results[auth_type] = test_winrm(host, username, password, auth_type, port)
    
    print(f"\n{'#'*60}")
    print(f"SUMMARY")
    print(f"{'#'*60}")
    for auth_type, success in results.items():
        status = "✓ WORKS" if success else "✗ FAILED"
        print(f"{auth_type.upper():12} : {status}")
    print(f"{'#'*60}\n")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python test_winrm_connection.py <host> <username> <password> [auth_type|all]")
        print("\nExamples:")
        print("  python test_winrm_connection.py 10.100.5.87 Administrator 'MyPassword' ntlm")
        print("  python test_winrm_connection.py 10.100.5.87 Administrator 'MyPassword' all")
        sys.exit(1)
    
    host = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    auth_type = sys.argv[4] if len(sys.argv) > 4 else 'ntlm'
    
    if auth_type.lower() == 'all':
        test_all_auth_types(host, username, password)
    else:
        success = test_winrm(host, username, password, auth_type)
        sys.exit(0 if success else 1)
