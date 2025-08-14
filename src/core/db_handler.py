from datetime import date, datetime

import mysql.connector


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

    def connect(self):
        """
        连接到数据库

        Returns:
            mysql.connector.connection.MySQLConnection: 数据库连接对象

        Raises:
            mysql.connector.Error: 数据库连接失败时抛出异常
        """
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            print("数据库连接成功")
            return self.connection
        except mysql.connector.Error as err:
            print(f"数据库连接失败: {err}")
            raise

    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("数据库连接已关闭")

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

            # 使用device_code查询
            cursor.execute(device_query_template, (device_code,))
            result = cursor.fetchone()

            return (result[0], result[1]) if result else None
        except mysql.connector.Error as err:
            print(f"查询设备ID失败: {err}")
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
            cursor = self.connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            # 获取列名
            columns = [desc[0] for desc in cursor.description]
            print(f"  查询返回 {len(results)} 条记录")

            # 处理数据
            data = {}
            for row in results:
                row_dict = dict(zip(columns, row))
                order_time = row_dict.get("加注时间")
                oil_remaining = (
                    row_dict.get("原油剩余比例", 0)
                    if row_dict.get("原油剩余比例") is not None
                    else 0
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

            # 转换为与原来read_inventory_data函数相同的格式
            result = [
                (date, float(record["oil_remaining"]) * 100)
                for date, record in sorted(data.items())
            ]
            print("  库存数据读取完成。")
            return result, columns, results
        except mysql.connector.Error as err:
            print(f"数据库查询失败: {err}")
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
            # 先通过设备ID获取客户ID
            customer_id = self.get_customer_id(device_id)

            if customer_id:
                # 再通过客户ID获取客户名称
                cursor = self.connection.cursor()
                cursor.execute(customer_query_template, (customer_id,))
                customer_result = cursor.fetchone()
                if customer_result and customer_result[0]:
                    return customer_result[0]

            print(f"警告：未找到设备ID {device_id} 对应的客户信息")
            return "未知客户"
        except mysql.connector.Error as err:
            print(f"通过设备ID查询客户名称失败: {err}")
            return "未知客户"
        except Exception as e:
            print(f"查询客户名称时发生未知错误: {e}")
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
            cursor.execute(
                "SELECT customer_id FROM oil.t_device WHERE id = %s", (device_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except mysql.connector.Error as err:
            print(f"查询客户ID失败: {err}")
            return None
        finally:
            if cursor:
                cursor.close()
