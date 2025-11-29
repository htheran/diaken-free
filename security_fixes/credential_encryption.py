"""
Credential Encryption Utilities for Diaken Project
Provides encryption/decryption for sensitive credentials
"""

from cryptography.fernet import Fernet
import base64
import os
from typing import Optional


class CredentialEncryptor:
    """Handle encryption and decryption of credentials"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryptor with encryption key
        
        Args:
            encryption_key: Base64 encoded encryption key.
                          If None, will try to get from environment variable ENCRYPTION_KEY
        """
        if encryption_key is None:
            encryption_key = os.environ.get('ENCRYPTION_KEY')
            if not encryption_key:
                raise ValueError(
                    "Encryption key not provided. "
                    "Set ENCRYPTION_KEY environment variable or pass explicitly."
                )
        
        # Asegurar que la key tiene el tamaño correcto (32 bytes)
        key_bytes = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        # Pad or truncate to 32 bytes
        key_bytes = key_bytes.ljust(32)[:32]
        # Encode as base64 for Fernet
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            ciphertext: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If decryption fails (invalid token or wrong key)
        """
        if not ciphertext:
            return ""
        
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # Token inválido - probablemente cambió la clave de encriptación
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to decrypt credential: {str(e)}")
            raise ValueError(
                "Failed to decrypt credential. The encryption key may have changed. "
                "Please delete and re-create the credential."
            ) from e
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key
        
        Returns:
            Base64 encoded encryption key
        """
        return Fernet.generate_key().decode()


# Mixin para modelos Django con credenciales encriptadas
class EncryptedCredentialMixin:
    """
    Mixin para agregar encriptación a modelos de Django
    
    Uso:
        class VCenterCredential(EncryptedCredentialMixin, models.Model):
            password = models.TextField()
            
            def save(self, *args, **kwargs):
                if not self.pk:  # Solo en creación
                    plain_password = self.password
                    super().save(*args, **kwargs)
                    self.set_encrypted_password(plain_password)
                    super().save(update_fields=['password'])
                else:
                    super().save(*args, **kwargs)
    """
    
    _encryptor = None
    
    @classmethod
    def get_encryptor(cls):
        """Get or create encryptor instance"""
        if cls._encryptor is None:
            cls._encryptor = CredentialEncryptor()
        return cls._encryptor
    
    def set_encrypted_password(self, password: str):
        """Encrypt and save password"""
        if password:
            encryptor = self.get_encryptor()
            self.password = encryptor.encrypt(password)
    
    def get_decrypted_password(self) -> str:
        """Get decrypted password"""
        if self.password:
            encryptor = self.get_encryptor()
            return encryptor.decrypt(self.password)
        return None


# Script de utilidad para migrar credenciales existentes
def migrate_existing_credentials():
    """
    Migra credenciales existentes de texto plano a encriptado
    
    Ejecutar con:
        python manage.py shell < security_fixes/credential_encryption.py
    """
    import django
    import os
    import sys
    
    # Setup Django
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diaken.settings')
    django.setup()
    
    from settings.models import VCenterCredential, WindowsCredential, DeploymentCredential
    
    encryptor = CredentialEncryptor()
    
    print("🔐 Migrando credenciales a formato encriptado...")
    print("=" * 60)
    
    # Migrar VCenterCredential
    print("\n📍 Migrando VCenterCredential...")
    for cred in VCenterCredential.objects.all():
        if cred.password and not cred.password.startswith('gAAAAA'):  # No está encriptado
            plain_password = cred.password
            cred.password = encryptor.encrypt(plain_password)
            cred.save(update_fields=['password'])
            print(f"  ✓ Encriptado: {cred.name}")
        else:
            print(f"  ⊙ Ya encriptado: {cred.name}")
    
    # Migrar WindowsCredential
    print("\n📍 Migrando WindowsCredential...")
    for cred in WindowsCredential.objects.all():
        if cred.password and not cred.password.startswith('gAAAAA'):
            plain_password = cred.password
            cred.password = encryptor.encrypt(plain_password)
            cred.save(update_fields=['password'])
            print(f"  ✓ Encriptado: {cred.name}")
        else:
            print(f"  ⊙ Ya encriptado: {cred.name}")
    
    # Migrar DeploymentCredential
    print("\n📍 Migrando DeploymentCredential...")
    for cred in DeploymentCredential.objects.all():
        if cred.password and not cred.password.startswith('gAAAAA'):
            plain_password = cred.password
            cred.password = encryptor.encrypt(plain_password)
            cred.save(update_fields=['password'])
            print(f"  ✓ Encriptado: {cred.name}")
        else:
            print(f"  ⊙ Ya encriptado: {cred.name}")
    
    print("\n" + "=" * 60)
    print("✅ Migración completada!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'generate-key':
            # Generar nueva clave
            print("🔑 Generando nueva clave de encriptación...")
            key = CredentialEncryptor.generate_key()
            print(f"\nENCRYPTION_KEY={key}")
            print("\n⚠️  IMPORTANTE: Guarda esta clave de forma segura!")
            print("   Agrégala a tu archivo .env o variables de entorno.")
        
        elif sys.argv[1] == 'test':
            # Test de encriptación
            print("🧪 Testing encriptación/desencriptación...")
            encryptor = CredentialEncryptor()
            
            test_password = "MySecretPassword123!"
            encrypted = encryptor.encrypt(test_password)
            decrypted = encryptor.decrypt(encrypted)
            
            print(f"Original:   {test_password}")
            print(f"Encriptado: {encrypted[:50]}...")
            print(f"Decriptado: {decrypted}")
            print(f"✓ Match: {test_password == decrypted}")
        
        elif sys.argv[1] == 'migrate':
            # Migrar credenciales existentes
            migrate_existing_credentials()
    else:
        print("Uso:")
        print("  python credential_encryption.py generate-key   - Generar nueva clave")
        print("  python credential_encryption.py test          - Probar encriptación")
        print("  python credential_encryption.py migrate       - Migrar credenciales existentes")
