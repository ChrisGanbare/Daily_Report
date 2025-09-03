import json
import os
import traceback


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
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ),
                "config",
            )
        else:
            self.config_dir = config_dir
        print(f"ConfigHandler初始化，配置目录: {self.config_dir}")

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
                if "db_config" in config:
                    db_config = config["db_config"]
                    if isinstance(db_config, dict):
                        print(f"数据库配置项: {list(db_config.keys())}")
            return config
        except FileNotFoundError as e:
            error_msg = (
                f"明文配置文件不存在: {config_path}\n"
                f"请检查以下事项：\n"
                f"1. 确保文件 {config_path} 存在\n"
                f"2. 检查文件路径是否正确\n"
                f"3. 确认您有访问该文件的权限"
            )
            print(error_msg)
            raise FileNotFoundError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = (
                f"明文配置文件格式错误，请检查是否为有效的JSON格式: {e}\n"
                f"请检查以下事项：\n"
                f"1. 确认配置文件 {config_path} 是有效的JSON格式\n"
                f"2. 检查是否有语法错误，如缺少引号、括号不匹配等\n"
                f"3. 可以使用在线JSON验证工具检查文件格式"
            )
            print(error_msg)
            raise json.JSONDecodeError(error_msg, e.doc, e.pos) from e
        except Exception as e:
            error_msg = (
                f"加载明文配置文件失败: {e}\n"
                f"请检查以下事项：\n"
                f"1. 确保文件 {config_path} 没有被其他程序占用\n"
                f"2. 检查您是否有读取该文件的权限\n"
                f"3. 确认文件未损坏"
            )
            print(error_msg)
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise Exception(error_msg) from e
