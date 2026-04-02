# BioAgent 更新日志

## 更新格式

每个更新条目包含：
- 日期
- 更新类型 (新增/修改/修复)
- 更新描述

---

## [新增] 2026-04-02

- 添加更新日志功能 (`core/changelog.py`)
  - 新增 `Changelog` 类管理更新日志
  - 新增 `add_update()` 快捷函数记录更新
  - 新增 `CHANGELOG.md` 文件存储更新历史
- 修改保存逻辑 (`run.py`, `core/agent.py`)
  - 不再每次问答自动保存结果
  - 改为退出时询问用户是否保存
  - 新增 `pending_save` 属性和 `save_pending()` 方法

---
