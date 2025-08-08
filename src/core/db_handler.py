import mysql.connector
from datetime import datetime, date


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

    def get_device_id_by_no(self, device_no, device_query_template):
        """
        根据设备编号查询设备ID，如果有多个相同设备编号，则返回create_time最新的记录
        
        Args:
            device_no (str): 设备编号
            device_query_template (str): SQL查询模板
            
        Returns:
            int or None: 设备ID或None（未找到时）
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            # 使用参数化查询防止SQL注入
            cursor.execute(device_query_template, (device_no,))
            result = cursor.fetchone()
            return result[0] if result else None
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
            print(f"查询返回 {len(results)} 条记录")

            # 处理数据
            data = {}
            for row in results:
                row_dict = dict(zip(columns, row))
                order_time = row_dict.get('加注时间')
                oil_remaining = row_dict.get('原油剩余比例', 0) if row_dict.get('原油剩余比例') is not None else 0

                if isinstance(order_time, datetime):
                    order_date = order_time.date()
                    if order_date not in data or order_time > data[order_date]["datetime"]:
                        data[order_date] = {"datetime": order_time, "oil_remaining": float(oil_remaining)}

            # 转换为与原来read_inventory_data函数相同的格式
            result = [(date, float(record["oil_remaining"]) * 100) for date, record in sorted(data.items())]
            print("\n步骤2：库存数据读取完成。")
            return result, columns, results
        except mysql.connector.Error as err:
            print(f"数据库查询失败: {err}")
            raise
        finally:
            if cursor:
                cursor.close()

    def get_customer_name_by_device_code(self, device_code):
        """
        根据设备编号获取客户名称
        
        Args:
            device_code (str): 设备编号
            
        Returns:
            str: 客户名称
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT c.customer_name
            FROM oil.t_device d
            LEFT JOIN oil.t_customer c ON d.customer_id = c.id
            LEFT JOIN (
                SELECT ta.*
                FROM oil.t_oil_type ta
                INNER JOIN (
                    SELECT device_id, max(id) AS id
                    FROM oil.t_oil_type
                    WHERE status=1
                    GROUP BY device_id
                ) tb ON ta.id = tb.id
            ) ot ON d.id = ot.device_id
            LEFT JOIN oil.t_device_oil o ON ot.id = o.oil_type_id
            WHERE d.device_code = %s
            AND d.del_status = 1
            AND o.STATUS = 1
            AND ot.STATUS = 1
            """
            cursor.execute(query, (device_code,))
            result = cursor.fetchone()
            if result and result[0]:
                return result[0]
            else:
                print(f"警告：未找到设备编号 {device_code} 对应的客户信息")
                return "未知客户"
        except mysql.connector.Error as err:
            print(f"通过设备编号查询客户名称失败: {err}")
            print(f"可能的原因：")
            print("1. 数据库连接异常")
            print("2. t_device、t_customer表不存在或表结构不正确")
            print("3. 设备编号不存在")
            print("4. 数据库权限不足")
            print("5. 设备与客户之间没有建立关联关系")
            return "未知客户"
        except Exception as e:
            print(f"查询客户名称时发生未知错误: {e}")
            return "未知客户"
        finally:
            if cursor:
                cursor.close()

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
            cursor.execute("SELECT customer_id FROM oil.t_device WHERE id = %s", (device_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except mysql.connector.Error as err:
            print(f"查询客户ID失败: {err}")
            return None
        finally:
            if cursor:
                cursor.close()