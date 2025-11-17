# 客户对账单功能修复分析

## 问题分析

对比原分支 `development-copy` 和当前分支 `feature/optimization-development` 的实现，发现以下关键差异：

### 1. 每日用量明细sheet

**原分支实现**：
- 按 `(device_code, oil_name)` 作为复合键，为每个设备-油品组合创建独立的列
- 从第3列开始，每列对应一个设备-油品组合
- 使用 `oil_columns` 列表保持列的顺序
- 数据来源：`daily_usage_data` 或 `data` 字段，格式是 `[(date, value), ...]`
- 行结构：第一列是年月，第二列是日期（日），第三列开始是各设备-油品组合的用量

**当前实现（错误）**：
- 按日期位置填充（列号 = 2 + 日期）
- 按油品名称和月份分组
- 数据来源：`daily_order_volume` 字段

**问题**：
- 列的组织方式错误：应该按设备-油品组合创建列，而不是按日期位置
- 数据组织方式错误：应该按设备-油品组合组织，而不是按油品-月份组织

### 2. 每月用量对比sheet

**原分支实现**：
- 按 `(device_code, oil_name)` 作为复合键，为每个设备-油品组合创建独立的列
- 从第3列开始，每列对应一个设备-油品组合
- 使用 `oil_columns` 列表保持列的顺序
- 数据来源：`monthly_usage_data` 或 `data` 字段，格式是 `[(date, value), ...]`
- 行结构：第一列是设备编号，第二列是油品名称，第三列开始是各设备-油品组合的月份数据

**当前实现（错误）**：
- 按月份填充（1-12月）
- 按设备-油品-月份组织数据
- 数据来源：`daily_order_volume` 字段

**问题**：
- 列的组织方式错误：应该按设备-油品组合创建列，而不是按月份
- 数据组织方式错误：应该按设备-油品组合组织，而不是按月份组织

### 3. 中润对账单sheet

**原分支实现**：
- 只更新行5的客户名称和月份
- 从行9开始填充数据，最多8行（行9-16）
- 清理行9-16的数据

**当前实现**：
- 基本正确，但需要确认行数限制

## 修复方案

### 1. 重新组织数据

需要将原始数据转换为按设备-油品组合组织的格式：

```python
# 按设备-油品组合组织数据
device_oil_columns = []  # 保持列的顺序
daily_usage_by_column = defaultdict(lambda: defaultdict(float))  # {(device_code, oil_name): {date: value}}

for row in raw_data:
    device_code = row.get('device_code', '')
    oil_name = row.get('oil_name', '未知油品')
    report_date = row.get('report_date')
    order_volume = row.get('daily_order_volume', 0) or 0
    
    key = (device_code, oil_name)
    if key not in device_oil_columns:
        device_oil_columns.append(key)
    
    # 处理日期格式
    if isinstance(report_date, datetime):
        date_key = report_date.date()
    elif isinstance(report_date, str):
        date_key = datetime.strptime(report_date, '%Y-%m-%d').date()
    else:
        date_key = report_date
    
    daily_usage_by_column[key][date_key] += float(order_volume)
```

### 2. 修复每日用量明细sheet

```python
# 从第3列开始，每列对应一个设备-油品组合
for col_idx, (device_code, oil_name) in enumerate(device_oil_columns, start=3):
    # 在行5写入列标题（设备编码-油品名称）
    ws.cell(row=5, column=col_idx).value = f"{device_code}-{oil_name}"
    
    # 填充每日数据
    for row_idx, date in enumerate(date_list, start=6):
        value = daily_usage_by_column[(device_code, oil_name)].get(date, 0.0)
        ws.cell(row=row_idx, column=col_idx).value = value
```

### 3. 修复每月用量对比sheet

```python
# 从第3列开始，每列对应一个设备-油品组合
for col_idx, (device_code, oil_name) in enumerate(device_oil_columns, start=3):
    # 在行6写入列标题（设备编码-油品名称）
    ws.cell(row=6, column=col_idx).value = f"{device_code}-{oil_name}"
    
    # 填充月份数据
    for month_idx, month_key in enumerate(months):
        value = monthly_usage_by_column[(device_code, oil_name)].get(month_key, 0.0)
        ws.cell(row=7 + month_idx, column=col_idx).value = value
```

## 实施步骤

1. ✅ 修改 `_update_daily_detail_sheet` 方法，按设备-油品组合创建列
2. ✅ 修改 `_update_monthly_comparison_sheet` 方法，按设备-油品组合创建列
3. ✅ 确保数据组织方式与原分支一致
4. ⚠️ 测试验证修复效果

## 修复完成

### 修复内容

1. **每日用量明细sheet**：
   - ✅ 改为按 `(device_code, oil_name)` 作为复合键，为每个设备-油品组合创建独立的列
   - ✅ 从第3列开始，每列对应一个设备-油品组合
   - ✅ 使用 `device_oil_columns` 列表保持列的顺序
   - ✅ 在行5写入列标题（设备编码-油品名称）
   - ✅ 行6开始，第一列是年月，第二列是日期（日），第三列开始是各设备-油品组合的每日用量

2. **每月用量对比sheet**：
   - ✅ 改为按 `(device_code, oil_name)` 作为复合键，为每个设备-油品组合创建独立的列
   - ✅ 从第3列开始，每列对应一个设备-油品组合
   - ✅ 使用 `device_oil_columns` 列表保持列的顺序
   - ✅ 在行6写入列标题（设备编码-油品名称）
   - ✅ 行7开始，每行对应一个月份（1-12月），第二列是月份标签，第三列开始是各设备-油品组合的月份用量

### 关键变更

**每日用量明细**：
- 修复前：按日期位置填充（列号 = 2 + 日期）
- 修复后：按设备-油品组合创建列，每列对应一个设备-油品组合

**每月用量对比**：
- 修复前：按月份填充（1-12月），每行对应一个设备-油品组合
- 修复后：按设备-油品组合创建列，每行对应一个月份（1-12月）

### 数据组织方式

```python
# 按设备-油品组合组织数据
device_oil_columns = []  # 保持列的顺序
daily_usage_by_column = defaultdict(lambda: defaultdict(float))  # {(device_code, oil_name): {date: value}}
monthly_usage_by_column = defaultdict(lambda: defaultdict(float))  # {(device_code, oil_name): {month: value}}

# 从第3列开始，每列对应一个设备-油品组合
for col_idx, (device_code, oil_name) in enumerate(device_oil_columns, start=3):
    # 写入列标题
    ws.cell(row=5, column=col_idx).value = f"{device_code}-{oil_name}"  # 每日用量明细
    ws.cell(row=6, column=col_idx).value = f"{device_code}-{oil_name}"  # 每月用量对比
    
    # 填充数据
    for date in date_list:
        value = daily_usage_by_column[(device_code, oil_name)].get(date, 0.0)
        ws.cell(row=row_idx, column=col_idx).value = value
```

