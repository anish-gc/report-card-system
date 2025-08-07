import base64
import hashlib
import os
from typing import Union, Optional

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


class AESCipherException(Exception):
    """Custom exception for AESCipher errors."""
    pass


class AESCipher:
    """
    Secure AES encryption/decryption implementation with proper padding and error handling.
    Uses AES-256-CBC mode with proper initialization vectors.
    """
    
    def __init__(self, key: str, block_size: int = AES.block_size):
        """
        Initialize the AESCipher with a key.
        
        Args:
            key: The encryption key (will be hashed to create a proper-length AES key)
            block_size: The AES block size (default is 16 bytes)
            
        Raises:
            ValueError: If key is empty or block_size is invalid
        """
        if not key:
            raise ValueError("Encryption key cannot be empty")
        
        if not isinstance(block_size, int) or block_size <= 0:
            raise ValueError(f"Invalid block size: {block_size}")
            
        self.block_size = block_size
        # SHA-256 produces a 32-byte key (256 bits) suitable for AES-256
        self.key = hashlib.sha256(key.encode('utf-8')).digest()
    
    def encrypt(self, raw_data: Union[str, bytes]) -> bytes:
        """
        Encrypt data using AES-CBC mode with a random initialization vector.
        
        Args:
            raw_data: The data to encrypt (string or bytes)
            
        Returns:
            Base64-encoded encrypted data with IV prepended
            
        Raises:
            AESCipherException: If encryption fails
            TypeError: If input type is not supported
        """
        try:
            # Convert string to bytes if necessary
            if isinstance(raw_data, str):
                data = raw_data.encode('utf-8')
            elif isinstance(raw_data, bytes):
                data = raw_data
            else:
                raise TypeError(f"Data must be string or bytes, not {type(raw_data)}")
            
            # Generate a random IV (initialization vector)
            iv = get_random_bytes(self.block_size)
            
            # Create AES cipher in CBC mode with the generated IV
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            
            # Pad the data to a multiple of block size and encrypt
            padded_data = pad(data, self.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            
            # Combine IV and encrypted data, then base64 encode
            result = base64.b64encode(iv + encrypted_data)
            return result
            
        except Exception as e:
            raise AESCipherException(f"Encryption failed: {str(e)}") from e
    
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        """
        Decrypt data that was encrypted with AESCipher.encrypt().
        
        Args:
            encrypted_data: The encrypted data (base64 string or bytes)
            
        Returns:
            Decrypted data as a UTF-8 string
            
        Raises:
            AESCipherException: If decryption fails
            TypeError: If input type is not supported
        """
        try:
            # Convert string to bytes if necessary
            if isinstance(encrypted_data, str):
                enc_bytes = encrypted_data.encode('utf-8')
            elif isinstance(encrypted_data, bytes):
                enc_bytes = encrypted_data
            else:
                raise TypeError(f"Encrypted data must be string or bytes, not {type(encrypted_data)}")
            
            # Base64 decode
            enc = base64.b64decode(enc_bytes)
            
            # Extract IV and ciphertext
            if len(enc) <= self.block_size:
                raise AESCipherException("Invalid encrypted data: too short")
                
            iv = enc[:self.block_size]
            ciphertext = enc[self.block_size:]
            
            # Create cipher with extracted IV and decrypt
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            padded_plaintext = cipher.decrypt(ciphertext)
            
            # Unpad and convert to string
            plaintext = unpad(padded_plaintext, self.block_size)
            return plaintext.decode('utf-8')
            
        except ValueError as e:
            raise AESCipherException(f"Decryption padding error: {str(e)}") from e
        except Exception as e:
            raise AESCipherException(f"Decryption failed: {str(e)}") from e
    
    @classmethod
    def generate_key(cls, length: int = 32) -> str:
        """
        Generate a secure random key suitable for AES encryption.
        
        Args:
            length: Length of the key in bytes (default 32 for AES-256)
            
        Returns:
            Base64-encoded random key
        """
        random_bytes = os.urandom(length)
        return base64.b64encode(random_bytes).decode('utf-8')


# Example usage:
# 
# # Generate a secure key (store this securely!)
# secure_key = AESCipher.generate_key()
# 
# # Create cipher with the key
# cipher = AESCipher(secure_key)
# 
# # Encrypt data
# encrypted = cipher.encrypt("Sensitive data")
# 
# # Decrypt data
# decrypted = cipher.decrypt(encrypted)