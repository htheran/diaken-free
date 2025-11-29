# 📁 Scripts (sc/)

Directorio con **todos los scripts `.sh`** para instalación, deployment y mantenimiento de Diaken PDN.

## 🐳 Docker

```bash
# Instalar Docker
bash sc/install_docker_oracle_linux.sh

# Usar Docker (archivos en /docker/)
cd docker/
docker compose up -d
```

## 🔧 Instalación

```bash
bash sc/setup_test_server.sh          # Servidor de pruebas
bash sc/deploy_production.sh          # Deployment producción
bash sc/migrate_database.sh           # Migración BD
```

## 🛠️ Mantenimiento

```bash
bash sc/run_scheduler.sh              # Scheduler manual
bash sc/run_scheduler_daemon.sh       # Scheduler daemon
bash sc/cleanup_snapshots.sh          # Limpiar snapshots
bash sc/cleanup_stuck_deployments.sh  # Limpiar deployments
```

## ✅ Validación

```bash
bash sc/compare_servers.sh            # Comparar servidores
bash sc/validate_sync.sh              # Validar sync
```

## 📚 Documentación

Ver carpeta `docker/` para documentación completa (no versionada en git):
- DOCKER_README.md
- DOCKER_SECURITY.md
- DATABASE_*.md
- Etc.
