# Diaken Server Requirements

## Overview

Resource requirements for running the Diaken platform with Ansible playbook execution at scale.

---

## Base Requirements (Small Scale: 1-10 servers)

### Minimum Configuration
```
CPU:    2 cores
RAM:    4 GB
Swap:   4 GB
Disk:   50 GB
```

### Recommended Configuration
```
CPU:    4 cores
RAM:    8 GB
Swap:   4 GB
Disk:   100 GB
```

**Use case:** Development, testing, small deployments

---

## Medium Scale (10-25 servers)

### Recommended Configuration
```
CPU:    4-6 cores
RAM:    12-16 GB
Swap:   8 GB
Disk:   200 GB
```

**Use case:** Staging environments, medium-sized infrastructure

---

## Large Scale (25-50 servers)

### Recommended Configuration
```
CPU:    8-12 cores
RAM:    24-32 GB
Swap:   16 GB
Disk:   500 GB - 1 TB
```

**Use case:** Production environments, large infrastructure

---

## Detailed Analysis for 50 Servers

### CPU Requirements

**Base calculation:**
```
Ansible forks (default): 5 parallel connections
50 servers / 5 forks = 10 batches
Each fork needs: ~0.5 CPU cores during execution

Minimum: 4 cores (will be slower)
Recommended: 8 cores (good performance)
Optimal: 12-16 cores (best performance)
```

**CPU Usage Breakdown:**
```
Component               CPU Usage
─────────────────────────────────
Django/Gunicorn         1-2 cores
PostgreSQL/SQLite       0.5-1 core
Ansible Control Node    2-8 cores (depends on forks)
vCenter API calls       0.5-1 core
Background tasks        0.5-1 core
─────────────────────────────────
Total                   5-14 cores
```

**Recommendation: 8-12 cores**

---

### RAM Requirements

**Base calculation:**
```
Per Ansible fork: ~100-200 MB
With 5 forks: 500 MB - 1 GB
With 10 forks: 1-2 GB
With 20 forks: 2-4 GB

Plus base system overhead
```

**RAM Usage Breakdown:**
```
Component                   RAM Usage
──────────────────────────────────────
Operating System            1-2 GB
Django/Gunicorn (4 workers) 2-4 GB
PostgreSQL/Database         1-2 GB
Ansible (5 forks)           1-2 GB
Ansible (10 forks)          2-4 GB
Ansible (20 forks)          4-8 GB
Python processes            1-2 GB
vCenter connections         500 MB - 1 GB
File buffers/cache          2-4 GB
──────────────────────────────────────
Total (5 forks)             8-16 GB
Total (10 forks)            10-20 GB
Total (20 forks)            14-28 GB
```

**Recommendations by fork count:**
- **5 forks (default):** 16 GB RAM
- **10 forks:** 24 GB RAM
- **20 forks:** 32 GB RAM

**Recommended: 24-32 GB RAM**

---

### Swap Space

**Purpose:**
- Handle memory spikes during large playbook executions
- Prevent OOM (Out of Memory) kills
- Safety buffer for system stability

**Calculation:**
```
Rule of thumb: 50-100% of RAM

For 24 GB RAM: 12-24 GB swap
For 32 GB RAM: 16-32 GB swap
```

**Recommendation: 16 GB swap**

---

### Disk Space

**Components:**
```
Component                   Disk Usage
──────────────────────────────────────
Operating System            10-20 GB
Diaken Application          5-10 GB
Python packages             2-5 GB
Database (SQLite/PostgreSQL) 5-20 GB
Logs (/var/log)             10-50 GB
Ansible temp files          5-10 GB
SSL certificates            1-5 GB
Snapshots metadata          1-5 GB
Media files                 5-10 GB
Backup space                50-100 GB
──────────────────────────────────────
Total                       94-235 GB
```

**Growth over time:**
```
Database: ~100 MB per 1000 deployments
Logs: ~1 GB per month (with rotation)
History: ~50 MB per 1000 executions
```

**Recommendations:**
- **Minimum:** 200 GB
- **Recommended:** 500 GB
- **Optimal:** 1 TB

**Recommended: 500 GB - 1 TB**

---

### Network Requirements

**Bandwidth:**
```
Per server connection: ~1-5 Mbps during playbook execution
50 servers × 5 Mbps = 250 Mbps peak

Recommended: 500 Mbps - 1 Gbps
```

**Latency:**
- To managed servers: < 50ms (ideal)
- To vCenter: < 20ms (ideal)

---

## Recommended Configuration for 50 Servers

### Option 1: Balanced (Recommended)
```
CPU:    8 cores (16 threads)
RAM:    24 GB
Swap:   16 GB
Disk:   500 GB SSD
Network: 1 Gbps
```

**Ansible forks:** 10  
**Concurrent executions:** 10 servers at a time  
**Total time for 50 servers:** ~5 batches

**Cost:** Medium  
**Performance:** Good  
**Scalability:** Can handle up to 75 servers

---

### Option 2: High Performance
```
CPU:    12 cores (24 threads)
RAM:    32 GB
Swap:   16 GB
Disk:   1 TB SSD
Network: 1 Gbps
```

**Ansible forks:** 20  
**Concurrent executions:** 20 servers at a time  
**Total time for 50 servers:** ~3 batches

**Cost:** High  
**Performance:** Excellent  
**Scalability:** Can handle up to 100+ servers

---

### Option 3: Budget (Minimum)
```
CPU:    6 cores (12 threads)
RAM:    16 GB
Swap:   8 GB
Disk:   250 GB SSD
Network: 500 Mbps
```

**Ansible forks:** 5  
**Concurrent executions:** 5 servers at a time  
**Total time for 50 servers:** ~10 batches

**Cost:** Low  
**Performance:** Acceptable  
**Scalability:** Limited to 50 servers

---

## Performance Comparison

### Playbook Execution Time (Update-Redhat-Host example)

**Assumptions:**
- Average playbook duration: 5 minutes per server
- 50 servers total

| Configuration | Forks | Batches | Total Time | Efficiency |
|---------------|-------|---------|------------|------------|
| Budget | 5 | 10 | ~50 min | 100% |
| Balanced | 10 | 5 | ~25 min | 200% |
| High Perf | 20 | 3 | ~15 min | 333% |

---

## Tuning Ansible for Performance

### Increase Forks

Edit `/etc/ansible/ansible.cfg`:
```ini
[defaults]
forks = 10  # Default: 5
```

**Recommendations:**
- 16 GB RAM: forks = 5-8
- 24 GB RAM: forks = 10-15
- 32 GB RAM: forks = 20-25

### Enable Pipelining

```ini
[ssh_connection]
pipelining = True
```

**Benefit:** Reduces SSH overhead by ~30%

### Optimize SSH

```ini
[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

**Benefit:** Reuses SSH connections

### Disable Gathering Facts (when not needed)

In playbooks:
```yaml
- hosts: all
  gather_facts: no  # Skip if not needed
```

**Benefit:** Saves 2-5 seconds per host

---

## Monitoring Resources

### Check Current Usage

```bash
# CPU usage
top -bn1 | grep "Cpu(s)"

# RAM usage
free -h

# Disk usage
df -h

# Swap usage
swapon --show

# Active Ansible processes
ps aux | grep ansible | wc -l
```

### Monitor During Execution

```bash
# Real-time monitoring
htop

# Watch RAM usage
watch -n 1 free -h

# Watch Ansible forks
watch -n 1 'ps aux | grep ansible-playbook | wc -l'
```

---

## Optimization Tips

### 1. Use SSD Storage
- 3-5x faster than HDD
- Better for database and logs
- Recommended for production

### 2. Separate Database Server (Optional)
For very large scale (100+ servers):
```
App Server:  8 cores, 16 GB RAM
DB Server:   4 cores, 16 GB RAM
```

### 3. Use PostgreSQL Instead of SQLite
- Better performance at scale
- Concurrent connections
- Recommended for 50+ servers

### 4. Enable Log Rotation
```bash
# Prevent logs from filling disk
logrotate -f /etc/logrotate.d/diaken
```

### 5. Schedule Heavy Tasks
- Run updates during off-hours
- Distribute load across time
- Avoid peak usage times

---

## Scaling Beyond 50 Servers

### 100 Servers
```
CPU:    16 cores
RAM:    48 GB
Swap:   24 GB
Disk:   1-2 TB
Forks:  25-30
```

### 200 Servers
```
CPU:    24-32 cores
RAM:    64-96 GB
Swap:   32 GB
Disk:   2-4 TB
Forks:  40-50
```

**Consider:**
- Multiple Diaken instances (load balancing)
- Dedicated database server
- Distributed task queue (Celery + Redis)
- Ansible Tower/AWX for enterprise scale

---

## Summary

### For 50 Servers - Recommended Specs:

```
┌─────────────────────────────────────────┐
│  CPU:     8-12 cores (16-24 threads)    │
│  RAM:     24-32 GB                      │
│  Swap:    16 GB                         │
│  Disk:    500 GB - 1 TB SSD             │
│  Network: 1 Gbps                        │
│  Forks:   10-20                         │
└─────────────────────────────────────────┘
```

**This configuration will:**
- ✅ Handle 50 servers comfortably
- ✅ Execute playbooks in 15-25 minutes
- ✅ Support concurrent operations
- ✅ Provide room for growth
- ✅ Maintain system stability

**Cost-Performance Sweet Spot:**
- 8 cores, 24 GB RAM, 500 GB SSD
- Can scale to 75 servers
- Good balance of cost and performance
