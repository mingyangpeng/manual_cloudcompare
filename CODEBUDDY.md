# CODEBUDDY.md

This file provides guidance to CodeBuddy when working with code in this repository.

git信息：
用户名 mingyangpeng
邮箱 8631020892@qq.com

## 项目概述

ManualCloudCompare 是一个基于 Python 3.10 + Open3D 0.19 原生 GUI 的 3D 点云可视化应用，使用 Open3D GUI 替代 Qt。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行主程序
python main.py

# 运行测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_main_window.py -v
```

## 架构设计

### 模块分层

项目采用**三层架构**，基于 Open3D GUI (`o3d.visualization.gui`):

1. **应用层 (UI)**: `src/ui/` - Open3D GUI 组件
   - `main_window.py` ✅ - 主窗口，使用 `o3d.visualization.gui.Window`
   - `db_tree_panel.py` - DB树面板，嵌入主窗口左侧
   - `property_panel.py` - 属性面板，嵌入主窗口
   - `console_panel.py` - 控制台面板，底部可滚动区域

2. **业务层 (Core)**: `src/core/` - 核心服务
   - `cloud_manager.py` - 点云的加载、卸载、状态管理
   - `viewer_service.py` - Open3D Visualizer 封装
   - `event_bus.py` - 模块间事件通信
   - `log_service.py` - 统一日志管理

3. **数据层 (Data)**: `src/data/` - 数据模型
   - `point_cloud.py` - 点云数据结构
   - `transform.py` - 几何变换矩阵

### Open3D GUI 关键 API

```python
# 场景创建
import open3d.visualization.rendering as rendering
scene = rendering.Open3DScene(renderer)

# 布局组件
gui.Vert()       # 垂直布局
gui.ScrollableVert()  # 可滚动垂直布局
gui.VGrid()      # 垂直网格
gui.Horiz()      # 水平布局
gui.CollapsableVert()  # 可折叠面板

# 组件
gui.SceneWidget  # 3D场景
gui.TextEdit     # 文本编辑
gui.Label        # 标签
gui.Checkbox     # 复选框
```

### 依赖关系

- `MainWindow` 使用 `o3d.visualization.gui.Window` + `rendering.Open3DScene`
- `CloudManager` 管理点云，通知 `ViewerService` 更新
- `PropertyPanel` 订阅选择事件显示属性

### 测试策略

- `tests/test_*.py` - 单元测试
- 覆盖率目标: 核心模块 > 80%
