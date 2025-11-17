# 客户对账单实现细节文档

## 实现概述

客户对账单功能已完全重构，使用模板文件生成，包含3个sheet的数据填充。

---

## 一、数据流程

### 1. 数据获取
```python
raw_report_data = await self.device_repo.get_daily_consumption_raw_data(
    device_codes_tuple, start_date_str, end_date_str
)
```

**数据字段**：
- `device_code`: 设备编码
- `oil_name`: 油品名称
- `customer_name`: 客户名称
- `device_name`: 设备名称
- `report_date`: 报告日期
- `daily_order_volume`: 每日订单量（关键字段）

### 2. 数据汇总

**汇总逻辑**：
```python
# 按（设备编码，油品名称）分组
device_oil_data = defaultdict(lambda: {
    'customer_name': '',
    'device_name': '',
    'oil_name': '',
    'total_order_volume': 0.0
})

# 汇总订单量
for row in raw_report_data:
    order_volume = row.get('daily_order_volume', 0) or 0
    device_oil_data[key]['total_order_volume'] += float(order_volume)
```

**关键点**：
- 只汇总 `daily_order_volume`（订单量）
- 不计算库存、加油量等字段
- 按（设备编码，油品名称）分组，因为同一设备可能有多种油品

### 3. 客户分组

```python
customer_groups = defaultdict(list)
for (device_code, oil_name), data in device_oil_data.items():
    customer_name = data['customer_name']
    customer_groups[customer_name].append({
        'device_code': device_code,
        'device_name': data['device_name'],
        'oil_name': data['oil_name'],
        'total_order_volume': data['total_order_volume']
    })
```

---

## 二、Sheet实现细节

### Sheet 1: 中润对账单

**模板结构**：
- 行5: 客户名称、月份
- 行8: 表头（序号、油品名称/型号、设备编码、本月总升数计量（L）、备注）
- 行9开始: 数据行

**实现逻辑**：
```python
# 更新客户名称和月份（行5）
ws.cell(row=5, column=1).value = f"客户名称：{customer_name}"
ws.cell(row=5, column=7).value = f"月份：{month_str}"

# 填充数据行（行9开始）
for idx, device in enumerate(devices, start=1):
    row = 9 + idx - 1
    ws.cell(row=row, column=1).value = idx  # 序号
    ws.cell(row=row, column=2).value = device.get('oil_name')  # 油品名称
    ws.cell(row=row, column=5).value = device.get('device_code')  # 设备编码
    ws.cell(row=row, column=6).value = device.get('total_order_volume')  # 本月总升数计量
```

**数据字段**：
- 序号：自动编号（1, 2, 3...）
- 油品名称/型号：`oil_name`
- 设备编码：`device_code`
- 本月总升数计量（L）：`total_order_volume`（汇总的订单量）
- 备注：可选

---

### Sheet 2: 每日用量明细

**模板结构**：
- 行2-3: 初始日期、结束日期
- 行5: 表头（用油型号、日）
- 行6开始: 数据行

**实现逻辑**：
```python
# 1. 按日期和油品组织数据
daily_data = defaultdict(float)
for row in raw_data:
    date_key = report_date.date()
    oil_name = row.get('oil_name')
    order_volume = row.get('daily_order_volume', 0)
    daily_data[(date_key, oil_name)] += float(order_volume)

# 2. 按油品和月份分组
oil_month_data = defaultdict(lambda: defaultdict(float))
for (date, oil_name), volume in daily_data.items():
    year_month = f"{date.year}-{date.month:02d}"
    oil_month_data[(oil_name, year_month)][date] = volume

# 3. 填充数据
for (oil_name, year_month), date_volumes in sorted(oil_month_data.items()):
    # 第一列：年月（合并单元格）
    ws.cell(row=row_idx, column=1).value = f"{year}年\n{month}月"
    
    # 第二列：日期（日）
    ws.cell(row=row_idx, column=2).value = str(date.day)
    
    # 第三列开始：每日用量（按日期位置）
    day_col = 2 + date.day
    ws.cell(row=row_idx, column=day_col).value = order_volume
```

**数据组织**：
- 按油品名称和月份分组
- 每个油品-月份组合占用多行（按日期数量）
- 第一列显示年月（合并单元格）
- 第二列显示日期（日）
- 第三列开始按日期位置填充用量

**注意事项**：
- 日期列从第3列开始，列号 = 2 + 日期（日）
- 例如：1号在第3列，15号在第17列
- 需要确保列号不超过模板的最大列数

---

### Sheet 3: 每月用量对比

**模板结构**：
- 行1: 截止日期
- 行5: 年份和合计标题
- 行6: 表头（设备编号、油品名称、1月-12月）
- 行7开始: 数据行
- 第15列（O列）：合计（SUM公式）

**实现逻辑**：
```python
# 1. 按设备-油品-月份组织数据
monthly_data = defaultdict(lambda: defaultdict(float))
for row in raw_data:
    device_code = row.get('device_code')
    oil_name = row.get('oil_name')
    month_key = f"{year}-{month:02d}"
    monthly_data[(device_code, oil_name)][month_key] += float(order_volume)

# 2. 填充数据行（从行7开始）
for (device_code, oil_name), month_volumes in monthly_data.items():
    # 设备编号（第1列）
    ws.cell(row=row_idx, column=1).value = device_code
    
    # 油品名称（第2列）
    ws.cell(row=row_idx, column=2).value = oil_name
    
    # 各月份数据（第3-14列，对应1-12月）
    for month_idx, month_key in enumerate(months, start=3):
        volume = month_volumes.get(month_key, 0.0)
        ws.cell(row=row_idx, column=month_idx).value = volume
    
    # 合计列（第15列，使用SUM公式）
    ws.cell(row=row_idx, column=15).value = f"=SUM(C{row_idx}:N{row_idx})"
```

**数据组织**：
- 按设备编码和油品名称分组
- 按月份（1-12月）汇总订单量
- 使用Excel SUM公式计算合计

**月份映射**：
- 第3列（C列）：1月
- 第4列（D列）：2月
- ...
- 第14列（N列）：12月
- 第15列（O列）：合计（SUM公式）

---

## 三、关键实现点

### 1. 数据传递

原始数据需要传递给模板生成方法，以便填充每日用量明细和每月用量对比：

```python
output_path = self._generate_customer_statement_from_template(
    customer_groups, start_date_str, end_date_str, raw_report_data
)
```

### 2. 客户数据筛选

为每个客户筛选相关的原始数据：

```python
customer_device_codes = {d['device_code'] for d in devices}
customer_raw_data = [row for row in raw_report_data 
                   if row.get('device_code') in customer_device_codes]
```

### 3. 日期处理

统一处理多种日期格式：

```python
if isinstance(report_date, datetime):
    date_key = report_date.date()
elif isinstance(report_date, str):
    date_key = datetime.strptime(report_date, '%Y-%m-%d').date()
else:
    date_key = report_date
```

### 4. Excel公式

每月用量对比使用SUM公式：

```python
from openpyxl.utils import get_column_letter
start_col_letter = get_column_letter(3)  # C列
end_col_letter = get_column_letter(14)  # N列
ws.cell(row=row_idx, column=15).value = f"=SUM({start_col_letter}{row_idx}:{end_col_letter}{row_idx})"
```

---

## 四、与原分支的对比

### 原分支实现（错误）

**业务逻辑**：
- 使用期初库存、期末库存、加油量等字段
- 计算实际消耗和误差
- 未使用模板文件

**数据字段**：
- 期初库存、期末库存、加油量、订单量、实际消耗、误差

### 新实现（正确）

**业务逻辑**：
- 只汇总订单量
- 使用模板文件生成
- 包含3个sheet的完整数据

**数据字段**：
- 序号、油品名称/型号、设备编码、本月总升数计量（L）、备注

---

## 五、测试建议

### 1. 功能测试

- [ ] 测试单设备单油品
- [ ] 测试单设备多油品
- [ ] 测试多设备单客户
- [ ] 测试多设备多客户
- [ ] 测试跨月份日期范围

### 2. 数据验证

- [ ] 验证"中润对账单"sheet的数据准确性
- [ ] 验证"每日用量明细"sheet的数据准确性
- [ ] 验证"每月用量对比"sheet的数据准确性
- [ ] 验证合计公式是否正确

### 3. 格式验证

- [ ] 验证Excel文件格式是否正确
- [ ] 验证3个sheet的内容是否完整
- [ ] 验证单元格格式（数字格式、对齐方式等）

---

## 六、已知限制

1. **每日用量明细**：
   - 日期列位置计算基于"列号 = 2 + 日期（日）"
   - 如果日期超过模板的最大列数，可能无法填充
   - 需要根据实际模板结构调整

2. **每月用量对比**：
   - 只显示当前年份的1-12月数据
   - 跨年数据需要特殊处理

3. **多客户处理**：
   - 当前实现为每个客户生成一个文件
   - 如果多个客户，可能需要调整

---

## 七、后续优化建议

1. **性能优化**：
   - 大量设备时，考虑分批处理
   - 优化数据查询和汇总逻辑

2. **功能扩展**：
   - 支持跨年数据
   - 支持自定义日期范围（超过1个月）
   - 支持导出格式选择

3. **错误处理**：
   - 增强数据验证
   - 提供更详细的错误信息
   - 处理边界情况
