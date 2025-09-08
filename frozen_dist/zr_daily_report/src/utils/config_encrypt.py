import base64
import json
import os

from cryptography.fernet import Fernet


def generate_key():
    """生成加密密钥"""
    return Fernet.generate_key()


def encrypt_config(data):
    """加密配置数据

    Args:
        data (str): 要加密的数据

    Returns:
        str: 加密后的数据
    """
    # 生成密钥
    key = generate_key()

    # 保存密钥
    with open(".env", "wb") as f:
        f.write(key)

    # 加密数据
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()


def decrypt_config(encrypted_data):
    """解密配置数据

    Args:
        encrypted_data (str): 加密的数据

    Returns:
        str: 解密后的数据
    """
    # 读取密钥
    with open(".env", "rb") as f:
        key = f.read()

    # 解密数据
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data.encode())
    return decrypted_data.decode()


if __name__ == "__main__":
    # 示例用法
    pass
