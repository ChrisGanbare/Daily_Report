import json
import os
import traceback

from cryptography.fernet import Fernet


class ConfigHandler:
    """配置文件处理类"""

    def __init__(self, config_dir=None):
        """
        初始化配置处理器

        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config文件夹
        """
        if config_dir is None:
            # 默认使用项目根目录下的config文件夹
            self.config_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config"
            )
        else:
            self.config_dir = config_dir
        print(f"ConfigHandler初始化，配置目录: {self.config_dir}")

    def load_encrypted_config(self, config_path=None):
        """
        加载加密的配置文件

        Args:
            config_path: 配置文件路径，默认为config/query_config_encrypted.json

        Returns:
            dict: 解密后的配置信息
        """
        if config_path is None:
            config_path = os.path.join(self.config_dir, "query_config_encrypted.json")

        print(f"尝试读取加密配置文件: {config_path}")

        # 检查配置文件是否存在
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"加密配置文件不存在: {config_path}")

        # 读取加密密钥
        key_path = os.path.join(self.config_dir, ".env")
        print(f"尝试读取密钥文件: {key_path}")

        if not os.path.exists(key_path):
            raise FileNotFoundError(f"密钥文件不存在: {key_path}")

        try:
            with open(key_path, "rb") as key_file:
                key = key_file.read()
                print(f"成功读取密钥文件，密钥长度: {len(key)} 字节")
        except Exception as e:
            print(f"读取密钥文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception(f"读取密钥文件失败: {e}")

        # 创建加密器
        try:
            fernet = Fernet(key)
            print("成功创建加密器")
        except Exception as e:
            print(f"创建加密器失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception(f"创建加密器失败: {e}")

        # 读取并解密配置文件
        try:
            with open(config_path, "rb") as encrypted_file:
                encrypted_data = encrypted_file.read()
                print(f"成功读取加密配置文件，数据长度: {len(encrypted_data)} 字节")
        except Exception as e:
            print(f"读取加密配置文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception(f"读取加密配置文件失败: {e}")

        # 解密数据
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
            print(f"成功解密配置文件，解密后数据长度: {len(decrypted_data)} 字节")
        except Exception as e:
            print(f"解密配置文件失败，请检查密钥是否正确: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception(f"解密配置文件失败，请检查密钥是否正确: {e}")

        # 打印解密后的内容长度（可选，出于安全考虑不打印完整内容）
        print(f"成功解密配置文件，内容长度: {len(decrypted_data)} 字节")

        # 解析JSON
        try:
            config_str = decrypted_data.decode("utf-8")
            print(f"解密数据转字符串成功，字符串长度: {len(config_str)} 字节")
            config = json.loads(config_str)
        except Exception as e:
            print(f"解析解密后的配置文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception(f"解析解密后的配置文件失败: {e}")

        print(f"成功解析配置文件，包含 {len(config)} 个配置项")
        # 打印配置项名称（不打印敏感信息）
        if isinstance(config, dict):
            print(f"配置项: {list(config.keys())}")
            if 'db_config' in config:
                db_config = config['db_config']
                if isinstance(db_config, dict):
                    print(f"数据库配置项: {list(db_config.keys())}")
        return config

    def create_encrypted_config(self, config_data, output_path=None):
        """
        创建加密的配置文件

        Args:
            config_data: 要加密的配置数据
            output_path: 输出文件路径，默认为config/query_config_encrypted.json
        """
        if output_path is None:
            output_path = os.path.join(self.config_dir, "query_config_encrypted.json")

        # 读取加密密钥
        key_path = os.path.join(self.config_dir, ".env")
        with open(key_path, "rb") as key_file:
            key = key_file.read()

        # 创建加密器
        fernet = Fernet(key)

        # 将配置数据转换为JSON字符串
        config_json = json.dumps(config_data, ensure_ascii=False, indent=2)

        # 加密数据
        encrypted_data = fernet.encrypt(config_json.encode("utf-8"))

        # 写入加密文件
        with open(output_path, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)

    def load_plain_config(self, config_path=None):
        """
        加载明文配置文件

        Args:
            config_path: 配置文件路径，默认为config/query_config.json

        Returns:
            dict: 配置信息
        """
        if config_path is None:
            config_path = os.path.join(self.config_dir, "query_config.json")

        print(f"尝试读取明文配置文件: {config_path}")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            print(f"成功加载明文配置文件，包含 {len(config)} 个配置项")
            # 打印配置项名称
            if isinstance(config, dict):
                print(f"配置项: {list(config.keys())}")
                if 'db_config' in config:
                    db_config = config['db_config']
                    if isinstance(db_config, dict):
                        print(f"数据库配置项: {list(db_config.keys())}")
            return config
        except Exception as e:
            print(f"加载明文配置文件失败: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise