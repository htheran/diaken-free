from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from security_fixes.credential_encryption import EncryptedCredentialMixin
import logging

logger = logging.getLogger(__name__)

class SettingSection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class GlobalSetting(models.Model):
    section = models.ForeignKey(SettingSection, related_name='settings', on_delete=models.CASCADE, null=True, blank=True)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    def __str__(self):
        return self.key

class DeploymentCredential(EncryptedCredentialMixin, models.Model):
    """Deployment credentials with optional encrypted password"""
    name = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    password = models.TextField(blank=True, null=True)  # Encrypted storage
    ssh_private_key = models.TextField(blank=True, null=True, help_text='Pega la llave privada SSH (opcional si subes archivo)')
    ssh_key_file = models.FileField(upload_to='ssh/', blank=True, null=True, help_text='Sube el archivo de llave SSH (.pem, .key)')
    ssh_key_file_path = models.CharField(max_length=500, blank=True, null=True, help_text='Ruta del archivo de llave SSH en disco')
    description = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        import os
        import stat
        import shutil
        
        # Handle password encryption if password exists
        password_updated = False
        if not self.pk and self.password:  # New credential with password
            plain_password = self.password
            # Save without password first
            temp_password = self.password
            self.password = None
            super().save(*args, **kwargs)
            # Now encrypt and save password
            self.set_encrypted_password(plain_password)
            super().save(update_fields=['password'])
            password_updated = True
            logger.info(f"Created encrypted deployment credential: {self.name}")
        elif self.pk and self.password:  # Existing credential, check if password changed
            try:
                old = DeploymentCredential.objects.get(pk=self.pk)
                if old.password != self.password and not self.password.startswith('gAAAAA'):
                    # Password changed and not encrypted yet
                    plain_password = self.password
                    super().save(*args, **kwargs)
                    self.set_encrypted_password(plain_password)
                    super().save(update_fields=['password'])
                    password_updated = True
                    logger.info(f"Updated encrypted deployment credential: {self.name}")
            except DeploymentCredential.DoesNotExist:
                pass
        
        if not password_updated and not self.pk:
            # First save to get ID
            super().save(*args, **kwargs)
        elif not password_updated:
            super().save(*args, **kwargs)
        
        # Handle SSH key file management
        from django.conf import settings
        key_dir = os.path.join(settings.BASE_DIR, 'media', 'ssh')
        os.makedirs(key_dir, exist_ok=True)
        key_file = os.path.join(key_dir, f'{self.id}.pem')
        
        # Prioridad 1: Archivo subido
        if self.ssh_key_file:
            # Copiar el archivo subido a la ruta final
            source_path = self.ssh_key_file.path
            shutil.copy(source_path, key_file)
            # Permisos 0600
            os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
            # Actualizar la ruta en el modelo
            if self.ssh_key_file_path != key_file:
                self.ssh_key_file_path = key_file
                super().save(update_fields=['ssh_key_file_path'])
        # Prioridad 2: Texto plano pegado
        elif self.ssh_private_key:
            # Normalizar la llave
            key_data = self.ssh_private_key.replace('\r\n', '\n').replace('\r', '\n').strip()
            # Validar formato
            if not (key_data.startswith('-----BEGIN') and ('PRIVATE KEY-----' in key_data)):
                raise ValueError('La llave SSH debe comenzar con -----BEGIN OPENSSH PRIVATE KEY----- o -----BEGIN RSA PRIVATE KEY-----')
            if not (key_data.endswith('-----END OPENSSH PRIVATE KEY-----') or key_data.endswith('-----END RSA PRIVATE KEY-----')):
                raise ValueError('La llave SSH debe terminar con -----END OPENSSH PRIVATE KEY----- o -----END RSA PRIVATE KEY-----')
            if not key_data.endswith('\n'):
                key_data += '\n'
            # Escribir en disco
            with open(key_file, 'w') as f:
                f.write(key_data)
            # Permisos 0600
            os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)
            # Actualizar la ruta en el modelo
            if self.ssh_key_file_path != key_file:
                self.ssh_key_file_path = key_file
                super().save(update_fields=['ssh_key_file_path'])
    
    def get_password(self):
        """Get decrypted password for use in connections"""
        if self.password:
            return self.get_decrypted_password()
        return None
    
    def delete(self, *args, **kwargs):
        # Eliminar el archivo de llave al borrar la credencial
        if self.ssh_key_file_path and os.path.exists(self.ssh_key_file_path):
            import os
            os.remove(self.ssh_key_file_path)
        super().delete(*args, **kwargs)
    
    def __str__(self):
        return self.name

def ssl_certificate_upload_path(instance, filename):
    # Retorna la ruta dinámica según el nombre del certificado
    # Mantiene el nombre original del archivo
    return f'ssl/{instance.name}/{filename}'

class SSLCertificate(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text='Certificate name (e.g., example.com)')
    cert_file = models.FileField(upload_to=ssl_certificate_upload_path, blank=True, null=True, help_text='Certificate file (.crt)')
    key_file = models.FileField(upload_to=ssl_certificate_upload_path, blank=True, null=True, help_text='Private key file (.key)')
    provider_file = models.FileField(upload_to=ssl_certificate_upload_path, blank=True, null=True, help_text='Provider/CA bundle file (.crt)')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'SSL Certificate'
        verbose_name_plural = 'SSL Certificates'
    
    def __str__(self):
        return self.name
    
    def get_cert_filename(self):
        import os
        return os.path.basename(self.cert_file.name) if self.cert_file else None
    
    def get_key_filename(self):
        import os
        return os.path.basename(self.key_file.name) if self.key_file else None
    
    def get_provider_filename(self):
        import os
        return os.path.basename(self.provider_file.name) if self.provider_file else None
    
    def save(self, *args, **kwargs):
        # Crear carpeta con el nombre del certificado
        import os
        from django.conf import settings
        ssl_dir = os.path.join(settings.BASE_DIR, 'media', 'ssl', self.name)
        os.makedirs(ssl_dir, exist_ok=True)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Eliminar archivos físicos al borrar el registro
        import os
        import shutil
        from django.conf import settings
        ssl_dir = os.path.join(settings.BASE_DIR, 'media', 'ssl', self.name)
        if os.path.exists(ssl_dir):
            shutil.rmtree(ssl_dir)
        super().delete(*args, **kwargs)

from django.utils.translation import gettext_lazy as _

class VCenterCredential(EncryptedCredentialMixin, models.Model):
    """vCenter credentials with encrypted password storage"""
    name = models.CharField(max_length=100, default='vCenter', verbose_name=_('Name'), help_text=_('Friendly name to identify this vCenter'))
    host = models.CharField(max_length=255, verbose_name=_('Host'))
    user = models.CharField(max_length=100, verbose_name=_('User'))
    password = models.TextField(verbose_name=_('Password'))  # Changed to TextField for encrypted storage
    ssl_verify = models.BooleanField(default=False, null=True, blank=True, verbose_name=_('SSL Verify'), help_text=_('Check to verify SSL certificate'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    def save(self, *args, **kwargs):
        """Override save to encrypt password"""
        if not self.pk:  # New credential
            plain_password = self.password
            super().save(*args, **kwargs)
            self.set_encrypted_password(plain_password)
            super().save(update_fields=['password'])
            logger.info(f"Created encrypted vCenter credential: {self.name}")
        else:
            # Check if password changed
            try:
                old = VCenterCredential.objects.get(pk=self.pk)
                if old.password != self.password:
                    # Password changed - check if it's already encrypted
                    if not self.password.startswith('gAAAAA'):  # Not encrypted
                        plain_password = self.password
                        super().save(*args, **kwargs)
                        self.set_encrypted_password(plain_password)
                        super().save(update_fields=['password'])
                        logger.info(f"Updated encrypted vCenter credential: {self.name}")
                    else:
                        super().save(*args, **kwargs)
                else:
                    super().save(*args, **kwargs)
            except VCenterCredential.DoesNotExist:
                super().save(*args, **kwargs)
    
    def get_password(self):
        """Get decrypted password for use in connections"""
        return self.get_decrypted_password()
    
    def __str__(self):
        return f"{self.name} ({self.host})"

class WindowsCredential(EncryptedCredentialMixin, models.Model):
    """Windows credentials with encrypted password storage for WinRM connections"""
    
    AUTH_TYPE_CHOICES = [
        ('ntlm', 'NTLM'),
        ('basic', 'Basic'),
        ('credssp', 'CredSSP'),
        ('kerberos', 'Kerberos'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Name"),
        help_text=_("Friendly name to identify these credentials")
    )
    username = models.CharField(
        max_length=200,
        verbose_name=_("Username"),
        help_text=_("Windows username (e.g., Administrator)")
    )
    password = models.TextField(
        verbose_name=_("Password"),
        help_text=_("Windows password (encrypted)")
    )
    domain = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Domain"),
        help_text=_("Active Directory domain (optional)")
    )
    auth_type = models.CharField(
        max_length=20,
        choices=AUTH_TYPE_CHOICES,
        default='ntlm',
        verbose_name=_("Authentication Type"),
        help_text=_("WinRM authentication method")
    )
    use_https = models.BooleanField(
        default=False,
        verbose_name=_("Use HTTPS"),
        help_text=_("Use HTTPS (port 5986) instead of HTTP (port 5985)")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _("Windows Credential")
        verbose_name_plural = _("Windows Credentials")
    
    def save(self, *args, **kwargs):
        """Override save to encrypt password"""
        if not self.pk:  # New credential
            plain_password = self.password
            super().save(*args, **kwargs)
            self.set_encrypted_password(plain_password)
            super().save(update_fields=['password'])
            logger.info(f"Created encrypted Windows credential: {self.name}")
        else:
            # Check if password changed
            try:
                old = WindowsCredential.objects.get(pk=self.pk)
                if old.password != self.password:
                    # Password changed - check if it's already encrypted
                    if not self.password.startswith('gAAAAA'):  # Not encrypted
                        plain_password = self.password
                        super().save(*args, **kwargs)
                        self.set_encrypted_password(plain_password)
                        super().save(update_fields=['password'])
                        logger.info(f"Updated encrypted Windows credential: {self.name}")
                    else:
                        super().save(*args, **kwargs)
                else:
                    super().save(*args, **kwargs)
            except WindowsCredential.DoesNotExist:
                super().save(*args, **kwargs)
    
    def get_password(self):
        """Get decrypted password for use in connections"""
        return self.get_decrypted_password()
    
    def __str__(self):
        return f"{self.name} ({self.username})"
    
    def get_port(self):
        """Retorna el puerto WinRM según el protocolo"""
        return 5986 if self.use_https else 5985
    
    def get_protocol(self):
        """Retorna el protocolo WinRM"""
        return 'https' if self.use_https else 'http'
    
    def get_endpoint(self, host):
        """Retorna el endpoint WinRM completo"""
        return f"{self.get_protocol()}://{host}:{self.get_port()}/wsman"

def ansible_template_upload_path(instance, filename):
    # Retorna la ruta dinámica según el tipo
    return f'j2/{instance.template_type}/{filename}'

class AnsibleTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ('host', 'Host'),
        ('group', 'Group'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    template_type = models.CharField(max_length=10, choices=TEMPLATE_TYPE_CHOICES, default='host')
    file = models.FileField(upload_to=ansible_template_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'name']
        verbose_name = 'Ansible Template'
        verbose_name_plural = 'Ansible Templates'
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    def save(self, *args, **kwargs):
        # La función upload_to ya maneja la ruta correctamente
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Eliminar el archivo físico al borrar el registro
        if self.file:
            import os
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)

# Create your models here.
