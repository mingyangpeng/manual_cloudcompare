"""
主窗口模块 - ManualCloudCompare

职责: 系统主容器，使用 Open3D Window 管理所有子组件
依赖: o3d.visualization.gui, o3d.visualization.rendering (Open3D 0.19+)

功能特性:
    - 左侧面板支持折叠 (使用 CollapsableVert)
    - 底部面板支持折叠 (使用 CollapsableVert)
    - 点击面板标题栏即可展开/收起
    - 左侧面板底部不能超过底部面板，动态紧贴
    - 支持鼠标拖动调整侧边栏宽度
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering

# 配置日志
_logger = logging.getLogger(__name__)


class ResizableSplitter:
    """可拖动的分隔条"""

    def __init__(self, orientation: str = "horizontal"):
        """
        初始化分隔条

        Args:
            orientation: "horizontal" (垂直分割线) 或 "vertical" (水平分割线)
        """
        self._orientation = orientation
        self._widget = gui.Widget()
        self._is_dragging = False
        self._drag_start_pos = 0
        self._on_drag_callback = None
        self._is_visible = False

        # 设置固定尺寸
        if orientation == "horizontal":
            self._widget.frame = gui.Rect(0, 0, 4, 100)
            self._widget.background_color = gui.Color(0.6, 0.6, 0.6)
        else:
            self._widget.frame = gui.Rect(0, 0, 100, 4)
            self._widget.background_color = gui.Color(0.6, 0.6, 0.6)

    @property
    def widget(self) -> gui.Widget:
        return self._widget

    @property
    def is_visible(self) -> bool:
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value: bool):
        self._is_visible = value
        self._widget.visible = value

    def set_on_drag(self, callback: Callable[[int], None]) -> None:
        """设置拖动回调 (接收偏移量)"""
        self._on_drag_callback = callback

    def handle_drag(self, x: int, y: int) -> None:
        """处理拖动事件"""
        if self._on_drag_callback:
            self._on_drag_callback(0)  # 简化版，由外部处理具体逻辑


class MainWindow:
    """
    主窗口类 - 管理系统主容器和所有子组件

    使用 Open3D 原生 GUI 框架构建，包含：
    - 3D 渲染区域 (SceneWidget)
    - 左侧面板 (DB树 + 属性窗口) - 支持折叠和拖动调整宽度，紧贴底部
    - 底部控制台面板 - 支持折叠
    """

    # 默认窗口尺寸
    DEFAULT_WIDTH: int = 1280
    DEFAULT_HEIGHT: int = 800

    # 左侧面板展开宽度 (像素) - 缩小到 150px
    LEFT_PANEL_WIDTH: int = 150

    # 底部面板展开高度 (像素) - 缩小到 100px
    BOTTOM_PANEL_HEIGHT: int = 100

    # 折叠后残留宽度 (仅折叠图标宽度) - 缩小到 18px
    COLLAPSED_ICON_WIDTH: int = 18

    # 侧边栏最小/最大宽度
    MIN_LEFT_PANEL_WIDTH: int = 80
    MAX_LEFT_PANEL_WIDTH: int = 400

    def __init__(
        self,
        title: str = "ManualCloudCompare",
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
    ) -> None:
        """
        初始化主窗口

        Args:
            title: 窗口标题
            width: 窗口宽度
            height: 窗口高度
        """
        self._title: str = title
        self._width: int = width
        self._height: int = height

        # 当前侧边栏宽度 (可变)
        self._current_left_width: int = self.LEFT_PANEL_WIDTH

        # 拖动状态
        self._is_dragging_splitter: bool = False
        self._drag_start_x: int = 0

        # Open3D GUI 组件
        self._window: Optional[gui.Window] = None
        self._scene_widget: Optional[gui.SceneWidget] = None
        self._left_panel: Optional[gui.CollapsableVert] = None
        self._bottom_panel: Optional[gui.CollapsableVert] = None
        self._splitter: Optional[ResizableSplitter] = None

        # 面板内部容器
        self._left_panel_content: Optional[gui.Vert] = None
        self._bottom_panel_content: Optional[gui.Vert] = None

        # 控制台文本控件
        self._console_text: Optional[gui.TextEdit] = None

        # 窗口运行状态
        self._is_running: bool = False

        # 回调函数
        self._on_close_callback: Optional[Callable[[], None]] = None

    # =========================================================================
    # 公共属性
    # =========================================================================

    @property
    def window(self) -> gui.Window:
        """获取 Open3D 窗口实例"""
        if self._window is None:
            raise RuntimeError("Window not initialized. Call setup() first.")
        return self._window

    @property
    def scene_widget(self) -> gui.SceneWidget:
        """获取 3D 场景控件"""
        if self._scene_widget is None:
            raise RuntimeError("SceneWidget not initialized. Call setup() first.")
        return self._scene_widget

    @property
    def left_panel(self) -> gui.CollapsableVert:
        """获取左侧面板"""
        if self._left_panel is None:
            raise RuntimeError("LeftPanel not initialized. Call setup() first.")
        return self._left_panel

    @property
    def bottom_panel(self) -> gui.CollapsableVert:
        """获取底部面板"""
        if self._bottom_panel is None:
            raise RuntimeError("BottomPanel not initialized. Call setup() first.")
        return self._bottom_panel

    @property
    def is_running(self) -> bool:
        """获取窗口运行状态"""
        return self._is_running

    @property
    def is_left_panel_collapsed(self) -> bool:
        """获取左侧面板折叠状态"""
        if self._left_panel is not None:
            return not self._left_panel.get_is_open()
        return False

    @property
    def is_bottom_panel_collapsed(self) -> bool:
        """获取底部面板折叠状态"""
        if self._bottom_panel is not None:
            return not self._bottom_panel.get_is_open()
        return False

    @property
    def current_left_width(self) -> int:
        """获取当前左侧面板宽度"""
        return self._current_left_width

    # =========================================================================
    # 公共方法
    # =========================================================================

    def setup(self) -> None:
        """
        设置窗口 - 初始化所有组件并建立层级关系
        """
        # 1. 创建主窗口
        self._create_window()

        # 2. 创建 3D 场景控件
        self._create_scene_widget()

        # 3. 创建分隔条
        self._create_splitter()

        # 4. 创建左侧面板
        self._create_left_panel()

        # 5. 创建底部控制台面板
        self._create_bottom_panel()

        # 6. 设置自定义布局回调
        self._setup_layout()

        # 7. 设置场景
        self._setup_scene()

        # 8. 设置键盘快捷键 (保留作为辅助方式)
        self._setup_shortcuts()

        _logger.debug(f"MainWindow initialized: {self._width}x{self._height}")

    def run(self) -> None:
        """运行主事件循环"""
        if self._window is None:
            raise RuntimeError("Window not initialized. Call setup() first.")

        self._is_running = True
        _logger.debug("Starting main event loop...")
        gui.Application.instance.run()
        self._is_running = False
        _logger.debug("Main event loop exited.")

    def close(self) -> None:
        """关闭主窗口"""
        if self._window is not None:
            self._window.close()
            _logger.debug("MainWindow closed.")

    def get_scene_widget(self) -> gui.SceneWidget:
        """获取 3D 场景控件"""
        return self.scene_widget

    def get_left_panel(self) -> gui.CollapsableVert:
        """获取左侧面板"""
        return self.left_panel

    def get_bottom_panel(self) -> gui.CollapsableVert:
        """获取底部面板"""
        return self.bottom_panel

    def set_on_close_callback(self, callback: Callable[[], None]) -> None:
        """设置窗口关闭回调"""
        self._on_close_callback = callback

    def append_console_log(self, message: str) -> None:
        """向控制台添加日志消息"""
        if self._console_text is not None:
            self._console_text.text_value += message + "\n"

    def clear_console(self) -> None:
        """清空控制台"""
        if self._console_text is not None:
            self._console_text.text_value = ""

    def toggle_left_panel(self) -> None:
        """切换左侧面板折叠状态"""
        if self._left_panel is not None:
            self._left_panel.set_is_open(self.is_left_panel_collapsed)
            self._force_layout_update()
            _logger.debug(f"Left panel collapsed: {self.is_left_panel_collapsed}")

    def toggle_bottom_panel(self) -> None:
        """切换底部面板折叠状态"""
        if self._bottom_panel is not None:
            self._bottom_panel.set_is_open(self.is_bottom_panel_collapsed)
            self._force_layout_update()
            _logger.debug(f"Bottom panel collapsed: {self.is_bottom_panel_collapsed}")

    # =========================================================================
    # 私有方法
    # =========================================================================

    def _create_window(self) -> None:
        """创建主窗口实例"""
        self._window = gui.Application.instance.create_window(
            self._title, self._width, self._height
        )
        self._window.set_on_close(self._handle_close)
        _logger.debug("Window created.")

    def _create_scene_widget(self) -> None:
        """创建 3D 场景渲染控件"""
        self._scene_widget = gui.SceneWidget()
        # 关键：使用 rendering.Open3DScene 创建场景
        self._scene_widget.scene = rendering.Open3DScene(self._window.renderer)
        self._scene_widget.set_view_controls(gui.SceneWidget.Controls.ROTATE_CAMERA)
        self._window.add_child(self._scene_widget)
        _logger.debug("SceneWidget created.")

    def _create_splitter(self) -> None:
        """创建分隔条"""
        self._splitter = ResizableSplitter("horizontal")
        self._splitter.is_visible = True

        # 设置拖动回调
        def on_drag(delta: int):
            self._current_left_width += delta
            # 限制宽度范围
            self._current_left_width = max(self.MIN_LEFT_PANEL_WIDTH, min(self.MAX_LEFT_PANEL_WIDTH, self._current_left_width))
            self._force_layout_update()

        self._splitter.set_on_drag(on_drag)

        self._window.add_child(self._splitter.widget)
        _logger.debug("Splitter created.")

    def _create_left_panel(self) -> None:
        """创建左侧面板 (使用 CollapsableVert 实现折叠)"""
        em = self._window.theme.font_size

        # 创建可折叠的标题栏
        self._left_panel = gui.CollapsableVert("◀ Side Panel", 0, gui.Margins(0.25 * em, 0.25 * em, 0, 0))
        self._left_panel.set_is_open(True)

        # 创建内容容器
        self._left_panel_content = gui.Vert(0, gui.Margins(0, 0, 0, 0))

        # DB 树区域 (内部也支持折叠)
        db_tree_section = gui.CollapsableVert("DB Tree", 0, gui.Margins(0, 0, 0, 0))
        db_tree_section.set_is_open(True)

        # DB 树占位符
        db_tree_placeholder = gui.Label("[Point Cloud List]")
        db_tree_placeholder.background_color = gui.Color(0.9, 0.9, 0.9)
        db_tree_section.add_child(db_tree_placeholder)

        self._left_panel_content.add_child(db_tree_section)

        # 分隔
        self._left_panel_content.add_child(gui.Label(""))

        # 属性区域 (内部也支持折叠)
        property_section = gui.CollapsableVert("Properties", 0, gui.Margins(0, 0, 0, 0))
        property_section.set_is_open(True)

        # 属性占位符
        property_placeholder = gui.Label("[Property Info]")
        property_placeholder.background_color = gui.Color(0.9, 0.9, 0.85)
        property_section.add_child(property_placeholder)

        self._left_panel_content.add_child(property_section)

        # 将内容添加到可折叠容器
        self._left_panel.add_child(self._left_panel_content)

        self._window.add_child(self._left_panel)
        _logger.debug("Left panel created.")

    def _create_bottom_panel(self) -> None:
        """创建底部控制台面板 (使用 CollapsableVert 实现折叠)"""
        em = self._window.theme.font_size

        # 创建可折叠的标题栏
        self._bottom_panel = gui.CollapsableVert("▲ Console", 0, gui.Margins(0.25 * em, 0.1 * em, 0, 0))
        self._bottom_panel.set_is_open(True)

        # 创建内容容器
        self._bottom_panel_content = gui.Vert(0, gui.Margins(0, 0, 0, 0))

        # 控制台文本
        self._console_text = gui.TextEdit()
        self._console_text.text_value = "Welcome to ManualCloudCompare v0.1.0\n" + "-" * 40 + "\n"
        self._bottom_panel_content.add_child(self._console_text)

        # 将内容添加到可折叠容器
        self._bottom_panel.add_child(self._bottom_panel_content)

        self._window.add_child(self._bottom_panel)
        _logger.debug("Bottom panel created.")

    def _setup_layout(self) -> None:
        """设置自定义布局回调"""
        self._window.set_on_layout(self._on_layout)

    def _setup_scene(self) -> None:
        """设置 3D 场景初始状态"""
        if self._scene_widget is None:
            return

        scene = self._scene_widget.scene

        # 设置背景颜色
        scene.set_background([0.1, 0.1, 0.1, 1.0])

        # 显示坐标轴
        scene.show_axes(True)

        # 设置光照 (带兼容性检查)
        if hasattr(scene, 'scene'):
            scene_inner = scene.scene
            if hasattr(scene_inner, 'set_sun_light'):
                scene_inner.set_sun_light([-0.5, 1.0, 0.5], [0.8, 0.8, 0.8], 50000)
            if hasattr(scene_inner, 'enable_sun_light'):
                scene_inner.enable_sun_light(True)

        # 设置相机位置
        bounds = scene.bounding_box
        if bounds is not None:
            center = bounds.get_center()
            self._scene_widget.setup_camera(60, bounds, center)

        _logger.debug("Scene setup completed.")

    def _setup_shortcuts(self) -> None:
        """设置键盘快捷键 (作为辅助方式)"""
        def handle_key(event):
            """处理键盘事件"""
            if event.key == gui.KeyName.L:
                self.toggle_left_panel()
            elif event.key == gui.KeyName.B:
                self.toggle_bottom_panel()
            return gui.KeyEvent.Result.HANDLED

        self._window.set_on_key(handle_key)
        _logger.debug("Keyboard shortcuts configured (L=left, B=bottom).")

    def _setup_mouse_tracking(self) -> None:
        """设置鼠标跟踪 (用于拖动分隔条)"""
        # SceneWidget 支持 set_on_mouse
        def on_mouse(event):
            """处理鼠标事件"""
            if self._scene_widget is None:
                return gui.SceneWidget.EventCallbackResult.HANDLED

            # 鼠标按下
            if event.type == gui.MouseEvent.Type.BUTTON_DOWN:
                if event.button == gui.MouseButton.LEFT:
                    # 检查是否在分隔条区域 (左侧面板右边缘 10px 范围内)
                    if self._left_panel is not None and not self.is_left_panel_collapsed:
                        panel_right = self._current_left_width
                        if abs(event.x - panel_right) <= 10:
                            self._is_dragging_splitter = True
                            self._drag_start_x = event.x
                            return gui.SceneWidget.EventCallbackResult.HANDLED

            # 鼠标释放
            elif event.type == gui.MouseEvent.Type.BUTTON_UP:
                if event.button == gui.MouseButton.LEFT:
                    self._is_dragging_splitter = False

            # 鼠标移动
            elif event.type == gui.MouseEvent.Type.MOVE:
                if self._is_dragging_splitter:
                    delta = event.x - self._drag_start_x
                    self._drag_start_x = event.x
                    self._current_left_width += delta
                    # 限制宽度范围
                    self._current_left_width = max(
                        self.MIN_LEFT_PANEL_WIDTH,
                        min(self.MAX_LEFT_PANEL_WIDTH, self._current_left_width)
                    )
                    self._force_layout_update()
                    return gui.SceneWidget.EventCallbackResult.HANDLED

            return gui.SceneWidget.EventCallbackResult.IGNORED

        self._scene_widget.set_on_mouse(on_mouse)
        _logger.debug("Mouse tracking configured.")

    def _force_layout_update(self) -> None:
        """强制触发布局更新"""
        if self._window is not None:
            self._window.set_needs_layout()
            # 触发重绘
            self._window.post_redraw()

    def _on_layout(self, layout_context) -> None:
        """布局回调 - 调整所有子组件的位置和大小"""
        r = self._window.content_rect

        # 计算底部面板的实际高度 (根据折叠状态)
        if self._bottom_panel is not None:
            if self.is_bottom_panel_collapsed:
                # 折叠时只显示标题栏高度
                bottom_height = self._bottom_panel.calc_preferred_size(
                    layout_context, gui.Widget.Constraints()
                ).height
            else:
                bottom_height = self.BOTTOM_PANEL_HEIGHT
        else:
            bottom_height = 0

        # 计算左侧面板的实际宽度 (根据折叠状态和拖动)
        if self._left_panel is not None:
            if self.is_left_panel_collapsed:
                # 折叠时只显示图标宽度
                left_width = self.COLLAPSED_ICON_WIDTH
            else:
                # 使用当前拖动后的宽度
                left_width = self._current_left_width
        else:
            left_width = 0

        # 左侧面板高度 = 窗口高度 - 底部面板高度 (紧贴底部)
        left_height = r.height - bottom_height

        # 布局左侧面板
        if self._left_panel is not None:
            self._left_panel.frame = gui.Rect(0, 0, left_width, left_height)

        # 布局分隔条 (位于左侧面板右边，仅在面板展开时可见)
        if self._splitter is not None:
            splitter_x = left_width
            splitter_height = left_height
            self._splitter.widget.frame = gui.Rect(splitter_x, 0, 4, splitter_height)
            # 分隔条仅在面板展开且不在拖动时高亮
            if not self.is_left_panel_collapsed:
                self._splitter.widget.visible = True
                # 拖动时改变颜色
                if self._is_dragging_splitter:
                    self._splitter.widget.background_color = gui.Color(0.3, 0.5, 0.9)
                else:
                    self._splitter.widget.background_color = gui.Color(0.6, 0.6, 0.6)
            else:
                self._splitter.widget.visible = False

        # 布局底部面板
        if self._bottom_panel is not None:
            self._bottom_panel.frame = gui.Rect(0, r.height - bottom_height, r.width, bottom_height)

        # 3D 场景占据剩余空间 (从分隔条后开始)
        if self._scene_widget is not None:
            scene_x = left_width + 4  # 分隔条宽度
            scene_y = 0
            scene_width = r.width - scene_x
            scene_height = r.height - bottom_height
            self._scene_widget.frame = gui.Rect(scene_x, scene_y, scene_width, scene_height)

    # =========================================================================
    # 事件处理器
    # =========================================================================

    def _handle_close(self) -> bool:
        """处理窗口关闭事件"""
        _logger.debug("Window close requested.")
        if self._on_close_callback is not None:
            try:
                self._on_close_callback()
            except Exception as e:
                _logger.error(f"Error in close callback: {e}")
        return True


class MainWindowFactory:
    """主窗口工厂类"""

    @staticmethod
    def create_default() -> MainWindow:
        """创建默认配置的主窗口"""
        return MainWindow(
            title="ManualCloudCompare",
            width=MainWindow.DEFAULT_WIDTH,
            height=MainWindow.DEFAULT_HEIGHT,
        )

    @staticmethod
    def create_fullscreen() -> MainWindow:
        """创建全屏主窗口 (默认使用 1920x1080)"""
        return MainWindow(
            title="ManualCloudCompare",
            width=1920,
            height=1080,
        )
