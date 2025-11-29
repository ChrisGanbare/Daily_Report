"""
设备配置管理器
负责读取和管理设备桶数配置
"""
import os
import csv
from typing import Dict, Optional
from datetime import datetime


class DeviceConfigManager:
    """设备配置管理器，用于读取设备桶数配置"""
    
    def __init__(self, config_file_path=None):
        """
        初始化设备配置管理器
        
        Args:
            config_file_path: 配置文件路径，默认为test_data/device_config.csv
        """
        if config_file_path is None:
            # 默认配置文件路径：项目根目录下的test_data/device_config.csv
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_file_path = os.path.join(project_root, 'test_data', 'device_config.csv')
        
        self.config_file_path = config_file_path
        self._config_cache: Optional[Dict[str, int]] = None
    
    def load_config(self) -> Dict[str, int]:
        """
        加载配置文件
        
        Returns:
            dict: {device_code: barrel_count} 的映射字典
        """
        # 如果已缓存，直接返回
        if self._config_cache is not None:
            return self._config_cache
        
        config_map = {}
        
        # 检查文件是否存在
        if not os.path.exists(self.config_file_path):
            print(f"提示：设备桶数配置文件不存在: {self.config_file_path}")
            print("将使用默认桶数1")
            self._config_cache = config_map
            return config_map
        
        # 尝试读取配置文件
        try:
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
            for encoding in encodings:
                try:
                    with open(self.config_file_path, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        
                        # 检查必要的列
                        if reader.fieldnames is None:
                            print(f"警告：配置文件 {self.config_file_path} 格式错误（无表头）")
                            break
                        
                        # 处理BOM：创建原始fieldname到清理后fieldname的映射
                        original_fieldnames = reader.fieldnames
                        fieldname_map = {}
                        cleaned_fieldnames = []
                        for orig_name in original_fieldnames:
                            cleaned_name = orig_name.strip('\ufeff').strip()
                            fieldname_map[cleaned_name] = orig_name
                            cleaned_fieldnames.append(cleaned_name)
                        
                        if 'device_code' not in cleaned_fieldnames:
                            print(f"警告：配置文件 {self.config_file_path} 缺少 'device_code' 列")
                            break
                        
                        if 'barrel_count' not in cleaned_fieldnames:
                            print(f"警告：配置文件 {self.config_file_path} 缺少 'barrel_count' 列")
                            break
                        
                        # 读取配置数据
                        for row in reader:
                            # 使用映射获取正确的键名（处理BOM情况）
                            device_code_key = fieldname_map.get('device_code', 'device_code')
                            barrel_count_key = fieldname_map.get('barrel_count', 'barrel_count')
                            device_code = row.get(device_code_key, '').strip()
                            barrel_count_str = row.get(barrel_count_key, '').strip()
                            
                            if not device_code:
                                continue
                            
                            # 解析桶数
                            try:
                                barrel_count = int(barrel_count_str) if barrel_count_str else 1
                                if barrel_count < 1:
                                    print(f"警告：设备 {device_code} 的桶数无效（{barrel_count_str}），将使用默认值1")
                                    barrel_count = 1
                                config_map[device_code] = barrel_count
                            except ValueError:
                                print(f"警告：设备 {device_code} 的桶数格式错误（{barrel_count_str}），将使用默认值1")
                                config_map[device_code] = 1
                        
                        # 成功读取，缓存结果
                        self._config_cache = config_map
                        if config_map:
                            print(f"成功加载设备桶数配置，共 {len(config_map)} 个设备")
                        return config_map
                        
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"读取配置文件时出错: {e}")
                    break
            
            # 所有编码都失败
            print(f"警告：无法读取配置文件 {self.config_file_path}，将使用默认桶数1")
            
        except Exception as e:
            print(f"加载设备配置时发生错误: {e}")
            import traceback
            print(traceback.format_exc())
        
        # 缓存空结果
        self._config_cache = config_map
        return config_map
    
    def get_barrel_count(self, device_code: str) -> int:
        """
        根据设备编码获取桶数
        
        Args:
            device_code: 设备编码
            
        Returns:
            int: 桶数，如果未找到则返回1（默认值）
        """
        if not device_code:
            return 1
        
        config_map = self.load_config()
        return config_map.get(device_code, 1)
    
    def clear_cache(self):
        """清除配置缓存，强制重新加载"""
        self._config_cache = None
    
    def get_config_info(self) -> Dict:
        """
        获取配置文件信息（用于显示）
        
        Returns:
            dict: 配置信息字典，包含文件路径、是否存在、设备数量、最后维护时间等
        """
        info = {
            'config_file_path': self.config_file_path,
            'config_file_abspath': os.path.abspath(self.config_file_path),
            'file_exists': os.path.exists(self.config_file_path),
            'file_size': 0,
            'file_mtime': None,
            'device_count': 0,
            'last_maintenance_time': None,
            'last_maintenance_type': None,
            'last_maintenance_description': None,
        }
        
        if info['file_exists']:
            # 获取文件信息
            info['file_size'] = os.path.getsize(self.config_file_path)
            info['file_mtime'] = os.path.getmtime(self.config_file_path)
            
            # 加载配置获取设备数量
            config_map = self.load_config()
            info['device_count'] = len(config_map)
            
            # 尝试从元数据文件获取维护信息
            try:
                from src.core.device_config_metadata import DeviceConfigMetadata
                metadata = DeviceConfigMetadata().load_metadata()
                if metadata:
                    info['last_maintenance_time'] = metadata.get('last_maintenance_time')
                    info['last_maintenance_type'] = metadata.get('last_maintenance_type')
                    info['last_maintenance_description'] = metadata.get('last_maintenance_description')
            except Exception:
                pass  # 如果元数据加载失败，忽略
            
            # 如果元数据中没有维护时间，使用文件修改时间作为备选
            if not info['last_maintenance_time'] and info['file_mtime']:
                info['last_maintenance_time'] = datetime.fromtimestamp(info['file_mtime']).strftime('%Y-%m-%d %H:%M:%S')
        
        return info
    
    def show_config_info(self):
        """
        显示配置文件信息（用户友好格式）
        """
        info = self.get_config_info()
        
        print("\n" + "="*60)
        print("设备桶数配置信息")
        print("="*60)
        
        if info['file_exists']:
            print(f"配置文件位置: {info['config_file_abspath']}")
            print(f"配置设备数量: {info['device_count']}")
            if info['last_maintenance_time']:
                print(f"最近维护时间: {info['last_maintenance_time']}")
                if info['last_maintenance_type']:
                    print(f"维护类型: {info['last_maintenance_type']}")
                if info['last_maintenance_description']:
                    print(f"维护说明: {info['last_maintenance_description']}")
        else:
            print(f"配置文件不存在: {info['config_file_abspath']}")
            print("将使用默认桶数1")
            print("\n提示：如需配置设备桶数，请创建配置文件并添加设备编码和桶数")
            print("配置文件格式：")
            print("  device_code,barrel_count")
            print("  MO24032700700011,2")
            print("  MO24032700700020,3")
        
        print("="*60 + "\n")

