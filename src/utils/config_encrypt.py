import base64
import json
import os

from cryptography.fernet import Fernet


def generate_key():
    """生成加密密钥"""
    return Fernet.generate_key()


def encrypt_config():
    """加密配置文件"""
    # 读取原始配置
    with open("query_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # 生成密钥
    key = generate_key()

    # 保存密钥
    with open(".env", "wb") as f:
        f.write(key)

    # 加密敏感信息
    fernet = Fernet(key)
    db_config = config["db_config"]
    db_config["password"] = fernet.encrypt(db_config["password"].encode()).decode()

    # 保存加密后的配置
    with open("query_config_encrypted.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


if __name__ == "__main__":
    encrypt_config()
