from datetime import date, datetime
import traceback
import sys

# 尝试导入mysql.connector，如果失败则使用PyMySQL
try:
    import mysql.connector
    from mysql.connector import pooling
    USE_PYMYSQL = False
    print("使用 mysql-connector-python 作为数据库驱动")
except ImportError:
    try:
        import pymysql
        mysql_connector = pymysql
        USE_PYMYSQL = True
        print("使用 PyMySQL 作为数据库驱动")
    except ImportError:
        raise ImportError("无法导入数据库驱动，请安装 mysql-connector-python 或 PyMySQL")


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
        print(f"使用的数据库驱动: {'PyMySQL' if USE_PYMYSQL else 'mysql-connector-python'}")

    def connect(self):
        """
        连接到数据库

        Returns:
            数据库连接对象

        Raises:
            Exception: 数据库连接失败时抛出异常
        """
        try:
            print(f"尝试连接数据库，配置信息: host={self.db_config.get('host')}, "
                  f"user={self.db_config.get('user')}, database={self.db_config.get('database')}")
            
            # 打印Python和数据库驱动版本信息
            print(f"Python版本: {sys.version}")
            if not USE_PYMYSQL:
                print(f"mysql-connector-python版本: {mysql.connector.__version__}")
            else:
                print(f"PyMySQL版本: {mysql.connector.__version__}")
            
            if not USE_PYMYSQL:
                # 使用mysql-connector-python
                # 尝试使用连接池方式连接
                pool_config = self.db_config.copy()
                pool_config['pool_name'] = 'zr_daily_report_pool'
                pool_config['pool_size'] = 1
                pool_config['pool_reset_session'] = True
                
                print("尝试创建连接池...")
                self.connection_pool = pooling.MySQLConnectionPool(**pool_config)
                print("连接池创建成功")
                
                print("尝试从连接池获取连接...")
                self.connection = self.connection_pool.get_connection()
                print("数据库连接成功")
            else:
                # 使用PyMySQL
                print("尝试直接连接...")
                # PyMySQL不支持pool_reset_session参数
                pymsql_config = self.db_config.copy()
                if 'pool_reset_session' in pymsql_config:
                    del pymsql_config['pool_reset_session']
                    
                self.connection = mysql.connector.connect(**pymsql_config)
                print("数据库连接成功")
            
            return self.connection
            
        except mysql.connector.Error as err:
            print(f"数据库连接失败 (数据库错误): {err}")
            print(f"错误类型: {type(err)}")
            if hasattr(err, 'errno'):
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

    def disconnect(self):
        """关闭数据库连接"""
        try:
            if self.connection and hasattr(self.connection, 'is_connected'):
                if self.connection.is_connected():
                    self.connection.close()
                    print("数据库连接已关闭")
                else:
                    print("数据库连接已关闭或未连接")
            elif self.connection and hasattr(self.connection, 'open'):
                # PyMySQL使用open属性
                if self.connection.open:
                    self.connection.close()
                    print("数据库连接已关闭")
                else:
                    print("数据库连接已关闭或未连接")
            elif self.connection:
                # 尝试直接调用close方法
                self.connection.close()
                print("数据库连接已关闭")
            else:
                print("数据库连接已关闭或未连接")
        except Exception as e:
            print(f"关闭数据库连接时发生错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")

    def get_device_and_customer_info(
        self, device_code, device_query_template
    ):
        """
        根据设备编号查询设备ID和客户ID，使用device_code查询

        Args:
            device_code (str): 设备编号
            device_query_template (str): 查询SQL模板（device_code）

        Returns:
            tuple or None: (设备ID, 客户ID)或None（未找到时）
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            print(f"执行设备信息查询，设备编号: {device_code}")
            print(f"查询SQL模板: {device_query_template}")

            # 使用device_code查询
            cursor.execute(device_query_template, (device_code,))
            result = cursor.fetchone()
            print(f"查询结果: {result}")

            return (result[0], result[1]) if result else None
        except mysql.connector.Error as err:
            print(f"查询设备ID失败: {err}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return None
        except Exception as e:
            print(f"查询设备信息时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return None
        finally:
            if cursor:
                cursor.close()

    def fetch_inventory_data(self, query):
        """
        从数据库获取库存数据

        Args:
            query (str): SQL查询语句

        Returns:
            tuple: (处理后的数据列表, 列名列表, 原始数据列表)
        """
        cursor = None
        try:
            print(f"执行库存数据查询，SQL: {query}")
            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            # 获取列名
            columns = [desc[0] for desc in cursor.description]
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
                    
                    if i < 5:  # 只打印前5条记录用于调试
                        print(f"    记录 {i+1}: 加注时间={order_time}, 原油剩余比例={oil_remaining}")

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
                        print(f"警告：记录 {i+1} 中加注时间类型未知: {type(order_time)}")

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
        except mysql.connector.Error as err:
            print(f"数据库查询失败: {err}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise
        except Exception as e:
            print(f"获取库存数据时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_customer_name_by_device_code(self, device_id, customer_query_template):
        """
        根据设备ID获取客户名称

        Args:
            device_id (int): 设备ID
            customer_query_template (str): 客户查询SQL模板

        Returns:
            str: 客户名称
        """
        try:
            print(f"查询客户名称，设备ID: {device_id}")
            # 先通过设备ID获取客户ID
            customer_id = self.get_customer_id(device_id)

            if customer_id:
                # 再通过客户ID获取客户名称
                cursor = self.connection.cursor()
                print(f"执行客户名称查询，SQL: {customer_query_template}, 参数: {customer_id}")
                cursor.execute(customer_query_template, (customer_id,))
                customer_result = cursor.fetchone()
                print(f"客户名称查询结果: {customer_result}")
                if customer_result and customer_result[0]:
                    return customer_result[0]

            print(f"警告：未找到设备ID {device_id} 对应的客户信息")
            return "未知客户"
        except mysql.connector.Error as err:
            print(f"通过设备ID查询客户名称失败: {err}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return "未知客户"
        except Exception as e:
            print(f"查询客户名称时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return "未知客户"

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
            cursor = self.connection.cursor()
            query = "SELECT customer_id FROM oil.t_device WHERE id = %s"
            print(f"执行客户ID查询，SQL: {query}, 参数: {device_id}")
            cursor.execute(query, (device_id,))
            result = cursor.fetchone()
            print(f"客户ID查询结果: {result}")
            return result[0] if result else None
        except mysql.connector.Error as err:
            print(f"查询客户ID失败: {err}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return None
        except Exception as e:
            print(f"查询客户ID时发生未知错误: {e}")
            print(f"详细错误信息:\n{traceback.format_exc()}")
            return None
        finally:
            if cursor:
                cursor.close()
