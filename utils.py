import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad
from base64 import b64decode,b64encode

# Constants for encryption
SECRET_KEY = os.getenv('ENCRYPTION_SECRET_KEY')
SECRET_IV = os.getenv('ENCRYPTION_SECRET_IV')

def encrypt_password(raw_password):
    # Create an AES cipher
    key = SECRET_KEY.encode('utf-8')[:16].ljust(16, b'\0')
    iv = SECRET_IV.encode('utf-8')[:16].ljust(16, b'\0')
    cipher = AES.new(key, AES.MODE_CBC, iv)
   
    # Pad the password and encrypt it
    padded_password = pad(raw_password.encode('utf-8'), AES.block_size)
    encrypted_password = cipher.encrypt(padded_password)
   
    # Return base64 encoded string
    return b64encode(encrypted_password).decode('utf-8')
 
def decrypt_password(encrypted_password):

    # Prepare key and IV
    key = SECRET_KEY.encode('utf-8')[:16].ljust(16, b'\0')
    iv = SECRET_IV.encode('utf-8')[:16].ljust(16, b'\0')
    cipher = AES.new(key, AES.MODE_CBC, iv)
   
    # Decode from base64 and decrypt
    encrypted_bytes = b64decode(encrypted_password)
    decrypted_padded = cipher.decrypt(encrypted_bytes)
   
    # Unpad and return the original password
    return unpad(decrypted_padded, AES.block_size).decode('utf-8')