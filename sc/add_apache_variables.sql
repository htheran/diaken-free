-- Script para agregar variables de Apache para Debian/Ubuntu
-- Ejecutar después de clonar en otro servidor

-- Crear sección Apache Variables si no existe
INSERT IGNORE INTO settings_settingsection (name, description) 
VALUES ('Apache Variables', 'Configuración de Apache para sistemas Debian/Ubuntu');

-- Obtener el ID de la sección
SET @section_id = (SELECT id FROM settings_settingsection WHERE name = 'Apache Variables');

-- Insertar variables
INSERT IGNORE INTO settings_globalsetting (section_id, `key`, value, description, `order`) VALUES
(@section_id, 'debian_apache_user', 'www-data', 'Usuario del servicio Apache en Debian/Ubuntu', 0),
(@section_id, 'debian_apache_group', 'www-data', 'Grupo del servicio Apache en Debian/Ubuntu', 0),
(@section_id, 'debian_server_root', '/opt/www/sites', 'Directorio raíz para sitios web en Debian/Ubuntu', 0),
(@section_id, 'debian_log_root', '/var/log/apache2/sites', 'Directorio de logs de Apache en Debian/Ubuntu', 0),
(@section_id, 'debian_http_port', '80', 'Puerto HTTP para Apache en Debian/Ubuntu', 0);

SELECT 'Variables de Apache agregadas exitosamente' AS resultado;
