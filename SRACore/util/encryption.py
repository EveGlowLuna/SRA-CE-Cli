import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path
from SRACore.util.const import AppDataSraDir


def generate_encryption_key() -> bytes:
    """生成一个安全的 32 字节 AES-256 密钥"""
    return AESGCM.generate_key(bit_length=256)

def save_key(key: bytes):
    """保存密钥到文件"""
    filepath = AppDataSraDir / "secret.key"
    key_b64 = base64.b64encode(key).decode('ascii')
    with open(filepath, 'w') as f:
        f.write(key_b64)
    os.chmod(filepath, 0o600)

def get_key():
    """加载密钥"""
    filepath = AppDataSraDir / "secret.key"
    if filepath.exists():
        with open(filepath, 'r') as f:
            key_b64 = f.read()
        return base64.b64decode(key_b64)
    else:
        key = generate_encryption_key()
        save_key(key)
        return key


def encrypt_data(plaintext: str) -> str:
    """
    使用 AES-256-GCM 加密字符串
    :param plaintext: 明文字符串
    :return: Base64 编码的 (nonce + ciphertext + tag)
    """
    key = get_key()
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes for AES-256")

    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce (recommended for GCM)
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, associated_data=None)

    # 拼接: nonce (12B) + ciphertext_with_tag (包含最后16B的认证标签)
    encrypted_data = nonce + ciphertext_with_tag
    return base64.b64encode(encrypted_data).decode("ascii")


def decrypt_data(encrypted_b64: str) -> str:
    """
    解密 AES-256-GCM 加密的数据
    :param encrypted_b64: Base64 编码的加密数据
    :return: 解密后的字符串，失败则返回空字符串
    """
    if not encrypted_b64:
        return ""
    key = get_key()
    try:
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")

        data = base64.b64decode(encrypted_b64)
        if len(data) < 12 + 16:  # 至少 nonce + tag
            return ""

        nonce = data[:12]
        ciphertext_with_tag = data[12:]

        aesgcm = AESGCM(key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data=None)
        return plaintext_bytes.decode("utf-8")

    except:
        return ""



# def win_decryptor(entropy: str = None) -> str:
#     """使用Windows DPAPI解密数据"""
#
#     if entropy == "":
#         return ""
#     try:
#         encrypted_bytes = base64.b64decode(entropy)
#         # 参数说明：加密数据、熵（C# 中为 null）、标志（0 表示当前用户）
#         decrypted_bytes = win32crypt.CryptUnprotectData(
#             encrypted_bytes,
#             None,
#             None,
#             None,
#             0
#         )[1]  # 返回元组，第2个元素是解密后的字节
#         return decrypted_bytes.decode("utf-8")
#
#     except Exception as e:
#         return ""
