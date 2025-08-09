    def get_device_id_by_no(self, device_no, device_query_template, device_query_fallback_template=None):
        """
        根据设备编号查询设备ID和客户ID，优先使用device_code查询，如果未找到则使用device_no查询
        
        Args:
            device_no (str): 设备编号
            device_query_template (str): 优先查询SQL模板（device_code）
            device_query_fallback_template (str): 备用查询SQL模板（device_no）
            
        Returns:
            tuple or None: (设备ID, 客户ID)或None（未找到时）
        """
        cursor = None
        try:
            cursor = self.connection.cursor()
            
            # 优先使用device_code查询
            cursor.execute(device_query_template, (device_no,))
            result = cursor.fetchone()
            
            # 如果通过device_code未找到，且提供了备用查询模板，则使用device_no查询
            if not result and device_query_fallback_template:
                cursor.execute(device_query_fallback_template, (device_no,))
                result = cursor.fetchone()
                
            return (result[0], result[1]) if result else None
        except mysql.connector.Error as err:
            print(f"查询设备ID失败: {err}")
            return None
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
        cursor = None
        try:
            cursor = self.connection.cursor()
            # 先通过设备ID获取客户ID
            cursor.execute("SELECT customer_id FROM oil.t_device WHERE id = %s", (device_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                customer_id = result[0]
                # 再通过客户ID获取客户名称
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
        finally:
            if cursor:
                cursor.close()
