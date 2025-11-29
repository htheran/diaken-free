# Snapshot Retention System

## Overview

The Diaken platform automatically manages vCenter snapshots with configurable retention periods. Snapshots are created before executing playbooks and automatically deleted after a specified time.

---

## Configuration

### Retention Period

**Location:** Settings → Global Settings → `snapshot_retention_hours`

**Range:** 1 - 99 hours  
**Default:** 24 hours  
**Current:** 1 hour (for testing purposes)

### How to Change Retention

1. Go to **Settings → Global Settings**
2. Find `snapshot_retention_hours`
3. Set value between 1-99 hours
4. Save

---

## Examples by Retention Period

### 1 Hour (Testing)
```
Created: 10:15:56
Deleted: ~11:30 (within 15 min of 11:15:56)
```

### 2 Hours
```
Created: 10:15:56
Deleted: ~12:30 (within 15 min of 12:15:56)
```

### 24 Hours (Default)
```
Created: 10:15:56 Day 1
Deleted: ~10:30 Day 2
```

### 72 Hours (3 Days)
```
Created: Monday 10:15:56
Deleted: Thursday ~10:30
```

---

## How It Works

**Cleanup runs:** Every 15 minutes  
**Precision:** ±15 minutes from exact retention time  
**Timezone:** UTC (timezone-aware)  
**Algorithm:** Exact age calculation in hours

---

## Storage Calculation

```
Storage = VMs × 25GB × (Retention Hours / 24)

Examples:
- 10 VMs, 1h:  ~10 GB
- 10 VMs, 24h: 250 GB
- 10 VMs, 72h: 750 GB
```

---

## Monitoring

```bash
# View cleanup logs
tail -f /var/log/snapshot_cleanup.log

# Manual cleanup
python manage.py cleanup_snapshots

# Check retention
python manage.py shell -c "
from settings.models import GlobalSetting
r = GlobalSetting.objects.filter(key='snapshot_retention_hours').first()
print(f'Retention: {r.value}h')
"
```
