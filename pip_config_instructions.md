# pip 阿里云镜像源配置说明

为了加速 Python 包的安装，建议配置阿里云镜像源。以下是配置方法：

## 方法一：临时使用（单次安装）

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 方法二：全局配置（推荐）

### Windows 系统：

1. 在用户目录下创建 pip 配置目录：
   - 按 `Win + R` 打开运行对话框
   - 输入 `%APPDATA%` 并回车
   - 在打开的目录中创建 `pip` 文件夹

2. 在 `pip` 文件夹中创建 `pip.ini` 文件，内容如下：
   ```ini
   [global]
   index-url = https://mirrors.aliyun.com/pypi/simple/
   
   [install]
   trusted-host = mirrors.aliyun.com
   ```

### Linux/macOS 系统：

1. 在用户主目录下创建 `.pip` 目录：
   ```bash
   mkdir ~/.pip
   ```

2. 在 `~/.pip` 目录中创建 `pip.conf` 文件，内容如下：
   ```ini
   [global]
   index-url = https://mirrors.aliyun.com/pypi/simple/
   
   [install]
   trusted-host = mirrors.aliyun.com
   ```

## 方法三：使用命令配置

```bash
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
pip config set install.trusted-host mirrors.aliyun.com
```

配置完成后，所有 pip 命令都会自动使用阿里云镜像源，大大提高下载速度。