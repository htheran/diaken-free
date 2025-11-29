#!/bin/bash
# Test WinRM with different username formats

HOST="$1"
PASSWORD="$2"

if [ -z "$HOST" ] || [ -z "$PASSWORD" ]; then
    echo "Usage: $0 <host> <password>"
    echo "Example: $0 10.100.5.87 'MyPassword'"
    exit 1
fi

echo ""
echo "============================================================"
echo "Testing WinRM with Different Username Formats"
echo "============================================================"
echo ""

# Test different username formats
USERNAMES=(
    "Administrator"
    ".\Administrator"
    "administrator"
    ".\administrator"
)

for USERNAME in "${USERNAMES[@]}"; do
    echo "--- Testing with username: $USERNAME ---"
    python /opt/www/app/scripts/test_winrm_connection.py "$HOST" "$USERNAME" "$PASSWORD" ntlm
    echo ""
done

echo "============================================================"
echo "Testing Complete"
echo "============================================================"
echo ""
