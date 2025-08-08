import json
import os
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
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
        else:
            self.config_dir = config_dir

    def load_encrypted_config(self, config_path=None):
        """
        加载加密的配置文件
        
        Args:
            config_path: 配置文件路径，默认为config/query_config_encrypted.json
            
        Returns:
            dict: 解密后的配置信息
        """
        if config_path is None:
            config_path = os.path.join(self.config_dir, 'query_config_encrypted.json')
        
        # 读取加密密钥
        key_path = os.path.join(self.config_dir, '.env')
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
        
        # 创建加密器
        fernet = Fernet(key)
        
        # 读取并解密配置文件
        with open(config_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        
        # 解密数据
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # 解析JSON
        config = json.loads(decrypted_data.decode('utf-8'))
        
        return config

    def create_encrypted_config(self, config_data, output_path=None):
        """
        创建加密的配置文件
        
        Args:
            config_data: 要加密的配置数据
            output_path: 输出文件路径，默认为config/query_config_encrypted.json
        """
        if output_path is None:
            output_path = os.path.join(self.config_dir, 'query_config_encrypted.json')
        
        # 读取加密密钥
        key_path = os.path.join(self.config_dir, '.env')
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
        
        # 创建加密器
        fernet = Fernet(key)
        
        # 将配置数据转换为JSON字符串
        config_json = json.dumps(config_data, ensure_ascii=False, indent=2)
        
        # 加密数据
        encrypted_data = fernet.encrypt(config_json.encode('utf-8'))
        
        # 写入加密文件
        with open(output_path, 'wb') as encrypted_file:
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
            config_path = os.path.join(self.config_dir, 'query_config.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config