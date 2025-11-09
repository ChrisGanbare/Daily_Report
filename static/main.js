document.addEventListener('DOMContentLoaded', () => {
    // 获取DOM元素
    const deviceList = document.getElementById('device-list');
    const deviceListContainer = document.getElementById('device-list-container');
    const searchCustomer = document.getElementById('search-customer');
    const searchDevice = document.getElementById('search-device');
    const reportTypeSelect = document.getElementById('report-type');
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const generateBtn = document.getElementById('generate-btn');
    const statusMessage = document.getElementById('status-message');
    const loadingSpinner = document.getElementById('loading-spinner');
    const selectAllCheckbox = document.getElementById('select-all-devices');
    const selectedDeviceCountSpan = document.getElementById('selected-device-count');
    
    const requiredElements = [
        { name: 'device-list', element: deviceList },
        { name: 'device-list-container', element: deviceListContainer },
        { name: 'search-customer', element: searchCustomer },
        { name: 'search-device', element: searchDevice },
        { name: 'report-type', element: reportTypeSelect },
        { name: 'start-date', element: startDateInput },
        { name: 'end-date', element: endDateInput },
        { name: 'generate-btn', element: generateBtn },
        { name: 'status-message', element: statusMessage },
        { name: 'loading-spinner', element: loadingSpinner },
        { name: 'select-all-devices', element: selectAllCheckbox },
        { name: 'selected-device-count', element: selectedDeviceCountSpan }
    ];
    
    const missingElements = requiredElements.filter(item => !item.element);
    if (missingElements.length > 0) {
        console.error('缺少必需的DOM元素:', missingElements.map(item => item.name).join(', '));
        alert('页面加载错误：缺少必需的页面元素。请刷新页面重试。');
        return;
    }

    let debounceTimer;

    // --- Functions ---

    const showLoading = (show) => {
        deviceListContainer.classList.toggle('loading', show);
        loadingSpinner.classList.toggle('hidden', !show);
    };

    const setStatus = (message, isError = false) => {
        statusMessage.textContent = message;
        statusMessage.style.color = isError ? '#e74c3c' : '#2ecc71';
    };

    const updateSelectedCount = () => {
        const checkedCheckboxes = deviceList.querySelectorAll('.device-checkbox:checked');
        selectedDeviceCountSpan.textContent = `(已选 ${checkedCheckboxes.length} 台)`;
        
        const allCheckboxes = deviceList.querySelectorAll('.device-checkbox');
        if (allCheckboxes.length > 0 && checkedCheckboxes.length === allCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCheckboxes.length > 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        }
    };

    const fetchDevices = async () => {
        showLoading(true);
        setStatus('');
        
        const customerQuery = searchCustomer.value;
        const deviceQuery = searchDevice.value;
        const url = new URL('/api/devices', window.location.origin);
        if (customerQuery) url.searchParams.append('customer_name', customerQuery);
        if (deviceQuery) url.searchParams.append('device_code', deviceQuery);

        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`服务器错误: ${response.statusText}`);
            const devices = await response.json();
            renderDevices(devices);
        } catch (error) {
            setStatus(`加载设备列表失败: ${error.message}`, true);
            deviceList.innerHTML = '';
        } finally {
            showLoading(false);
            updateSelectedCount();
        }
    };

    const renderDevices = (devices) => {
        const fragment = document.createDocumentFragment();

        if (devices.length === 0) {
            const p = document.createElement('p');
            p.textContent = '未找到匹配的设备。';
            p.style.textAlign = 'center';
            p.style.padding = '20px';
            fragment.appendChild(p);
        } else {
            devices.forEach(device => {
                const item = document.createElement('div');
                item.className = 'device-item';
                item.innerHTML = `
                    <input type="checkbox" class="device-checkbox" value="${device.code}" id="device-${device.code}">
                    <label for="device-${device.code}" style="width:100%; cursor:pointer; display:flex;">
                        <span class="device-name">${device.code}</span>
                        <span class="customer-name">${device.name}</span>
                    </label>
                `;
                fragment.appendChild(item);
            });
        }
        
        deviceList.replaceChildren(fragment);

        deviceList.querySelectorAll('.device-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectedCount);
        });
    };

    const handleGenerateReport = async () => {
        if (!reportTypeSelect || !startDateInput || !endDateInput) {
            setStatus('页面元素加载异常，请刷新页面重试。', true);
            return;
        }
        
        const reportType = reportTypeSelect.value;
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        
        // --- Validation ---
        if (!reportType) {
            setStatus('请选择报表类型。', true);
            return;
        }
        if (!startDate || !endDate) {
            setStatus('请选择开始和结束日期。', true);
            return;
        }
        
        const start = new Date(startDate);
        const end = new Date(endDate);
        if (start > end) {
            setStatus('开始日期不能晚于结束日期。', true);
            return;
        }

        // 新增：每日消耗误差报表日期范围验证
        if (reportType === 'daily_consumption') {
            const monthDiff = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
            if (monthDiff >= 2) {
                setStatus('每日消耗误差报表查询日期跨度不能超过两个月。', true);
                return;
            }
        }

        const selectedCheckboxes = deviceList.querySelectorAll('.device-checkbox:checked');
        if (selectedCheckboxes.length === 0) {
            setStatus('请至少选择一个设备。', true);
            return;
        }

        generateBtn.disabled = true;
        setStatus('正在生成报表，请稍候...');

        const selectedDevices = Array.from(selectedCheckboxes).map(cb => cb.value);

        const requestBody = {
            report_type: reportType,
            devices: selectedDevices,
            start_date: startDate,
            end_date: endDate,
        };

        try {
            const response = await fetch('/api/reports/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '生成失败');
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            let filename = `report.zip`;
            if (contentDisposition) {
                if (contentDisposition.includes('filename*=')) {
                    const utf8Match = contentDisposition.match(/filename\*=['"]?utf-8['"]?['\'\'\s]*([^;\s"]+)/i);
                    if (utf8Match && utf8Match[1]) {
                        filename = decodeURIComponent(utf8Match[1]);
                    }
                } else {
                    const filenameMatch = contentDisposition.match(/filename=['"]?([^;\s"]+)['"]?/i);
                    if (filenameMatch && filenameMatch[1]) {
                        filename = decodeURIComponent(filenameMatch[1]);
                    }
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' && !filename.endsWith('.xlsx')) {
                    filename += '.xlsx';
                } else if (contentType === 'application/zip' && !filename.endsWith('.zip')) {
                    filename += '.zip';
                }
            }

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            setStatus('报表生成成功！已开始下载。');

        } catch (error) {
            setStatus(`生成报表失败: ${error.message}`, true);
        } finally {
            generateBtn.disabled = false;
        }
    };

    // --- Event Listeners ---

    searchCustomer.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchDevices, 300);
    });

    searchDevice.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchDevices, 300);
    });

    generateBtn.addEventListener('click', handleGenerateReport);

    selectAllCheckbox.addEventListener('change', (e) => {
        const checkboxes = deviceList.querySelectorAll('.device-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = e.target.checked;
        });
        updateSelectedCount();
    });

    // --- Initial Load ---
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);
    endDateInput.value = today.toISOString().split('T')[0];
    startDateInput.value = sevenDaysAgo.toISOString().split('T')[0];
    
    fetchDevices();
});
