# ✈ World of Airports Bot

自动化脚本，用于在 MuMu 模拟器上自动操作 World of Airports 游戏。

## 功能

- 自动扫描右侧飞机列表，识别需要操作的飞机
- 自动处理起飞流程（推出、滑行、起飞、领取奖励）
- 自动处理降落流程（准许着陆、选择空置停机位、确认）
- 自动处理地勤流程（分配地勤人员、开启机坪代理、指派）
- 随机发呆和随机地图浏览，模拟人类操作避免被检测
- 图形化界面，支持开始/暂停/终止，实时显示详细日志

## 环境要求

- Windows 10/11
- MuMu 模拟器（国际版）已安装并运行
- ADB 已连接模拟器（`172.26.18.222:5555`）
- Python 3.7+（如果从源码运行）

## 依赖安装（源码运行）

```bash
pip install opencv-python pillow numpy pytesseract keyboard
```

还需要安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)，安装后将路径填入 `main.py`。

## 使用方法

### 直接运行 exe（推荐）

1. 下载 `WoA_Bot.exe`
2. 将 `TesseractOCR` 文件夹和 `templates` 文件夹放在与 exe 相同目录
3. 打开 MuMu 模拟器，启动 World of Airports
4. 双击 `WoA_Bot.exe`
5. 点击「开始」按钮

### 从源码运行

```bash
python main.py
```

## 打包成 exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "WoA_Bot" --add-data "templates;templates" --add-data "TesseractOCR;TesseractOCR" main.py
```

## 模板图片

`templates/` 文件夹需要包含以下图片（从游戏截图裁剪）：

| 文件名 | 说明 |
|--------|------|
| `takeoff_icon.png` | 起飞图标（飞机侧面向上） |
| `landing_icon.png` | 降落图标（飞机侧面向下） |
| `maintenance_icon.png` | 地勤/滑行图标（飞机正面） |

运行 `crop_icons.py` 可以交互式裁剪这些图标。

## 注意事项

- 脚本只选择**空置**停机位，付费停机位会自动跳过
- 地勤人员不足时自动跳过，不会强行分配
- 按 `P` 键可以暂停/继续（命令行模式）
- 游戏分辨率需为 1920x1080

## 免责声明

本项目仅供学习交流使用，使用脚本可能违反游戏服务条款，风险自负。
