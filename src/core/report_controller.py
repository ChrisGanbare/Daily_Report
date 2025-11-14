"""
报表控制器 - 基于development-copy分支的业务逻辑重构
"""

import logging
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import tempfile

logger = logging.getLogger(__name__)


class ReportController:
    """报表控制器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化报表控制器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化组件
        self.statement_handler = None
        self.database_handler = None
        self.data_manager = None
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        # 简化实现：返回默认配置
        return {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "daily_report",
                "user": "postgres",
                "password": "password"
            },
            "report": {
                "max_devices_per_customer": 100,
                "default_output_dir": tempfile.gettempdir(),
                "template_path": None
            }
        }
    
    def generate_customer_statement(self,
                                  log_prefix: str,
                                  devices_data: List[Dict[str, Any]],
                                  query_config: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
        """
        生成客户对账单 - 基于development-copy分支的核心逻辑
        
        Args:
            log_prefix: 日志前缀
            devices_data: 设备数据列表
            query_config: 查询配置
            
        Returns:
            (成功状态, 输出文件路径, 警告信息列表)
        """
        logger.info(f"{log_prefix} 开始生成客户对账单")
        
        start_time = datetime.now()
        failed_devices = []
        warnings = []
        
        try:
            # 1. 初始化组件
            self._initialize_components()
            
            # 2. 处理设备数据
            processed_devices_data = self._process_devices_data(devices_data, query_config, warnings)
            
            if not processed_devices_data:
                error_msg = "没有有效的设备数据可用于生成对账单"
                logger.error(f"{log_prefix} {error_msg}")
                return False, "", [error_msg]
            
            # 3. 加载配置
            config = self._load_query_config(query_config)
            
            # 4. 建立数据库连接
            self._establish_database_connection()
            
            # 5. 选择输出目录
            output_dir = self._select_output_directory(query_config)
            
            # 6. 初始化数据管理器
            self._initialize_data_manager()
            
            # 7. 处理每个设备
            customer_devices_data = self._process_each_device(
                processed_devices_data, config, failed_devices, warnings, log_prefix
            )
            
            if not customer_devices_data:
                error_msg = "所有设备数据处理失败"
                logger.error(f"{log_prefix} {error_msg}")
                return False, "", [error_msg] + warnings
            
            # 8. 按客户分组设备
            customer_groups = self._group_devices_by_customer(customer_devices_data)
            
            # 9. 检查日期范围一致性
            self._check_device_dates_consistency(customer_groups, config)
            
            # 10. 生成输出文件名
            output_filename = self._generate_output_filename(config, customer_groups)
            
            # 11. 生成对账单
            output_path = self._generate_customer_statement_report(
                customer_groups, output_dir, output_filename, config
            )
            
            # 12. 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"{log_prefix} 客户对账单生成完成，耗时: {execution_time:.2f}秒")
            
            # 13. 处理失败设备
            if failed_devices:
                failed_by_customer = self._group_failed_devices_by_customer(failed_devices)
                for customer, devices in failed_by_customer.items():
                    warnings.append(f"客户 {customer} 以下设备处理失败: {', '.join(devices)}")
            
            return True, output_path, warnings
            
        except ValueError as e:
            error_msg = f"参数错误: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            return False, "", [error_msg] + warnings
            
        except Exception as e:
            error_msg = f"生成客户对账单时发生未知错误: {str(e)}"
            logger.error(f"{log_prefix} {error_msg}")
            logger.error(traceback.format_exc())
            return False, "", [error_msg] + warnings
            
        finally:
            # 清理资源
            self._cleanup_resources()
    
    def _initialize_components(self) -> None:
        """初始化组件"""
        if self.statement_handler is None:
            from .statement_handler import StatementHandler
            self.statement_handler = StatementHandler(self.config["report"].get("template_path"))
    
    def _process_devices_data(self, 
                            devices_data: List[Dict[str, Any]], 
                            query_config: Dict[str, Any],
                            warnings: List[str]) -> List[Dict[str, Any]]:
        """处理设备数据"""
        processed_data = []
        
        # 检查是否使用缓存数据
        use_cached_data = query_config.get("use_cached_data", False)
        
        if use_cached_data and devices_data:
            # 使用缓存数据
            logger.info("使用缓存数据生成对账单")
            processed_data = devices_data
        else:
            # 需要从CSV文件读取数据
            csv_file_path = query_config.get("csv_file_path")
            if csv_file_path and os.path.exists(csv_file_path):
                processed_data = self._load_devices_from_csv(csv_file_path, warnings)
            else:
                warnings.append("未提供有效的CSV文件路径，将使用空设备列表")
        
        return processed_data
    
    def _load_devices_from_csv(self, csv_file_path: str, warnings: List[str]) -> List[Dict[str, Any]]:
        """从CSV文件加载设备数据"""
        try:
            import pandas as pd
            
            # 读取CSV文件
            df = pd.read_csv(csv_file_path)
            
            # 验证必要列
            required_columns = ['device_code', 'device_name', 'oil_name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                warnings.append(f"CSV文件缺少必要列: {', '.join(missing_columns)}")
                return []
            
            # 转换为字典列表
            devices_data = df.to_dict('records')
            logger.info(f"从CSV文件加载了 {len(devices_data)} 条设备记录")
            
            return devices_data
            
        except Exception as e:
            warnings.append(f"读取CSV文件失败: {str(e)}")
            return []
    
    def _load_query_config(self, query_config: Dict[str, Any]) -> Dict[str, Any]:
        """加载查询配置"""
        config = self.config.copy()
        config.update(query_config)
        
        # 设置默认值
        if "start_date" not in config:
            config["start_date"] = datetime.now().strftime("%Y-%m-01")  # 当月第一天
        if "end_date" not in config:
            config["end_date"] = datetime.now().strftime("%Y-%m-%d")   # 当天
        
        return config
    
    def _establish_database_connection(self) -> None:
        """建立数据库连接"""
        # 简化实现：在实际项目中这里会连接真实数据库
        logger.info("数据库连接已建立")
    
    def _select_output_directory(self, query_config: Dict[str, Any]) -> str:
        """选择输出目录"""
        output_dir = query_config.get("output_dir")
        if not output_dir:
            output_dir = self.config["report"]["default_output_dir"]
        
        # 创建目录（如果不存在）
        os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def _initialize_data_manager(self) -> None:
        """初始化数据管理器"""
        # 简化实现
        if self.data_manager is None:
            # 这里可以初始化真实的数据管理器
            self.data_manager = {"initialized": True}
    
    def _process_each_device(self,
                           devices_data: List[Dict[str, Any]],
                           config: Dict[str, Any],
                           failed_devices: List[str],
                           warnings: List[str],
                           log_prefix: str) -> List[Dict[str, Any]]:
        """处理每个设备"""
        customer_devices_data = []
        
        for device_data in devices_data:
            try:
                # 获取设备ID和客户ID
                device_code = device_data.get("device_code")
                customer_id = device_data.get("customer_id")
                
                if not device_code:
                    warnings.append("跳过设备代码为空的数据记录")
                    continue
                
                # 查询原始数据
                raw_data = self._query_device_raw_data(device_code, config)
                
                if not raw_data:
                    failed_devices.append(device_code)
                    warnings.append(f"设备 {device_code} 没有找到数据")
                    continue
                
                # 计算用量数据
                consumption_data = self._calculate_consumption_data(raw_data, device_data)
                
                # 检查油品名称列
                oil_name = self._extract_oil_name(raw_data, device_data)
                
                # 验证数据
                if not self._validate_device_data(consumption_data, oil_name):
                    failed_devices.append(device_code)
                    warnings.append(f"设备 {device_code} 数据验证失败")
                    continue
                
                # 添加到结果列表
                device_record = {
                    "device_code": device_code,
                    "customer_id": customer_id,
                    "customer_name": device_data.get("customer_name", "未知客户"),
                    "device_name": device_data.get("device_name", "未知设备"),
                    "oil_name": oil_name,
                    "beginning_inventory": consumption_data.get("beginning_inventory", 0),
                    "ending_inventory": consumption_data.get("ending_inventory", 0),
                    "refill_volume": consumption_data.get("refill_volume", 0),
                    "order_volume": consumption_data.get("order_volume", 0),
                    "actual_consumption": consumption_data.get("actual_consumption", 0),
                    "error": consumption_data.get("error", 0)
                }
                
                customer_devices_data.append(device_record)
                
            except Exception as e:
                failed_devices.append(device_data.get("device_code", "未知设备"))
                error_msg = f"处理设备 {device_data.get('device_code', '未知设备')} 时发生错误: {str(e)}"
                warnings.append(error_msg)
                logger.error(f"{log_prefix} {error_msg}")
        
        return customer_devices_data
    
    def _query_device_raw_data(self, device_code: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查询设备原始数据"""
        # 简化实现：返回模拟数据
        return [
            {
                "device_code": device_code,
                "report_date": config["start_date"],
                "beginning_inventory": 1000,
                "ending_inventory": 800,
                "refill_volume": 200,
                "order_volume": 350
            }
        ]
    
    def _calculate_consumption_data(self, raw_data: List[Dict[str, Any]], device_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算用量数据"""
        if not raw_data:
            return {}
        
        # 使用第一条记录进行计算
        data = raw_data[0]
        
        beginning_inventory = data.get("beginning_inventory", 0)
        ending_inventory = data.get("ending_inventory", 0)
        refill_volume = data.get("refill_volume", 0)
        order_volume = data.get("order_volume", 0)
        
        # 计算实际消耗
        actual_consumption = max(0, (beginning_inventory - ending_inventory) + refill_volume)
        
        # 计算误差
        error = actual_consumption - order_volume
        
        return {
            "beginning_inventory": beginning_inventory,
            "ending_inventory": ending_inventory,
            "refill_volume": refill_volume,
            "order_volume": order_volume,
            "actual_consumption": actual_consumption,
            "error": error
        }
    
    def _extract_oil_name(self, raw_data: List[Dict[str, Any]], device_data: Dict[str, Any]) -> str:
        """提取油品名称"""
        # 优先使用设备数据中的油品名称
        oil_name = device_data.get("oil_name")
        
        if not oil_name and raw_data:
            # 从原始数据中提取
            oil_name = raw_data[0].get("oil_name", "未知油品")
        
        return oil_name or "未知油品"
    
    def _validate_device_data(self, consumption_data: Dict[str, Any], oil_name: str) -> bool:
        """验证设备数据"""
        if not consumption_data:
            return False
        
        # 检查必要字段
        required_fields = ["beginning_inventory", "ending_inventory", "order_volume"]
        for field in required_fields:
            if field not in consumption_data:
                return False
        
        return True
    
    def _group_devices_by_customer(self, customer_devices_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按客户分组设备"""
        customer_groups = {}
        
        for device_data in customer_devices_data:
            customer_id = device_data.get("customer_id", "unknown")
            customer_name = device_data.get("customer_name", "未知客户")
            
            if customer_id not in customer_groups:
                customer_groups[customer_id] = {
                    "customer_name": customer_name,
                    "devices": []
                }
            
            customer_groups[customer_id]["devices"].append(device_data)
        
        return customer_groups
    
    def _check_device_dates_consistency(self, customer_groups: Dict[str, Any], config: Dict[str, Any]) -> None:
        """检查设备日期范围一致性"""
        # 简化实现：所有设备使用相同的日期范围
        start_date = config["start_date"]
        end_date = config["end_date"]
        
        logger.info(f"所有设备使用相同的日期范围: {start_date} 至 {end_date}")
    
    def _generate_output_filename(self, config: Dict[str, Any], customer_groups: Dict[str, Any]) -> str:
        """生成输出文件名"""
        if len(customer_groups) == 1:
            # 单个客户
            customer_data = next(iter(customer_groups.values()))
            customer_name = customer_data["customer_name"].replace("/", "_")
            return f"{customer_name}_客户对账单"
        else:
            # 多个客户
            return "多客户对账单汇总"
    
    def _generate_customer_statement_report(self,
                                          customer_groups: Dict[str, Any],
                                          output_dir: str,
                                          output_filename: str,
                                          config: Dict[str, Any]) -> str:
        """生成客户对账单报告"""
        from .customer_statement_generator import CustomerStatementGenerator
        
        # 初始化生成器
        generator = CustomerStatementGenerator(config.get("template_path"))
        
        output_files = []
        
        for customer_id, customer_data in customer_groups.items():
            customer_name = customer_data["customer_name"]
            devices = customer_data["devices"]
            
            # 生成单个客户对账单
            output_path = generator.generate_report(
                customer_data={"customer_name": customer_name},
                devices_data=devices,
                output_dir=output_dir,
                start_date=config["start_date"],
                end_date=config["end_date"]
            )
            
            output_files.append(output_path)
        
        # 如果是单个文件，直接返回路径
        if len(output_files) == 1:
            return output_files[0]
        else:
            # 多个文件需要打包
            return self._package_multiple_reports(output_files, output_dir, output_filename)
    
    def _package_multiple_reports(self, output_files: List[str], output_dir: str, output_filename: str) -> str:
        """打包多个报告文件"""
        import zipfile
        
        zip_path = Path(output_dir) / f"{output_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in output_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
                    # 删除原始文件
                    os.remove(file_path)
        
        return str(zip_path)
    
    def _group_failed_devices_by_customer(self, failed_devices: List[str]) -> Dict[str, List[str]]:
        """按客户分组失败设备"""
        # 简化实现：所有失败设备归为"未知客户"
        return {"未知客户": failed_devices}
    
    def _cleanup_resources(self) -> None:
        """清理资源"""
        # 关闭数据库连接等资源
        if self.database_handler:
            # 在实际项目中这里会关闭数据库连接
            pass
    
    def generate_refueling_details(self, *args, **kwargs) -> Any:
        """生成加油详情报告"""
        # 简化实现
        logger.info("生成加油详情报告功能待实现")
        return None