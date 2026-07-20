# PourTask

PourTask 是一款安静、离线优先的 Windows 任务管理器，使用 Python、PySide6、Qt Quick 和 SQLite 构建。收件箱、今天、月份、已完成、搜索、逾期和即将到期都是同一个任务数据库的筛选视图。

## 开发

需要 Python 3.12 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\run_dev.ps1
```

使用 `.\scripts\test.ps1` 运行测试，使用 `.\scripts\build_windows.ps1` 构建 Windows 可执行文件。

## 本地数据

- 数据库：`%LOCALAPPDATA%\PourTask\data\pourtask.db`
- 备份：`%LOCALAPPDATA%\PourTask\backups\`
- 设置：`%LOCALAPPDATA%\PourTask\settings.json`
- 日志：`%LOCALAPPDATA%\PourTask\logs\`

卸载应用不会静默删除该文件夹。只有在也要删除任务、设置和备份时，才应手动移除它。

PourTask 没有账户、云服务、遥测或自动日志上传。桌面小组件目前使用安全的独立工具窗口；在发布前，Windows 桌面层附加及“显示桌面”行为仍需原生验证。
