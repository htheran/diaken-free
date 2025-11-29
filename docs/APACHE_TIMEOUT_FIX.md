# Apache Timeout Configuration for Long-Running Deployments

## Problem

VM deployments were failing with **504 Gateway Timeout** after approximately 2 minutes.

**Error:**
```
Gateway Timeout
The gateway did not receive a timely response from the upstream server or application.
```

**Cause:**
- Default Apache timeout: 60 seconds
- Default WSGI timeouts: 60-120 seconds
- VM deployments take: 8-10 minutes (depending on playbooks)

## Solution

Increased all timeout values to **900 seconds (15 minutes)** to accommodate long-running deployment operations.

### Files Modified

#### 1. `/etc/httpd/conf.d/00-diaken-global.conf`

Added WSGI timeout parameters:

```apache
WSGIDaemonProcess diaken \
    python-home=/opt/www/app/diaken-pdn/venv \
    python-path=/opt/www/app/diaken-pdn \
    user=apache \
    group=apache \
    processes=2 \
    threads=15 \
    display-name=%{GROUP} \
    socket-timeout=900 \
    connect-timeout=900 \
    request-timeout=900 \
    queue-timeout=900 \
    graceful-timeout=900
```

**Timeout Parameters:**
- `socket-timeout=900` - Socket read/write timeout
- `connect-timeout=900` - Connection establishment timeout
- `request-timeout=900` - Request processing timeout
- `queue-timeout=900` - Queue wait timeout
- `graceful-timeout=900` - Graceful shutdown timeout

#### 2. `/etc/httpd/conf.d/diaken-ssl.conf`

Added Apache timeout directives:

```apache
# Timeout Configuration
# Increased timeouts for long-running deployment operations (8-10 minutes)
# Default Apache timeout is 60 seconds, which is too short for VM deployments
Timeout 900
ProxyTimeout 900
```

**Directives:**
- `Timeout 900` - Overall request timeout
- `ProxyTimeout 900` - Proxy connection timeout

## Verification

After applying changes:

1. Restart Apache:
   ```bash
   sudo systemctl restart httpd
   ```

2. Test deployment:
   - Deploy a VM with playbooks
   - Verify it completes without timeout (up to 15 minutes)

3. Check logs if issues persist:
   ```bash
   tail -f /var/log/httpd/error_log
   ```

## Timeout Values

| Component | Old Value | New Value | Reason |
|-----------|-----------|-----------|--------|
| Apache Timeout | 60s | 900s | VM deployments take 8-10 minutes |
| WSGI socket-timeout | default | 900s | Prevent socket closure during long operations |
| WSGI connect-timeout | default | 900s | Allow time for vCenter connections |
| WSGI request-timeout | default | 900s | Allow full deployment to complete |
| WSGI queue-timeout | default | 900s | Prevent queue timeout during busy periods |
| WSGI graceful-timeout | default | 900s | Allow graceful shutdown of long operations |

## Notes

- **15 minutes** should be sufficient for most deployments
- If deployments consistently take longer, increase timeouts further
- Monitor Apache memory usage with longer timeouts
- Consider implementing async task queue for very long operations

## Related Issues

- Gateway Timeout (504) errors during VM deployment
- Deployments failing before completion
- Ansible playbook execution interrupted

## Date

October 16, 2025
