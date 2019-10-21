import base64
import hashlib
import os
from Crypto.Cipher import AES
from core.src.services.abstracts import AESCipherServiceAbstract


class AESCipherServiceImpl(AESCipherServiceAbstract):

    def __init__(self, key, iv=None):
        self.bs = 32
        self.key = hashlib.sha256(key).digest()
        self.iv = iv

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = self.iv or os.urandom(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.urlsafe_b64encode(iv + cipher.encrypt(raw)).decode()

    def decrypt(self, enc):
        enc = base64.urlsafe_b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]
