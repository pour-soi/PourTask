# PourTask

**当前验证版本：v1.2.0-beta.1**

PourTask 是一款面向 Windows 的精致、本地优先桌面任务管理器。它采用安静的 Pour-family 界面，并将收件箱、今天、月份、已完成、搜索和设置作为同一个本地任务数据库的筛选视图。

## 当前支持

- 创建、编辑、完成、恢复和删除任务，以及当前会话内的短时撤销
- 保存前即可填写备注、计划日期、截止日期和指定月份的完整新建任务表单
- 美国日期显示与宽容输入、日期日历和指定月份选择器
- 对任务标题和备注进行不区分大小写的搜索
- 导出本地备份，以及经过验证的数据替换导入
- 可选 Windows 系统托盘、开机启动、桌面组件和窗口位置保存
- 导航、搜索、新建、保存、取消和撤销快捷键

PourTask 当前不提供账户、云同步、协作、提醒、重复任务、附件、优先级、标签或 AI 任务规划。

## 运行 Windows 发布版本

1. 从验证版 GitHub Pre-release 下载 `PourTask-v1.2.0-beta.1-Windows-Setup.exe` 或 `PourTask-v1.2.0-beta.1-Windows.zip`。
2. 运行安装程序，或将完整便携 ZIP 解压到一个可写文件夹。
3. 使用便携版本时，在解压后的文件夹中运行 `PourTask.exe`。

请保持完整解压目录，不要仅移动可执行文件而丢下它所需的 `_internal` 运行目录。

由于首个版本没有代码签名，Windows 可能显示“未知发布者”提示。

## 本地数据

PourTask 将可变数据保存在应用目录之外：

- 数据库：`%LOCALAPPDATA%\PourTask\data\pourtask.db`
- 备份：`%LOCALAPPDATA%\PourTask\backups\`
- 设置：`%LOCALAPPDATA%\PourTask\settings.json`
- 日志：`%LOCALAPPDATA%\PourTask\logs\`

更新、移动或删除便携应用目录不会静默删除这些数据。只有在也希望删除任务、设置和备份时，才应手动删除本地数据目录。

## 从源码运行

需要 Python 3.12 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\run_dev.ps1
```

## 运行测试

```powershell
.\scripts\test.ps1
```

完整发布验证还会运行 Python compilation、QML 加载、QML lint、PyInstaller Windows 构建，以及独立便携目录启动检查。

## 构建 Windows 便携包

```powershell
.\scripts\build_windows.ps1
```

当前开发构建会生成：

- `release\PourTask-v1.2.0-beta.1-Windows\`
- `release\PourTask-v1.2.0-beta.1-Windows.zip`
- `release\PourTask-v1.2.0-beta.1-Windows.zip.sha256`
- `release\PourTask-v1.2.0-beta.1-Windows-Setup.exe`
- `release\PourTask-v1.2.0-beta.1-Windows-Setup.exe.sha256`

## 隐私

PourTask 不包含遥测，也不会自动上传日志。日志默认只保留技术诊断信息，不记录完整任务标题或备注。
