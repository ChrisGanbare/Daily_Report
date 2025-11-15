# 客户对账单模板格式修复

## 修复日期
2025-01-XX

## 问题描述

之前的客户对账单实现存在以下问题：
1. **业务逻辑错误**：使用了期初库存、期末库存、加油量等字段，但客户对账单业务不需要这些
2. **未使用模板文件**：没有使用指定的模板格式生成对账单
3. **缺少3个sheet**：模板包含3个sheet（中润对账单、每日用量明细、每月用量对比），但实现中未正确使用

## 正确的业务逻辑

根据用户反馈和模板文件分析，客户对账单的正确业务逻辑是：

### 数据字段
- **序号**：自动编号
- **油品名称/型号**：设备的油品名称
- **设备编码**：设备编码
- **本月总升数计量（L）**：订单量（daily_order_volume）的汇总
- **备注**：可选备注信息

### 不需要的字段
- ❌ 期初库存
- ❌ 期末库存
- ❌ 加油量
- ❌ 实际消耗
- ❌ 误差

### 模板结构

模板文件 `template/statement_template.xlsx` 包含3个sheet：

1. **中润对账单**
   - 行5: 客户名称、月份
   - 行8: 表头（序号、油品名称/型号、设备编码、本月总升数计量（L）、备注）
   - 行9开始: 数据行

2. **每日用量明细**
   - 行2-3: 初始日期、结束日期
   - 行5开始: 每日用量数据

3. **每月用量对比**
   - 月度对比数据

## 修复内容

### 1. 重写数据汇总逻辑

**修复前**：
```python
# 错误：计算期初库存、期末库存、加油量等
consumption_data = self._calculate_consumption_for_statement(device_data, barrel_count)
```

**修复后**：
```python
# 正确：只汇总订单量
device_oil_data = defaultdict(lambda: {
    'customer_name': '',
    'device_name': '',
    'oil_name': '',
    'total_order_volume': 0.0
})

for row in raw_report_data:
    order_volume = row.get('daily_order_volume', 0) or 0
    device_oil_data[key]['total_order_volume'] += float(order_volume)
```

### 2. 实现模板文件生成

**新增方法**：
- `_generate_customer_statement_from_template()` - 使用模板文件生成对账单
- `_update_main_statement_sheet()` - 更新"中润对账单"sheet
- `_update_daily_detail_sheet()` - 更新"每日用量明细"sheet
- `_update_monthly_comparison_sheet()` - 更新"每月用量对比"sheet

### 3. 数据分组逻辑

**修复前**：
- 按设备分组，每个设备一条记录

**修复后**：
- 按（设备编码，油品名称）分组
- 汇总每个设备-油品组合的订单量
- 按客户分组设备

## 代码变更

### 主要修改文件
- `src/services/report_service.py`

### 修改的方法
1. `_generate_customer_statement_report()` - 完全重写
2. 新增 `_generate_customer_statement_from_template()` - 模板生成
3. 新增 `_update_main_statement_sheet()` - 更新主sheet
4. 新增 `_update_daily_detail_sheet()` - 更新每日明细sheet
5. 新增 `_update_monthly_comparison_sheet()` - 更新月度对比sheet

### 废弃的方法（保留但不再使用）
- `_calculate_consumption_for_statement()` - 不再需要
- `_generate_customer_statement_excel()` - 已替换为模板版本
- `_setup_customer_statement_sheet()` - 已替换为模板版本
- `_add_notes_to_statement()` - 不再需要
- `_adjust_statement_formatting()` - 模板已包含格式

## 待完成事项

### 1. 每日用量明细sheet ⚠️
- [ ] 实现每日用量数据的填充逻辑
- [ ] 需要根据日期范围填充每日数据

### 2. 每月用量对比sheet ⚠️
- [ ] 实现月度对比数据的填充逻辑
- [ ] 需要根据业务需求填充对比数据

### 3. 测试验证 ⚠️
- [ ] 创建新的测试用例验证模板格式
- [ ] 验证3个sheet的内容是否正确
- [ ] 验证数据汇总逻辑是否正确

## 使用说明

### 生成客户对账单

```python
# 在 ReportService 中
output_path, warnings = await service._generate_customer_statement_report(
    device_codes=['DEV001', 'DEV002'],
    start_date_str='2025-01-01',
    end_date_str='2025-01-31'
)
```

### 数据格式要求

输入数据应包含：
- `device_code`: 设备编码
- `oil_name`: 油品名称
- `customer_name`: 客户名称
- `daily_order_volume`: 每日订单量（用于汇总）

## 验证清单

- [x] 业务逻辑修正（移除期初库存、期末库存等）
- [x] 使用模板文件生成
- [x] 实现"中润对账单"sheet更新
- [ ] 实现"每日用量明细"sheet更新
- [ ] 实现"每月用量对比"sheet更新
- [ ] 测试验证

## 总结

✅ **已完成**：
1. 修正业务逻辑，移除不需要的字段
2. 实现基于模板文件的生成逻辑
3. 实现"中润对账单"sheet的更新

⚠️ **待完成**：
1. 完善"每日用量明细"sheet的数据填充
2. 完善"每月用量对比"sheet的数据填充
3. 创建测试用例验证功能

客户对账单功能已按照正确的业务逻辑和模板格式进行重构，核心功能已实现。
