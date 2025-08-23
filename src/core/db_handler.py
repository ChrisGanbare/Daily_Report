import sys
import traceback
import time
from datetime import date, datetime

# 导入mysql.connector
import mysql.connector
import logging
from typing import List, Tuple, Optional
from mysql.connector import pooling


class DatabaseHandler:
    """数据库处理类，负责所有数据库相关操作"""

    def __init__(self, db_config):
        """
        初始化数据库处理器

        Args:
            db_config (dict): 数据库配置信息
        """
        self.db_config = db_config
        self.connection = None
        self.connection_pool = None
        print(f"DatabaseHandler初始化，数据库配置: {db_config}")
        print("使用的数据库驱动: mysql-connector-python")

    def connect(self):
        """
        连接到数据库

        Returns:
            数据库连接对象

        Raises:
            Exception: 数据库连接失败时抛出异常
        """
        try:
            print(
                f"尝试连接数据库，配置信息: host={self.db_config.get('host')}, "
                f"user={self.db_config.get('user')}, database={self.db_config.get('database')}"
            )

            # 打印Python和数据库驱动版本信息
            print(f"Python版本: {sys.version}")
            print(f"mysql-connector-python版本: {mysql.connector.__version__}")

            # 使用mysql-connector-python
            # 尝试使用连接池方式连接
            pool_config = self.db_config.copy()
            pool_config["pool_name"] = "zr_daily_report_pool"
            pool_config["pool_size"] = 5  # 增加连接池大小
            pool_config["pool_reset_session"] = True

            print("尝试创建连接池...")
            self.connection_pool = pooling.MySQLConnectionPool(**pool_config)
            print("连接池创建成功")

            print("尝试从连接池获取连接...")
            self.connection = self.connection_pool.get_connection()
            print("数据库连接成功")

            return self.connection

        except mysql.connector.Error as err:
            print(f"数据库连接失败 (数据库错误): {err}")
            print(f"错误类型: {type(err)}")
            if hasattr(err, "errno"):
                print(f"错误代码: {err.errno}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise
        except Exception as e:
            print(f"数据库连接过程中发生未知错误 (Exception): {e}")
            print(f"错误类型: {type(e)}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise
        except BaseException as e:
            print(f"数据库连接过程中发生严重错误 (BaseException): {e}")
            print(f"错误类型: {type(e)}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def _ensure_connection(self):
        """
        确保数据库连接有效，如果连接无效则尝试重新连接
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 检查连接是否存在
                if self.connection is None:
                    print("连接不存在，从连接池获取新连接...")
                    self.connection = self.connection_pool.get_connection()
                    return True
                
                # 检查连接是否有效
                if hasattr(self.connection, 'is_connected') and self.connection.is_connected():
                    return True
                else:
                    print("连接已断开，尝试重新连接...")
                    # 关闭旧连接
                    try:
                        self.connection.close()
                    except:
                        pass
                    
                    # 获取新连接
                    self.connection = self.connection_pool.get_connection()
                    return True
                    
            except Exception as e:
                print(f"连接检查失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    raise
        
        return False

    def disconnect(self):
        """关闭数据库连接"""
        try:
            # 检查是否有连接对象
            if not self.connection:
                print("数据库连接已关闭或未连接")
                return

            # 检查连接是否有效
            if hasattr(self.connection, "is_connected"):
                # mysql-connector-python
                try:
                    if self.connection.is_connected():
                        self.connection.close()
                        print("数据库连接已关闭")
                    else:
                        print("数据库连接已关闭或未连接")
                except Exception:
                    # is_connected()可能抛出异常
                    self.connection.close()
                    print("数据库连接已关闭")
            else:
                # 尝试直接调用close方法
                try:
                    self.connection.close()
                    print("数据库连接已关闭")
                except Exception:
                    print("数据库连接已关闭或未连接")
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")

    def get_latest_device_id_and_customer_id(self, device_code, device_query_template):
        """
        根据设备编号查询设备ID和客户ID，使用device_code查询
        如果有多条记录，则选择create_time最新且device_id最大的记录

        Args:
            device_code (str): 设备编号
            device_query_template (str): 查询SQL模板（device_code）

        Returns:
            tuple or None: (设备ID, 客户ID)或None（未找到时）
        """
        cursor = None
        try:
            # 确保连接有效
            self._ensure_connection()
            
            cursor = self.connection.cursor()
            print(f"执行设备信息查询，设备编号: {device_code}")
            
            # 修改查询语句，获取所有匹配的记录并按create_time降序、id降序排列
            # 假设原查询模板类似于: SELECT id, customer_id FROM oil.t_device WHERE device_code = %s
            # 我们需要添加ORDER BY子句来排序
            if "ORDER BY" not in device_query_template.upper():
                # 在WHERE条件后添加排序条件
                if "WHERE" in device_query_template.upper():
                    ordered_query = device_query_template.replace(
                        "WHERE device_code = %s", 
                        "WHERE device_code = %s ORDER BY create_time DESC, id DESC"
                    )
                else:
                    # 如果没有WHERE子句，直接添加ORDER BY
                    ordered_query = device_query_template + " ORDER BY create_time DESC, id DESC"
            else:
                # 如果已经有ORDER BY子句，使用原始查询
                ordered_query = device_query_template
                
            print(f"查询SQL: {ordered_query}")

            # 使用device_code查询
            cursor.execute(ordered_query, (device_code,))
            results = cursor.fetchall()
            
            if results:
                # 选择第一条记录（根据排序规则，这是create_time最新且device_id最大的记录）
                result = results[0]
                print(f"查询结果: {results}")
                print(f"选中的记录: {result}")
                return (result[0], result[1]) if len(result) >= 2 else None
            else:
                print("未找到匹配的设备记录")
                return None
                
        except Exception as e:
            print(f"查询设备信息时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return None
        finally:
            if cursor:
                # 消费所有未读结果以避免"Unread result found"错误
                try:
                    cursor.fetchall()
                except:
                    pass
                cursor.close()

    def get_customer_name_by_device_code(self, device_code):
        """
        根据设备编号获取客户名称

        Args:
            device_code (str): 设设备编号

        Returns:
            str: 客户名称
        """
        try:
            print(f"查询客户名称，设备编号: {device_code}")
            # 先通过设备编号获取设备ID和客户ID
            device_info = self.get_latest_device_id_and_customer_id(
                device_code,
                "SELECT id, customer_id FROM oil.t_device WHERE device_code = %s",
            )

            if device_info:
                _, customer_id = device_info  # 使用下划线表示我们不使用device_id

                # 再通过客户ID获取客户名称
                # 确保连接有效
                self._ensure_connection()
                
                cursor = self.connection.cursor()
                # 定义专用的客户名称查询SQL
                customer_query = (
                    "SELECT customer_name FROM oil.t_customer WHERE id = %s"
                )
                print(f"执行客户名称查询，SQL: {customer_query}, 参数: {customer_id}")
                cursor.execute(customer_query, (customer_id,))
                customer_result = cursor.fetchone()
                print(f"客户名称查询结果: {customer_result}")
                if customer_result and customer_result[0]:
                    return customer_result[0]

            print(f"警告：未找到设备编号 {device_code} 对应的客户信息")
            return "未知客户"
        except Exception as e:
            print(f"查询客户名称时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return "未知客户"

    def _execute_query(self, device_id, query_or_template, start_date=None, end_date=None):
        """
        执行数据库查询的公共方法

        Args:
            device_id (int): 设备ID
            query_or_template (str): SQL查询语句或模板
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期

        Returns:
            tuple: (查询结果列表, 列名列表)
        """
        cursor = None
        try:
            # 确保连接有效
            self._ensure_connection()
            
            # 如果提供了日期参数，则格式化查询模板，否则直接使用查询语句
            if start_date and end_date:
                end_condition = f"{end_date} 23:59:59"
                query = query_or_template.format(
                    device_id=device_id,
                    start_date=start_date,
                    end_condition=end_condition,
                )
            else:
                query = query_or_template

            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            # 获取列名
            try:
                if hasattr(cursor, "description") and cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                else:
                    columns = []
            except (TypeError, AttributeError):
                # 在测试环境中，cursor.description可能是Mock对象
                columns = []
            
            return results, columns
        except Exception as e:
            print(f"执行数据库查询时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def fetch_inventory_data(
        self, device_id, query_or_template, start_date=None, end_date=None
    ):
        """
        从数据库获取库存数据

        Args:
            device_id (int): 设备ID
            query_or_template (str): SQL查询语句或模板
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期

        Returns:
            tuple: (处理后的数据列表, 列名列表, 原始数据列表)
        """
        try:
            print(f"执行库存数据查询，SQL: {query_or_template}")
            results, columns = self._execute_query(device_id, query_or_template, start_date, end_date)
            
            print(f"  查询返回 {len(results)} 条记录")
            print(f"  列名: {columns}")

            # 处理数据
            data = {}
            for i, row in enumerate(results):
                try:
                    row_dict = dict(zip(columns, row))
                    order_time = row_dict.get("加注时间")
                    oil_remaining = (
                        row_dict.get("原油剩余比例", 0)
                        if row_dict.get("原油剩余比例") is not None
                        else 0
                    )

                    oil_name = row_dict.get("油品名称", "未知油品")
                    if i < 5:  # 只打印前5条记录用于调试
                        print(
                            f"    记录 {i+1}: 加注时间={order_time}, 油品名称={oil_name}, 原油剩余比例={oil_remaining}"
                        )

                    if isinstance(order_time, datetime):
                        order_date = order_time.date()
                        if (
                            order_date not in data
                            or order_time > data[order_date]["datetime"]
                        ):
                            data[order_date] = {
                                "datetime": order_time,
                                "oil_remaining": float(oil_remaining),
                            }
                    elif isinstance(order_time, str):
                        # 处理字符串格式的日期
                        parsed_datetime = None
                        # 尝试多种日期格式
                        for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                parsed_datetime = datetime.strptime(order_time, fmt)
                                break
                            except ValueError:
                                continue

                        if parsed_datetime:
                            order_date = parsed_datetime.date()
                            if (
                                order_date not in data
                                or parsed_datetime > data[order_date]["datetime"]
                            ):
                                data[order_date] = {
                                    "datetime": parsed_datetime,
                                    "oil_remaining": float(oil_remaining),
                                }
                        else:
                            print(f"警告：无法解析日期字符串 {order_time}")
                    elif order_time is None:
                        print(f"警告：记录 {i+1} 中加注时间为空")
                    else:
                        print(
                            f"警告：记录 {i+1} 中加注时间类型未知: {type(order_time)}"
                        )

                except Exception as row_e:
                    print(f"处理记录 {i+1} 时发生错误: {row_e}")
                    print(f"详细错误信息:\n{traceback.format_exc()}")
                    continue

            # 转换为与原来read_inventory_data函数相同的格式
            result = [
                (date, float(record["oil_remaining"]) * 100)
                for date, record in sorted(data.items())
            ]
            print("  库存数据读取完成。")
            return result, columns, results
        except Exception as e:
            print(f"获取库存数据时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def fetch_daily_usage_data(
        self, device_id, query_or_template, start_date=None, end_date=None
    ):
        """
        从数据库获取每日用量数据，用于对账单生成

        Args:
            device_id (int): 设备ID
            query_or_template (str): SQL查询语句或模板
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期

        Returns:
            tuple: (处理后的数据列表, 列名列表, 原始数据列表)
        """
        cursor = None  # 初始化cursor为None
        try:
            print(f"执行每日用量数据查询，SQL: {query_or_template}")
            results, columns = self._execute_query(device_id, query_or_template, start_date, end_date)
            
            print(f"  查询返回 {len(results)} 条记录")
            print(f"  列名: {columns}")

            # 处理数据
            data = {}
            for i, row in enumerate(results):
                try:
                    row_dict = dict(zip(columns, row))
                    order_time = row_dict.get("加注时间")
                    oil_remaining = (
                        row_dict.get("原油剩余比例", 0)
                        if row_dict.get("原油剩余比例") is not None
                        else 0
                    )
                    
                    # 获取油加注值
                    oil_val = (
                        row_dict.get("油加注값", 0)
                        if row_dict.get("油加注값") is not None
                        else 0
                    )

                    if i < 5:  # 只打印前5条记录用于调试
                        print(
                            f"    记录 {i+1}: 加注时间={order_time}, 油品名称={row_dict.get('油品名称', '未知油品')}, 油加注값={oil_val},原油剩余比例={oil_remaining}"
                        )

                    if isinstance(order_time, datetime):
                        order_date = order_time.date()
                        if order_date not in data:
                            data[order_date] = {
                                "datetime": order_time,
                                "oil_remaining": float(oil_remaining),
                                "oil_val": float(oil_val),  # 存储正确的油加注값
                            }
                        else:
                            # 累加同一天的油加注值
                            data[order_date]["oil_val"] += float(oil_val)
                    elif isinstance(order_time, str):
                        # 处理字符串格式的日期
                        parsed_datetime = None
                        # 尝试多种日期格式
                        for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                parsed_datetime = datetime.strptime(order_time, fmt)
                                break
                            except ValueError:
                                continue

                        if parsed_datetime:
                            order_date = parsed_datetime.date()
                            if order_date not in data:
                                data[order_date] = {
                                    "datetime": parsed_datetime,
                                    "oil_remaining": float(oil_remaining),
                                    "oil_val": float(oil_val),  # 存储正确的油加注값
                                }
                            else:
                                # 累加同一天的油加注값
                                data[order_date]["oil_val"] += float(oil_val)
                        else:
                            print(f"警告：无法解析日期字符串 {order_time}")
                    elif order_time is None:
                        print(f"警告：记录 {i+1} 中加注时间为空")
                    else:
                        print(
                            f"警告：记录 {i+1} 中加注时间类型未知: {type(order_time)}"
                        )

                except Exception as row_e:
                    print(f"处理记录 {i+1} 时发生错误: {row_e}")
                    print(f"详细错误信息:\n{traceback.format_exc()}")
                    continue

            # 转换为对账单需要的格式，使用正确的油加注值字段
            result = [
                (date, float(record["oil_val"]))  # 使用正确的油加注값字段
                for date, record in sorted(data.items())
            ]
            print("  每日用量数据读取完成。")
            return result, columns, results
        except Exception as e:
            print(f"获取每日用量数据时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise
        finally:
            if cursor:
                # 消费所有未读结果以避免"Unread result found"错误
                try:
                    cursor.fetchall()
                except:
                    pass
                cursor.close()

    def fetch_monthly_usage_data(
        self, device_id, query_or_template, start_date=None, end_date=None
    ):
        """
        从数据库获取每月用量数据，用于对账单生成

        Args:
            device_id (int): 设设备ID
            query_or_template (str): SQL查询语句或模板
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期

        Returns:
            tuple: (处理后的数据列表, 列名列表, 原始数据列表)
        """
        try:
            print(f"执行每月用量数据查询，SQL: {query_or_template}")
            results, columns = self._execute_query(device_id, query_or_template, start_date, end_date)
            
            print(f"  查询返回 {len(results)} 条记录")
            print(f"  列名: {columns}")

            # 处理数据
            data = {}
            for i, row in enumerate(results):
                try:
                    row_dict = dict(zip(columns, row))
                    order_time = row_dict.get("加注时间")
                    oil_remaining = (
                        row_dict.get("原油剩余比例", 0)
                        if row_dict.get("原油剩余比例") is not None
                        else 0
                    )
                    
                    # 获取油加注值
                    oil_val = (
                        row_dict.get("油加注값", 0)
                        if row_dict.get("油加注값") is not None
                        else 0
                    )

                    if i < 5:  # 只打印前5条记录用于调试
                        print(
                            f"    记录 {i+1}: 加注时间={order_time}, 油品名称={row_dict.get('油品名称', '未知油品')}, 油加注값={oil_val},原油剩余比例={oil_remaining}"
                        )

                    if isinstance(order_time, datetime):
                        # 获取订单的月份作为key
                        order_month = order_time.strftime("%Y-%m")
                        if order_month not in data or order_time > data[order_month]["datetime"]:
                            data[order_month] = {
                                "datetime": order_time,
                                "oil_remaining": float(oil_remaining),
                                "oil_val": float(oil_val),  # 存储正确的油加注값
                            }
                    elif isinstance(order_time, str):
                        # 处理字符串格式的日期
                        parsed_datetime = None
                        # 尝试多种日期格式
                        for fmt in ["%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                parsed_datetime = datetime.strptime(order_time, fmt)
                                break
                            except ValueError:
                                continue

                        if parsed_datetime:
                            # 获取订单的月份作为key
                            order_month = parsed_datetime.strftime("%Y-%m")
                            if order_month not in data or parsed_datetime > data[order_month]["datetime"]:
                                data[order_month] = {
                                    "datetime": parsed_datetime,
                                    "oil_remaining": float(oil_remaining),
                                    "oil_val": float(oil_val),  # 存储正确的油加注값
                                }
                        else:
                            print(f"警告：无法解析日期字符串 {order_time}")
                    elif order_time is None:
                        print(f"警告：记录 {i+1} 中加注时间为空")
                    else:
                        print(
                            f"警告：记录 {i+1} 中加注时间类型未知: {type(order_time)}"
                        )

                except Exception as row_e:
                    print(f"处理记录 {i+1} 时发生错误: {row_e}")
                    print(f"详细错误信息:\n{traceback.format_exc()}")
                    continue

            # 转换为对账单需要的格式，使用正确的油加注值字段
            result = [
                (month, float(record["oil_val"]))  # 使用正确的油加注값字段
                for month, record in sorted(data.items())
            ]
            print("  每月用量数据读取完成。")
            return result, columns, results
        except Exception as e:
            print(f"获取每月用量数据时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise

    def get_customer_id(self, device_id):
        """
        根据设备ID获取客户ID

        Args:
            device_id (int): 设备ID

        Returns:
            int or None: 客户ID或None（未找到时）
        """
        cursor = None
        try:
            # 确保连接有效
            self._ensure_connection()
            
            cursor = self.connection.cursor()
            query = "SELECT customer_id FROM oil.t_device WHERE id = %s"
            print(f"执行客户ID查询，SQL: {query}, 参数: {device_id}")
            cursor.execute(query, (device_id,))
            result = cursor.fetchone()
            print(f"客户ID查询结果: {result}")
            return result[0] if result else None
        except Exception as e:
            print(f"查询客户ID时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return None
        finally:
            if cursor:
                cursor.close()