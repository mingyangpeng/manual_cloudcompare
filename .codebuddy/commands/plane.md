# 点云可视化系统架构设计

## 项目概述
- **项目名称**: ManualCloudCompare
- **技术栈**: Python 3.10 + Open3D + OpenCV + NumPy
- **UI框架**: Open3D 原生 GUI (非 Qt)
- **项目类型**: 桌面级 3D 点云可视化应用

---

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           应用层 (Application Layer)                     │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  主窗口模块  │  │  DB树模块   │  │  属性模块   │  │  控制台模块  │    │
│  │  MainWindow │  │DBTreePanel │  │PropPanel    │  │ConsolePanel │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │           │
├─────────┴────────────────┴────────────────┴────────────────┴───────────┤
│                          事件总线层 (Event Bus Layer)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                           核心业务层 (Core Business Layer)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 点云管理服务 │  │ 可视化服务   │  │ 选择管理   │  │  日志服务   │     │
│  │CloudManager│  │ViewerService│  │SelectionMgr│  │ LogService  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────────────────────┤
│                          数据层 (Data Layer)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │ 点云数据结构 │  │ 几何变换矩阵 │  │ 可视化配置  │                     │
│  │  PointCloud │  │  Transform  │  │  ViewConfig │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
├─────────────────────────────────────────────────────────────────────────┤
│                          依赖层 (Dependency Layer)                       │
│      Open3D GUI      │      OpenCV        │      NumPy                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Open3D GUI 框架说明

### 2.1 核心组件

| 组件 | 类名 | 用途 |
|------|------|------|
| 应用 | `o3d.visualization.gui.Application` | 应用实例管理 |
| 窗口 | `o3d.visualization.gui.Window` | 主窗口容器 |
| 场景控件 | `o3d.visualization.gui.SceneWidget` | 3D渲染区域 |
| 布局容器 | `gui.VGrid` / `gui.HGrid` / `gui.VStack` | 布局管理 |
| 面板 | `gui.Panel` | 可缩放面板 |
| 树形控件 | `gui.TreeCtrl` | DB树显示 |
| 文本编辑 | `gui.TextEdit` | 控制台输出 |
| 标签 | `gui.Label` | 属性显示 |
| 复选框 | `gui.Checkbox` | 可见性控制 |

### 2.2 窗口创建流程

```python
# 标准 Open3D GUI 窗口创建
app = gui.Application.instance
app.initialize()

window = app.create_window("ManualCloudCompare", width, height)
window.add_child(scene_widget)
window.add_child(left_panel)
window.add_child(console_panel)

app.run()
```

---

## 3. 功能模块详细设计

### 模块 1: 主窗口 (MainWindow) ✅ 已实现

**实现文件**: `src/ui/main_window.py`

```
模块: MainWindow
├── 职责: 系统主容器，使用 Open3D Window 管理所有子组件
├── 依赖: o3d.visualization.gui
├── 子组件:
│   ├── SceneWidget (固定大小，3D渲染区域)
│   ├── left_panel (DB树+属性，可缩放)
│   └── bottom_panel (控制台，可缩放)
└── 功能:
    ├── 初始化窗口布局
    ├── 管理组件层级关系
    └── 处理窗口事件 (resize, close)
```

**接口设计:**
```python
class MainWindow:
    def __init__(self, title: str, width: int, height: int)
    def get_scene_widget(self) -> gui.SceneWidget
    def get_left_panel(self) -> gui.VGrid
    def get_bottom_panel(self) -> gui.Panel
    def add_on_layout_callback(self, callback: Callable) -> None
```

---

### 模块 2: DB树窗口 (DBTreePanel)

```
模块: DBTreePanel
├── 职责: 管理已加载点云计算的树形列表
├── 依赖: MainWindow
├── Open3D组件: gui.TreeCtrl
├── 功能:
│   ├── 显示点云计算列表 (名称、可见性勾选)
│   ├── 单击选中高亮
│   ├── 双击编辑名称
│   └── 右键菜单 (删除、重命名)
└── 事件:
    ├── on_cloud_toggled(cloud_id, visible)
    ├── on_cloud_selected(cloud_id)
    └── on_cloud_context_menu(cloud_id, x, y)
```

**接口设计:**
```python
class DBTreePanel:
    def add_cloud(self, cloud_id: str, name: str) -> None
    def remove_cloud(self, cloud_id: str) -> None
    def set_cloud_visible(self, cloud_id: str, visible: bool) -> None
    def set_cloud_selected(self, cloud_id: str) -> None
    def get_visible_clouds(self) -> List[str]
    def get_selected_cloud(self) -> Optional[str]
```

---

### 模块 3: 属性窗口 (PropertyPanel)

```
模块: PropertyPanel
├── 职责: 显示选中点云计算的详细信息
├── 依赖: DBTreePanel, CloudManager
├── Open3D组件: gui.VGrid + gui.Label
├── 显示内容:
│   ├── 基本信息: 名称、点数量、颜色
│   ├── 几何属性: 包围盒、质心、体素尺寸
│   ├── 统计信息: 点密度
│   └── 元数据: 文件路径、创建时间
└── 刷新策略: 选中项变化时更新
```

**接口设计:**
```python
class PropertyPanel:
    def update_properties(self, cloud_data: PointCloudData) -> None
    def clear(self) -> None
    def set_readonly(self, readonly: bool) -> None
```

---

### 模块 4: 控制台窗口 (ConsolePanel)

```
模块: ConsolePanel
├── 职责: 日志输出和系统信息展示
├── 依赖: LogService
├── Open3D组件: gui.Panel + gui.TextEdit
├── 功能:
│   ├── 日志级别过滤 (DEBUG/INFO/WARN/ERROR)
│   ├── 自动滚动到最新消息
│   ├── 清空控制台按钮
│   └── 消息着色 (按级别)
└── 配置: 滚动缓冲区，最大 5000 行
```

**接口设计:**
```python
class ConsolePanel:
    def append_log(self, message: str, level: LogLevel) -> None
    def clear(self) -> None
    def set_filter(self, min_level: LogLevel) -> None
```

---

### 模块 5: 点云管理服务 (CloudManager)

```
模块: CloudManager
├── 职责: 点云计算的加载、卸载、状态管理
├── 依赖: PointCloud Data Model
├── 核心功能:
│   ├── load_cloud(path: str) -> CloudID
│   ├── unload_cloud(cloud_id: CloudID) -> bool
│   ├── get_cloud(cloud_id: CloudID) -> PointCloudData
│   ├── list_clouds() -> List[CloudMeta]
│   └── set_visible(cloud_id, visible) -> None
└── 内部管理:
    ├── 点云计算缓存池
    ├── ID 分配器
    └── 可见性状态映射
```

**接口设计:**
```python
class CloudManager:
    def load(self, path: str) -> CloudID: ...
    def unload(self, cloud_id: CloudID) -> bool: ...
    def get(self, cloud_id: CloudID) -> Optional[PointCloudData]: ...
    def set_visible(self, cloud_id: CloudID, visible: bool) -> None: ...
    def get_visible(self) -> List[CloudID]: ...
    def get_all(self) -> List[CloudMeta]: ...
```

---

### 模块 6: 可视化服务 (ViewerService)

```
模块: ViewerService
├── 职责: 封装 Open3D Visualizer 和 SceneWidget
├── 依赖: Open3D, CloudManager
├── 核心功能:
│   ├── init_scene(scene_widget: SceneWidget) -> None
│   ├── add_geometry(cloud_id, geometry: o3d.geometry.PointCloud)
│   ├── remove_geometry(cloud_id) -> None
│   ├── update_geometry(cloud_id, geometry) -> None
│   ├── set_background(color: Color) -> None
│   └── capture_screenshot(path: str) -> bool
└── 渲染控制:
    ├── 渲染模式切换 (点/网格)
    ├── 坐标系显示
    └── 点大小调整
```

**接口设计:**
```python
class ViewerService:
    def __init__(self, cloud_manager: CloudManager)
    def set_scene_widget(self, widget: gui.SceneWidget) -> None
    def add_cloud(self, cloud_id: CloudID, pcd: o3d.geometry.PointCloud) -> None
    def remove_cloud(self, cloud_id: CloudID) -> None
    def update_visibility(self, visible_ids: List[CloudID]) -> None
    def render(self) -> None
```

---

### 模块 7: 日志服务 (LogService)

```
模块: LogService
├── 职责: 统一日志管理和分发
├── 依赖: Python logging
├── 日志级别: DEBUG(10), INFO(20), WARN(30), ERROR(40)
├── 输出目标:
│   ├── ConsolePanel (实时显示)
│   ├── 文件 (logs/app.log)
│   └── 标准输出
└── 格式化: [时间戳][级别] 消息内容
```

**接口设计:**
```python
class LogService:
    def debug(self, message: str) -> None: ...
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
    def set_console(self, console: Optional[ConsolePanel]) -> None
```

---

### 模块 8: 事件总线 (EventBus)

```
模块: EventBus
├── 职责: 模块间松耦合事件通信
├── 依赖: None
├── 事件类型:
│   ├── CloudLoadedEvent(cloud_id, cloud_data)
│   ├── CloudUnloadedEvent(cloud_id)
│   ├── CloudSelectedEvent(cloud_id)
│   ├── CloudToggledEvent(cloud_id, visible)
│   └── LogEvent(message, level)
└── 模式: 发布/订阅 (Pub/Sub)
```

**接口设计:**
```python
class EventBus:
    def subscribe(event_type: Type, callback: Callable) -> None
    def unsubscribe(event_type: Type, callback: Callable) -> None
    def publish(event: Event) -> None
```

---

## 4. 模块依赖关系图

```
                        ┌──────────────────┐
                        │   MainWindow     │
                        │ (Open3D Window)  │
                        └────────┬─────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
           ▼                     ▼                     ▼
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │ DBTreePanel  │      │PropertyPanel│      │ConsolePanel │
    │  (TreeCtrl)  │      │   (VGrid)   │      │ (TextEdit)  │
    └──────┬───────┘      └──────┬──────┘      └──────▲──────┘
           │                     │                     │
           └──────────┬──────────┴─────────────────────┘
                      │           事件通知
                      ▼
             ┌────────────────────┐
             │     EventBus       │
             │     (事件总线)      │
             └─────────┬──────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
   ┌───────────┐ ┌───────────┐ ┌───────────┐
   │CloudManager│ │ViewerServ │ │ LogService│
   └─────┬─────┘ └─────┬─────┘ └───────────┘
         │             │
         │    ┌────────┘
         │    │
         ▼    ▼
   ┌─────────────────┐
   │  Open3D Scene   │
   │   Widget        │
   └─────────────────┘
```

---

## 5. 窗口布局配置

```
┌─────────────────────────────────────────────────────────────────┐
│                      Window (o3d.gui.Window)                    │
│                                                                 │
│  ┌─────────────────┐ ┌─────────────────────────────────────┐   │
│  │  left_panel     │ │                                     │   │
│  │  (可缩放)        │ │                                     │   │
│  │  ┌─────────────┐│ │                                     │   │
│  │  │ DBTreePanel ││ │        SceneWidget                  │   │
│  │  │ (TreeCtrl)  ││ │        (3D渲染区域)                  │   │
│  │  ├─────────────┤│ │        (固定大小)                   │   │
│  │  │PropertyPanel││ │                                     │   │
│  │  │ (VGrid)     ││ │                                     │   │
│  │  └─────────────┘│ │                                     │   │
│  └─────────────────┘ └─────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  bottom_panel (ConsolePanel)                                ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │ TextEdit (可滚动/缩放, 缓冲区5000行)                     │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 布局代码示例

```python
# 创建主窗口
window = app.create_window("ManualCloudCompare", 1280, 800)

# 3D 场景区域 (固定大小)
scene = gui.SceneWidget()
scene.set_on_refresh(self._on_scene_refresh)

# 左侧面板 (可缩放)
left_panel = gui.VGrid(2)
left_panel.add_child(db_tree_panel)
left_panel.add_child(property_panel)

# 底部控制台 (可缩放)
console_panel = gui.Panel(gui.TOP)
console_panel.add_child(console_text)
```

---

## 6. 代码审核清单

| 审核项 | 说明 | 优先级 |
|--------|------|--------|
| 模块接口文档 | 每个公共接口必须有docstring | 必须 |
| 类型注解 | 函数参数/返回值必须标注类型 | 必须 |
| 异常处理 | 所有外部调用必须try-catch | 必须 |
| 资源释放 | 文件/内存资源正确释放 | 必须 |
| Open3D GUI规范 | 遵循Open3D事件循环规范 | 必须 |
| 测试覆盖 | 核心逻辑测试覆盖率>80% | 应该 |

---

## 7. 测试分层方案

```
┌─────────────────────────────────────────┐
│        端到端测试 (E2E Tests)            │
│   test_full_workflow.py                 │
│   - 完整加载-显示-交互流程               │
├─────────────────────────────────────────┤
│        集成测试 (Integration Tests)     │
│   test_cloud_manager.py                 │
│   test_viewer_service.py                │
│   - 模块间交互正确性                     │
├─────────────────────────────────────────┤
│        单元测试 (Unit Tests)            │
│   tests/unit/                           │
│   - 各模块独立功能测试                   │
├─────────────────────────────────────────┤
│        UI测试 (UI Tests)                │
│   tests/ui/                             │
│   - Open3D GUI 组件测试                 │
└─────────────────────────────────────────┘
```

### 测试用例清单

| 测试文件 | 测试内容 | 目标覆盖率 |
|---------|---------|-----------|
| `test_cloud_manager.py` | 点云计算加载/卸载/状态 | 85% |
| `test_viewer_service.py` | Open3D渲染封装 | 80% |
| `test_event_bus.py` | 事件订阅/发布 | 75% |
| `test_data_models.py` | 数据结构验证 | 90% |
| `test_integration.py` | 模块集成 | 70% |

---

## 8. 相关技术文档

### 8.1 核心技术文档

| 技术 | 版本 | 文档链接 | 关键内容 |
|------|------|----------|----------|
| **Open3D** | 0.18+ | [官方文档](https://www.open3d.org/docs/release/) | GUI、Visualizer、点云处理 |
| **Open3D GUI** | - | [GUI教程](https://www.open3d.org/docs/release/tutorial/gui/index.html) | Window、SceneWidget、自定义UI |
| **OpenCV** | 4.10+ | [官方文档](https://docs.opencv.org/4.x/) | 图像处理、标定 |
| **NumPy** | 2.0+ | [官方文档](https://numpy.org/doc/stable/) | 数组运算 |

### 8.2 Open3D GUI 参考

```python
# 关键 GUI 类参考
from open3d.visualization import gui, render

# 窗口管理
gui.Application.instance  # 单例应用
gui.Application.create_window()  # 创建窗口
gui.Application.run()  # 运行事件循环

# UI组件
gui.Window  # 主窗口
gui.SceneWidget  # 3D场景
gui.Button  # 按钮
gui.Checkbox  # 复选框
gui.TreeCtrl  # 树形控件
gui.TextEdit  # 文本编辑
gui.Label  # 标签
gui.Slider  # 滑块
gui.TabControl  # 标签页

# 布局
gui.VGrid  # 垂直网格
gui.HGrid  # 水平网格
gui.VStack  # 垂直堆叠
gui.HStack  # 水平堆叠
gui.Panel  # 可拆分面板
```

### 8.3 Python 3.10 新特性

```python
# 结构化模式匹配
match event:
    case CloudLoadedEvent(cloud_id=cid):
        viewer.add_cloud(cid)
    case CloudToggledEvent(cloud_id=cid, visible=v):
        viewer.set_visible(cid, v)

# 泛型简化
from collections.abc import Callable

class Signal[T]:
    def emit(self, value: T) -> None: ...
```

---

## 9. Git 代码版本管理策略

### 9.1 分支模型

```
main (生产环境)
  │
  └── develop (开发主分支)
        │
        ├── feat/cloud-manager
        ├── feat/db-tree-panel
        ├── feat/property-panel
        ├── feat/console-panel
        └── fix/...
```

### 9.2 提交规范 (Conventional Commits)

```bash
# 格式: <type>(<scope>): <description>

# 示例
feat(cloud-manager): add load_cloud method
feat(db-tree): implement checkbox toggle
fix(viewer): resolve memory leak
test(unit): add cloud manager tests
docs: update architecture design
```

### 9.3 发布流程

```bash
# 1. 合并到 main
git checkout main
git merge --no-ff develop

# 2. 打标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 3. 推送
git push origin main --tags
```

---

## 10. 项目目录结构

```
manual_cloudcompare/
├── main.py                    # 入口
├── src/
│   ├── __init__.py
│   │
│   ├── ui/                   # Open3D GUI 模块
│   │   ├── __init__.py
│   │   └── main_window.py   # 主窗口 ✅ 已实现
│   │
│   ├── core/                 # 核心服务
│   │   ├── __init__.py
│   │   ├── cloud_manager.py
│   │   ├── viewer_service.py
│   │   ├── event_bus.py
│   │   └── log_service.py
│   │
│   └── data/                 # 数据模型
│       ├── __init__.py
│       ├── point_cloud.py
│       └── transform.py
│
├── tests/
│   ├── __init__.py
│   └── test_main_window.py
│
├── docs/
├── config/
├── requirements.txt
├── CODEBUDDY.md
└── .gitignore
```

---

## 11. 下一步行动计划

| 优先级 | 模块 | 任务 | 依赖 |
|--------|------|------|------|
| P0 | EventBus | 事件通信基础设施 | - |
| P0 | CloudManager | 点云计算加载管理 | EventBus |
| P0 | MainWindow | Open3D GUI 主窗口框架 | Open3D |
| P1 | DBTreePanel | DB树面板实现 | MainWindow |
| P1 | PropertyPanel | 属性面板实现 | MainWindow |
| P1 | ConsolePanel | 控制台面板实现 | LogService |
| P1 | ViewerService | Open3D SceneWidget 封装 | CloudManager |
| P2 | 集成测试 | 模块集成测试 | 所有P1 |
