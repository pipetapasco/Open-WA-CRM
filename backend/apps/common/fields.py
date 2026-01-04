from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


class EncryptedTextField(models.TextField):
    """
    Campo de texto que cifra su valor al guardarse en BD y lo descifra al leerse.
    Utiliza Fernet (cifrado simétrico AES).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(settings, 'ENCRYPTION_KEY') or not settings.ENCRYPTION_KEY:
            raise ValueError('ENCRYPTION_KEY missing in settings.')
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    def get_prep_value(self, value):
        """Prepara el valor para guardarlo en la BD (Encriptación)."""
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value

        try:
            encrypted_value = self.fernet.encrypt(value.encode())
            return encrypted_value.decode()
        except Exception as e:
            raise ValueError(f'Error encrypting data: {e}')

    def from_db_value(self, value, expression, connection):
        """Convierte el valor leído de la BD a objeto Python (Desencriptación)."""
        if value is None or value == '':
            return value

        try:
            decrypted_value = self.fernet.decrypt(value.encode())
            return decrypted_value.decode()
        except Exception as e:
            print(f'Warning: Could not decrypt data. Returning raw value. Error: {e}')
            return value
