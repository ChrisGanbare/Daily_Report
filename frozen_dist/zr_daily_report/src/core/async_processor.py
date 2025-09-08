"""
异步处理器
支持大数据量的并发处理，提高系统性能
"""

import asyncio
import logging
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import aiomysql


class AsyncDatabaseHandler:
    """异步数据库处理器"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.pool = None
        self._lock = threading.Lock()

    async def create_pool(self):
        """创建数据库连接池"""
        if self.pool is None:
            with self._lock:
                if self.pool is None:
                    self.pool = await aiomysql.create_pool(
                        host=self.db_config.get("host", "localhost"),
                        port=self.db_config.get("port", 3306),
                        user=self.db_config.get("user"),
                        password=self.db_config.get("password"),
                        db=self.db_config.get("database"),
                        charset="utf8mb4",
                        autocommit=True,
                        maxsize=20,
                        minsize=5,
                    )
        return self.pool

    async def execute_query(
        self, query: str, params: tuple = None
    ) -> List[Dict[str, Any]]:
        """执行异步查询"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                results = await cursor.fetchall()
                return [dict(row) for row in results]

    async def execute_many(
        self, query: str, params_list: List[tuple]
    ) -> List[Dict[str, Any]]:
        """批量执行查询"""
        pool = await self.create_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.executemany(query, params_list)
                results = await cursor.fetchall()
                return [dict(row) for row in results]

    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()


class AsyncFileProcessor:
    """异步文件处理器"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_csv_file(
        self, file_path: str, chunk_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """异步处理CSV文件"""
        loop = asyncio.get_event_loop()

        def read_csv_chunk(start_line: int, end_line: int) -> List[Dict[str, Any]]:
            import csv

            results = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if start_line <= i < end_line:
                        results.append(row)
            return results

        # 获取文件总行数
        total_lines = (
            sum(1 for _ in open(file_path, "r", encoding="utf-8")) - 1
        )  # 减去标题行

        # 分块处理
        tasks = []
        for i in range(0, total_lines, chunk_size):
            end_line = min(i + chunk_size, total_lines)
            task = loop.run_in_executor(self.executor, read_csv_chunk, i, end_line)
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)

        # 合并结果
        all_results = []
        for result in results:
            all_results.extend(result)

        return all_results

    async def process_excel_file(
        self, file_path: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """异步处理Excel文件"""
        loop = asyncio.get_event_loop()

        def read_excel():
            import pandas as pd

            excel_data = pd.read_excel(file_path, sheet_name=None)
            return {
                sheet_name: df.to_dict("records")
                for sheet_name, df in excel_data.items()
            }

        return await loop.run_in_executor(self.executor, read_excel)


class AsyncReportGenerator:
    """异步报表生成器"""

    def __init__(
        self, db_handler: AsyncDatabaseHandler, file_processor: AsyncFileProcessor
    ):
        self.db_handler = db_handler
        self.file_processor = file_processor
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def generate_inventory_reports_async(
        self, devices: List[Dict[str, Any]], output_dir: str
    ) -> List[Dict[str, Any]]:
        """异步生成库存报表"""
        tasks = []

        for device in devices:
            task = self._generate_single_device_report(device, output_dir)
            tasks.append(task)

        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        successful_reports = []
        failed_reports = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_reports.append({"device": devices[i], "error": str(result)})
            else:
                successful_reports.append(result)

        return {
            "successful": successful_reports,
            "failed": failed_reports,
            "total": len(devices),
            "success_count": len(successful_reports),
            "failed_count": len(failed_reports),
        }

    async def _generate_single_device_report(
        self, device: Dict[str, Any], output_dir: str
    ) -> Dict[str, Any]:
        """生成单个设备的报表"""
        try:
            device_code = device["device_code"]
            start_date = device["start_date"]
            end_date = device["end_date"]

            # 异步查询设备数据
            query = """
                SELECT * FROM inventory_data 
                WHERE device_code = %s AND date BETWEEN %s AND %s
                ORDER BY date
            """
            params = (device_code, start_date, end_date)

            data = await self.db_handler.execute_query(query, params)

            if not data:
                return {
                    "device_code": device_code,
                    "status": "no_data",
                    "message": "设备在指定时间范围内没有数据",
                }

            # 异步生成Excel文件
            output_file = f"{output_dir}/{device_code}_inventory_report.xlsx"
            success = await self._generate_excel_async(data, output_file, device_code)

            return {
                "device_code": device_code,
                "status": "success" if success else "failed",
                "output_file": output_file,
                "data_count": len(data),
            }

        except Exception as e:
            return {
                "device_code": device.get("device_code", "unknown"),
                "status": "error",
                "error": str(e),
            }

    async def _generate_excel_async(
        self, data: List[Dict[str, Any]], output_file: str, device_code: str
    ) -> bool:
        """异步生成Excel文件"""
        loop = asyncio.get_event_loop()

        def generate_excel():
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font

                wb = Workbook()
                ws = wb.active
                ws.title = "库存数据"

                # 添加标题
                ws.append(["日期", "库存百分比"])

                # 添加数据
                for row in data:
                    ws.append([row.get("date"), row.get("inventory_percentage", 0)])

                # 保存文件
                wb.save(output_file)
                return True
            except Exception as e:
                logging.error(f"生成Excel文件失败: {e}")
                return False

        return await loop.run_in_executor(self.executor, generate_excel)


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.results: Dict[str, Any] = {}
        self._lock = threading.Lock()

    async def submit_task(self, task_id: str, coro: Callable, *args, **kwargs) -> str:
        """提交异步任务"""
        with self._lock:
            if task_id in self.tasks:
                raise ValueError(f"任务ID {task_id} 已存在")

            task = asyncio.create_task(coro(*args, **kwargs))
            self.tasks[task_id] = task
            return task_id

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        with self._lock:
            if task_id not in self.tasks:
                return {"status": "not_found"}

            task = self.tasks[task_id]

            if task.done():
                if task.exception():
                    return {"status": "failed", "error": str(task.exception())}
                else:
                    result = task.result()
                    self.results[task_id] = result
                    return {"status": "completed", "result": result}
            else:
                return {"status": "running"}

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if not task.done():
                    task.cancel()
                    return True
        return False

    async def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        tasks_status = {}
        for task_id in list(self.tasks.keys()):
            status = await self.get_task_status(task_id)
            tasks_status[task_id] = status
        return tasks_status


# 异步上下文管理器
class AsyncContext:
    """异步上下文管理器"""

    def __init__(self):
        self.db_handler = None
        self.file_processor = None
        self.report_generator = None
        self.task_manager = AsyncTaskManager()

    async def __aenter__(self):
        """进入异步上下文"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文"""
        if self.db_handler:
            await self.db_handler.close()
        if self.file_processor:
            self.file_processor.executor.shutdown(wait=True)


# 使用示例
async def main_async():
    """异步主函数示例"""
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "password",
        "database": "oil",
    }

    async with AsyncContext() as context:
        # 初始化组件
        context.db_handler = AsyncDatabaseHandler(db_config)
        context.file_processor = AsyncFileProcessor()
        context.report_generator = AsyncReportGenerator(
            context.db_handler, context.file_processor
        )

        # 处理设备数据
        devices = [
            {
                "device_code": "DEV001",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
            {
                "device_code": "DEV002",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            },
        ]

        # 异步生成报表
        results = await context.report_generator.generate_inventory_reports_async(
            devices, "./output"
        )

        print(f"成功生成 {results['success_count']} 个报表")
        print(f"失败 {results['failed_count']} 个报表")

        return results
