from django.db import models

# Esta app no requiere modelos propios.
# Usa VCenterCredential de la app settings para obtener configuración de vCenters.
# Los datos de VMs se consultan en tiempo real desde vCenter, no se almacenan en BD.
