# Ansible Forks Explicado

## ¿Qué son los Ansible Forks?

**Ansible Forks** es el número de **conexiones paralelas** que Ansible puede mantener simultáneamente para ejecutar tareas en múltiples servidores al mismo tiempo.

---

## Analogía Simple

Imagina que tienes que pintar 50 casas:

### Sin Forks (1 pintor)
```
Casa 1 → Casa 2 → Casa 3 → ... → Casa 50
Tiempo: 50 horas (1 hora por casa)
```

### Con 5 Forks (5 pintores)
```
Lote 1: Casas 1-5   (simultáneo) → 1 hora
Lote 2: Casas 6-10  (simultáneo) → 1 hora
Lote 3: Casas 11-15 (simultáneo) → 1 hora
...
Lote 10: Casas 46-50 (simultáneo) → 1 hora
Tiempo total: 10 horas
```

### Con 10 Forks (10 pintores)
```
Lote 1: Casas 1-10   (simultáneo) → 1 hora
Lote 2: Casas 11-20  (simultáneo) → 1 hora
...
Lote 5: Casas 41-50  (simultáneo) → 1 hora
Tiempo total: 5 horas
```

---

## Cómo Funciona en Ansible

### Ejemplo: 50 servidores, playbook de 5 minutos

#### Forks = 5 (Default)
```
┌─────────────────────────────────────────┐
│ Lote 1: Servidores 1-5   → 5 minutos   │
│ Lote 2: Servidores 6-10  → 5 minutos   │
│ Lote 3: Servidores 11-15 → 5 minutos   │
│ Lote 4: Servidores 16-20 → 5 minutos   │
│ Lote 5: Servidores 21-25 → 5 minutos   │
│ Lote 6: Servidores 26-30 → 5 minutos   │
│ Lote 7: Servidores 31-35 → 5 minutos   │
│ Lote 8: Servidores 36-40 → 5 minutos   │
│ Lote 9: Servidores 41-45 → 5 minutos   │
│ Lote 10: Servidores 46-50 → 5 minutos  │
└─────────────────────────────────────────┘
Total: 10 lotes × 5 min = 50 minutos
```

#### Forks = 10
```
┌─────────────────────────────────────────┐
│ Lote 1: Servidores 1-10  → 5 minutos   │
│ Lote 2: Servidores 11-20 → 5 minutos   │
│ Lote 3: Servidores 21-30 → 5 minutos   │
│ Lote 4: Servidores 31-40 → 5 minutos   │
│ Lote 5: Servidores 41-50 → 5 minutos   │
└─────────────────────────────────────────┘
Total: 5 lotes × 5 min = 25 minutos
```

#### Forks = 20
```
┌─────────────────────────────────────────┐
│ Lote 1: Servidores 1-20  → 5 minutos   │
│ Lote 2: Servidores 21-40 → 5 minutos   │
│ Lote 3: Servidores 41-50 → 5 minutos   │
└─────────────────────────────────────────┘
Total: 3 lotes × 5 min = 15 minutos
```

---

## Dividir en Grupos de 20 Servidores

### Opción 1: Usar Grupos de Ansible (Recomendado)

Si divides tus 50 servidores en grupos de 20:

```
Grupo 1: 20 servidores
Grupo 2: 20 servidores
Grupo 3: 10 servidores
```

#### Con Forks = 10

**Grupo 1 (20 servidores):**
```
Lote 1: Servidores 1-10  → 5 min
Lote 2: Servidores 11-20 → 5 min
Total: 10 minutos
```

**Grupo 2 (20 servidores):**
```
Lote 1: Servidores 21-30 → 5 min
Lote 2: Servidores 31-40 → 5 min
Total: 10 minutos
```

**Grupo 3 (10 servidores):**
```
Lote 1: Servidores 41-50 → 5 min
Total: 5 minutos
```

**Tiempo total:** 25 minutos (si se ejecutan secuencialmente)

---

### Ventajas de Dividir en Grupos

#### 1. Menor Uso de Recursos
```
50 servidores con forks=10:
- RAM: ~3-4 GB para Ansible
- CPU: 4-6 cores activos

20 servidores con forks=10:
- RAM: ~2-3 GB para Ansible
- CPU: 3-4 cores activos
```

#### 2. Mayor Control
- Puedes ejecutar grupos en diferentes momentos
- Menos riesgo si algo falla
- Más fácil de monitorear

#### 3. Menor Impacto en Red
- Menos conexiones simultáneas
- Menos carga en vCenter
- Más estable

---

## Requisitos de Recursos por Forks

### RAM por Fork

```
Forks    RAM Ansible    RAM Total Recomendada
─────────────────────────────────────────────
5        1-2 GB         16 GB
10       2-3 GB         24 GB
20       4-6 GB         32 GB
30       6-9 GB         48 GB
```

### CPU por Fork

```
Forks    CPU Activos    CPU Total Recomendados
─────────────────────────────────────────────
5        2-3 cores      6 cores
10       4-6 cores      8 cores
20       8-12 cores     12 cores
30       12-18 cores    16 cores
```

---

## Comparación: 50 Servidores vs Grupos de 20

### Escenario A: 50 Servidores Juntos

**Configuración:**
- 50 servidores
- Forks = 10
- RAM: 24 GB
- CPU: 8 cores

**Ejecución:**
```
Lote 1: 10 servidores → 5 min
Lote 2: 10 servidores → 5 min
Lote 3: 10 servidores → 5 min
Lote 4: 10 servidores → 5 min
Lote 5: 10 servidores → 5 min
────────────────────────────────
Total: 25 minutos
```

**Recursos durante ejecución:**
- RAM usada: ~20 GB
- CPU usada: ~6-7 cores
- Conexiones: 10 simultáneas

---

### Escenario B: 3 Grupos de 20, 20, 10

**Configuración:**
- Grupo 1: 20 servidores
- Grupo 2: 20 servidores
- Grupo 3: 10 servidores
- Forks = 10
- RAM: 16 GB (¡menos!)
- CPU: 6 cores (¡menos!)

**Ejecución Grupo 1:**
```
Lote 1: 10 servidores → 5 min
Lote 2: 10 servidores → 5 min
Total: 10 minutos
```

**Ejecución Grupo 2:**
```
Lote 1: 10 servidores → 5 min
Lote 2: 10 servidores → 5 min
Total: 10 minutos
```

**Ejecución Grupo 3:**
```
Lote 1: 10 servidores → 5 min
Total: 5 minutos
```

**Total si se ejecutan secuencialmente:** 25 minutos  
**Total si se ejecutan en paralelo:** 10 minutos (requiere más recursos)

**Recursos durante ejecución (por grupo):**
- RAM usada: ~14 GB
- CPU usada: ~4-5 cores
- Conexiones: 10 simultáneas

---

## Ventajas y Desventajas

### 50 Servidores Juntos

**Ventajas:**
- ✅ Más simple de gestionar
- ✅ Una sola ejecución
- ✅ Mismo tiempo total (si secuencial)

**Desventajas:**
- ❌ Requiere más RAM (24 GB)
- ❌ Requiere más CPU (8 cores)
- ❌ Más difícil de monitorear
- ❌ Mayor riesgo si falla

---

### Grupos de 20

**Ventajas:**
- ✅ Menos RAM requerida (16 GB)
- ✅ Menos CPU requerida (6 cores)
- ✅ Más fácil de monitorear
- ✅ Menor riesgo
- ✅ Puedes ejecutar en diferentes horarios
- ✅ Más control granular

**Desventajas:**
- ❌ Más trabajo de gestión
- ❌ Mismo tiempo total (si secuencial)
- ❌ Necesitas organizar grupos

---

## Recomendación para tu Caso

### Si tienes recursos limitados (16 GB RAM, 6 cores):

**Dividir en grupos de 20 es MEJOR:**

```
┌─────────────────────────────────────────┐
│  Configuración Recomendada:             │
├─────────────────────────────────────────┤
│  CPU:     6 cores                       │
│  RAM:     16 GB                         │
│  Forks:   10                            │
│  Grupos:  3 grupos (20, 20, 10)         │
├─────────────────────────────────────────┤
│  Tiempo por grupo: ~10 minutos          │
│  Tiempo total: 25 minutos (secuencial)  │
│  Uso de RAM: ~14 GB (cómodo)            │
│  Uso de CPU: ~5 cores (cómodo)          │
└─────────────────────────────────────────┘
```

---

### Si tienes buenos recursos (24 GB RAM, 8 cores):

**Puedes ejecutar 50 juntos:**

```
┌─────────────────────────────────────────┐
│  Configuración Recomendada:             │
├─────────────────────────────────────────┤
│  CPU:     8 cores                       │
│  RAM:     24 GB                         │
│  Forks:   10                            │
│  Servidores: 50 juntos                  │
├─────────────────────────────────────────┤
│  Tiempo total: 25 minutos               │
│  Uso de RAM: ~20 GB                     │
│  Uso de CPU: ~7 cores                   │
└─────────────────────────────────────────┘
```

---

## Cómo Configurar Forks

### Método 1: Archivo de Configuración Global

Editar `/etc/ansible/ansible.cfg`:

```ini
[defaults]
forks = 10
```

### Método 2: Variable de Entorno

```bash
export ANSIBLE_FORKS=10
ansible-playbook playbook.yml
```

### Método 3: Línea de Comandos

```bash
ansible-playbook playbook.yml --forks=10
```

---

## Cómo Crear Grupos en Diaken

### En la Interfaz Web:

1. **Ir a Inventory → Groups**
2. **Crear grupos:**
   - Grupo 1: "Production-Batch-1" (20 servidores)
   - Grupo 2: "Production-Batch-2" (20 servidores)
   - Grupo 3: "Production-Batch-3" (10 servidores)

3. **Ejecutar playbook por grupo:**
   - Deploy → Execute Group Playbook
   - Seleccionar grupo
   - Ejecutar

---

## Tabla Comparativa Final

| Aspecto | 50 Juntos | 3 Grupos de 20 |
|---------|-----------|----------------|
| **RAM Requerida** | 24 GB | 16 GB ✅ |
| **CPU Requerida** | 8 cores | 6 cores ✅ |
| **Tiempo Total** | 25 min | 25 min |
| **Control** | Bajo | Alto ✅ |
| **Riesgo** | Alto | Bajo ✅ |
| **Gestión** | Simple ✅ | Más complejo |
| **Monitoreo** | Difícil | Fácil ✅ |
| **Flexibilidad** | Baja | Alta ✅ |

---

## Resumen

### ¿Qué son los Forks?
**Conexiones paralelas de Ansible = Servidores simultáneos**

### ¿Dividir en grupos de 20?
**SÍ, si tienes recursos limitados:**
- Menos RAM (16 GB vs 24 GB)
- Menos CPU (6 cores vs 8 cores)
- Más control y seguridad
- Mismo tiempo total

### Configuración Óptima para Grupos de 20:
```
CPU:   6 cores
RAM:   16 GB
Forks: 10
Tiempo: ~10 min por grupo
```

**¡Dividir en grupos es una excelente estrategia para optimizar recursos!** 🎯
