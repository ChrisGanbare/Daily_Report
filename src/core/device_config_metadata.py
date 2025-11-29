"""
设备配置元数据管理器
负责管理设备配置文件的元数据信息（维护时间、维护类型等）
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional, List


class DeviceConfigMetadata:
    """设备配置元数据管理器"""
    
    def __init__(self, meta_file_path=None):
        """
        初始化元数据管理器
        
        Args:
            meta_file_path: 元数据文件路径，默认为test_data/device_config.meta.json
        """
        if meta_file_path is None:
            # 默认元数据文件路径：项目根目录下的test_data/device_config.meta.json
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            meta_file_path = os.path.join(project_root, 'test_data', 'device_config.meta.json')
        
        self.meta_file_path = meta_file_path
        self._metadata_cache: Optional[Dict] = None
    
    def load_metadata(self) -> Optional[Dict]:
        """
        加载元数据
        
        Returns:
            dict: 元数据字典，如果文件不存在或格式错误则返回None
        """
        if self._metadata_cache is not None:
            return self._metadata_cache
        
        if not os.path.exists(self.meta_file_path):
            return None
        
        try:
            with open(self.meta_file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            self._metadata_cache = metadata
            return metadata
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告：无法读取元数据文件 {self.meta_file_path}: {e}")
            return None
    
    def save_metadata(self, maintenance_type: str, description: str = None, config_file_path: str = None, device_count: int = None):
        """
        保存元数据（更新维护时间）
        
        Args:
            maintenance_type: 维护类型（"增加"、"修改"、"删除"）
            description: 维护描述（可选）
            config_file_path: 配置文件路径（可选，用于记录）
            device_count: 设备数量（可选，用于记录）
        """
        # 加载现有元数据
        metadata = self.load_metadata() or {}
        
        # 更新维护信息
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        metadata['last_maintenance_time'] = current_time
        metadata['last_maintenance_type'] = maintenance_type
        
        if config_file_path:
            metadata['config_file_path'] = config_file_path
        
        if device_count is not None:
            metadata['device_count'] = device_count
        
        if description:
            metadata['last_maintenance_description'] = description
        
        # 维护历史记录（保留最近10条）
        if 'maintenance_history' not in metadata:
            metadata['maintenance_history'] = []
        
        history_item = {
            'time': current_time,
            'type': maintenance_type,
            'description': description or f"{maintenance_type}设备配置"
        }
        metadata['maintenance_history'].insert(0, history_item)
        metadata['maintenance_history'] = metadata['maintenance_history'][:10]  # 只保留最近10条
        
        # 保存元数据
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.meta_file_path), exist_ok=True)
            
            with open(self.meta_file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 清除缓存
            self._metadata_cache = None
            
            print(f"已更新配置维护记录: {maintenance_type} - {current_time}")
        except IOError as e:
            print(f"警告：无法保存元数据文件 {self.meta_file_path}: {e}")
    
    def get_config_info(self) -> Dict:
        """
        获取配置信息（用于显示）
        
        Returns:
            dict: 配置信息字典
        """
        metadata = self.load_metadata()
        
        info = {
            'last_maintenance_time': None,
            'last_maintenance_type': None,
            'last_maintenance_description': None,
            'device_count': None,
            'config_file_path': None,
        }
        
        if metadata:
            info['last_maintenance_time'] = metadata.get('last_maintenance_time')
            info['last_maintenance_type'] = metadata.get('last_maintenance_type')
            info['last_maintenance_description'] = metadata.get('last_maintenance_description')
            info['device_count'] = metadata.get('device_count')
            info['config_file_path'] = metadata.get('config_file_path')
        
        return info
    
    def clear_cache(self):
        """清除元数据缓存，强制重新加载"""
        self._metadata_cache = None

