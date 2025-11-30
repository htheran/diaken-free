# Plantillas Jinja2 - Diaken

Esta carpeta contiene plantillas Jinja2 para configuración de servicios.

## Estructura de Directorios

```
j2/
├── host/      # Plantillas para hosts individuales
└── group/     # Plantillas para grupos de hosts
```

## Tipos de Plantillas Soportadas

- **Configuración Apache/Httpd:** `.conf.j2`
- **HTML:** `.html.j2`
- **XML:** `.xml.j2`
- **JSON:** `.json.j2`
- **Otros archivos de configuración**

## Uso

Las plantillas Jinja2 se utilizan para generar archivos de configuración dinámicos durante el aprovisionamiento de VMs.

### Variables Disponibles

Las plantillas pueden usar variables como:
- `{{ hostname }}`
- `{{ ip_address }}`
- `{{ domain }}`
- Otras variables definidas en el contexto

## Nota Importante

⚠️ Las plantillas NO se incluyen en el repositorio Git por razones de seguridad.

**¿Por qué?**
- Las plantillas pueden contener configuraciones específicas del entorno
- Pueden incluir información sensible (rutas, dominios, etc.)
- Cada instalación tiene sus propias plantillas personalizadas

**Al clonar el repositorio:**
- ✅ Estructura de directorios completa
- ✅ Este archivo README.md
- ✅ Archivos .gitkeep en cada directorio
- ❌ Plantillas (.j2, .html, .conf, etc.) NO incluidas

**Para agregar plantillas:**
1. Subir plantillas vía interfaz web de Diaken
2. O copiar manualmente a los directorios correspondientes

## Ejemplos de Plantillas

### Apache VirtualHost (virtualhost.conf.j2)
```jinja2
<VirtualHost *:80>
    ServerName {{ hostname }}.{{ domain }}
    DocumentRoot /var/www/{{ hostname }}
    
    <Directory /var/www/{{ hostname }}>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

### Index HTML (index.html.j2)
```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>{{ hostname }}</title>
</head>
<body>
    <h1>Welcome to {{ hostname }}</h1>
    <p>IP: {{ ip_address }}</p>
</body>
</html>
```

## Ubicación de Uso

Las plantillas se utilizan en:
- Playbooks de Ansible
- Scripts de aprovisionamiento
- Configuración automática de servicios
