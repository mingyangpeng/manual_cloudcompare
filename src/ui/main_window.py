"""
主窗口模块 - ManualCloudCompare

职责: 系统主容器，使用 Open3D Window 管理所有子组件
依赖: o3d.visualization.gui, o3d.visualization.rendering (Open3D 0.19+)

功能特性:
    - 左侧面板完全折叠隐藏，鼠标靠近左边缘时显示展开按钮
    - 底部面板完全折叠隐藏，鼠标靠近下边缘时显示展开按钮
    - 点击展开按钮恢复面板
    - 键盘快捷键辅助 (L=左侧, B=底部)
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering

# 配置日志
_logger = logging.getLogger(__name__)


class MainWindow:
    """
    主窗口类 - 管理系统主容器和所有子组件

    使用 Open3D 原生 GUI 框架构建，包含：
    - 3D 渲染区域 (SceneWidget)
    - 左侧面板 (DB树 + 属性窗口) - 完全隐藏，边缘触发显示
    - 底部控制台面板 - 完全隐藏，边缘触发显示
    """

    # 默认窗口尺寸
    DEFAULT_WIDTH: int = 1280
    DEFAULT_HEIGHT: int = 800

    # 左侧面板展开宽度 (像素)
    LEFT_PANEL_WIDTH: int = 250

    # 底部面板展开高度 (像素)
    BOTTOM_PANEL_HEIGHT: int = 150

    # 边缘热区宽度 (鼠标靠近边缘时显示展开按钮)
    EDGE_HOT_ZONE: int = 5

    # 展开按钮大小
    EXPAND_BUTTON_SIZE: int = 32

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

        # Open3D GUI 组件
        self._window: Optional[gui.Window] = None
        self._scene_widget: Optional[gui.SceneWidget] = None
        self._left_panel: Optional[gui.Vert] = None
        self._bottom_panel: Optional[gui.Vert] = None

        # 边缘展开按钮 (悬浮在场景边缘)
        self._left_expand_btn: Optional[gui.Button] = None
        self._bottom_expand_btn: Optional[gui.Button] = None

        # 展开按钮显示状态
        self._show_left_btn: bool = False
        self._show_bottom_btn: bool = False

        # 面板可见状态
        self._left_panel_visible: bool = True
        self._bottom_panel_visible: bool = True

        # 面板内部容器 (用于折叠内容)
        self._left_panel_header: Optional[gui.CollapsableVert] = None
        self._bottom_panel_header: Optional[gui.CollapsableVert] = None

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
    def left_panel(self) -> gui.Vert:
        """获取左侧面板"""
        if self._left_panel is None:
            raise RuntimeError("LeftPanel not initialized. Call setup() first.")
        return self._left_panel

    @property
    def bottom_panel(self) -> gui.Vert:
        """获取底部面板"""
        if self._bottom_panel is None:
            raise RuntimeError("BottomPanel not initialized. Call setup() first.")
        return self._bottom_panel

    @property
    def is_running(self) -> bool:
        """获取窗口运行状态"""
        return self._is_running

    @property
    def is_left_panel_visible(self) -> bool:
        """获取左侧面板可见状态"""
        return self._left_panel_visible

    @property
    def is_bottom_panel_visible(self) -> bool:
        """获取底部面板可见状态"""
        return self._bottom_panel_visible

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

        # 3. 创建边缘展开按钮
        self._create_expand_buttons()

        # 4. 创建左侧面板
        self._create_left_panel()

        # 5. 创建底部控制台面板
        self._create_bottom_panel()

        # 6. 设置自定义布局回调
        self._setup_layout()

        # 7. 设置场景
        self._setup_scene()

        # 8. 设置键盘快捷键
        self._setup_shortcuts()

        # 9. 设置定时器检测鼠标位置
        self._setup_mouse_tracking()

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

    def get_left_panel(self) -> gui.Vert:
        """获取左侧面板"""
        return self.left_panel

    def get_bottom_panel(self) -> gui.Vert:
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

    def show_left_panel(self) -> None:
        """显示左侧面板"""
        self._left_panel_visible = True
        self._show_left_btn = False
        self._update_layout()
        _logger.debug("Left panel shown.")

    def hide_left_panel(self) -> None:
        """隐藏左侧面板"""
        self._left_panel_visible = False
        self._show_left_btn = False
        self._update_layout()
        _logger.debug("Left panel hidden.")

    def toggle_left_panel(self) -> None:
        """切换左侧面板显示状态"""
        if self._left_panel_visible:
            self.hide_left_panel()
        else:
            self.show_left_panel()

    def show_bottom_panel(self) -> None:
        """显示底部面板"""
        self._bottom_panel_visible = True
        self._show_bottom_btn = False
        self._update_layout()
        _logger.debug("Bottom panel shown.")

    def hide_bottom_panel(self) -> None:
        """隐藏底部面板"""
        self._bottom_panel_visible = False
        self._show_bottom_btn = False
        self._update_layout()
        _logger.debug("Bottom panel hidden.")

    def toggle_bottom_panel(self) -> None:
        """切换底部面板显示状态"""
        if self._bottom_panel_visible:
            self.hide_bottom_panel()
        else:
            self.show_bottom_panel()

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

    def _create_expand_buttons(self) -> None:
        """创建边缘展开按钮"""
        # 左侧展开按钮
        self._left_expand_btn = gui.Button("▶")
        self._left_expand_btn.set_on_clicked(self.show_left_panel)
        self._left_expand_btn.tooltip = "Show Side Panel"
        self._window.add_child(self._left_expand_btn)

        # 底部展开按钮
        self._bottom_expand_btn = gui.Button("▲")
        self._bottom_expand_btn.set_on_clicked(self.show_bottom_panel)
        self._bottom_expand_btn.tooltip = "Show Console"
        self._window.add_child(self._bottom_expand_btn)

        _logger.debug("Expand buttons created.")

    def _create_left_panel(self) -> None:
        """创建左侧面板"""
        em = self._window.theme.font_size

        # 创建主容器
        self._left_panel = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 0, 0))

        # 可折叠标题栏
        self._left_panel_header = gui.CollapsableVert("◀ Side Panel", 0, gui.Margins(0, 0, 0, 0))
        self._left_panel_header.set_is_open(True)

        # 内部内容容器
        left_content = gui.Vert(0, gui.Margins(0, 0, 0, 0))

        # DB 树区域
        db_tree_section = gui.CollapsableVert("DB Tree", 0, gui.Margins(0, 0, 0, 0))
        db_tree_section.set_is_open(True)

        db_tree_placeholder = gui.Label("[Point Cloud List]")
        db_tree_placeholder.background_color = gui.Color(0.9, 0.9, 0.9)
        db_tree_section.add_child(db_tree_placeholder)
        left_content.add_child(db_tree_section)

        left_content.add_child(gui.Label(""))

        # 属性区域
        property_section = gui.CollapsableVert("Properties", 0, gui.Margins(0, 0, 0, 0))
        property_section.set_is_open(True)

        property_placeholder = gui.Label("[Property Info]")
        property_placeholder.background_color = gui.Color(0.9, 0.9, 0.85)
        property_section.add_child(property_placeholder)
        left_content.add_child(property_section)

        self._left_panel_header.add_child(left_content)
        self._left_panel.add_child(self._left_panel_header)

        self._window.add_child(self._left_panel)
        _logger.debug("Left panel created.")

    def _create_bottom_panel(self) -> None:
        """创建底部控制台面板"""
        em = self._window.theme.font_size

        # 创建主容器
        self._bottom_panel = gui.Vert(0, gui.Margins(0.25 * em, 0.1 * em, 0, 0))

        # 可折叠标题栏
        self._bottom_panel_header = gui.CollapsableVert("▲ Console", 0, gui.Margins(0, 0, 0, 0))
        self._bottom_panel_header.set_is_open(True)

        # 内部内容容器
        bottom_content = gui.Vert(0, gui.Margins(0, 0, 0, 0))

        # 控制台文本
        self._console_text = gui.TextEdit()
        self._console_text.text_value = "Welcome to ManualCloudCompare v0.1.0\n" + "-" * 40 + "\n"
        bottom_content.add_child(self._console_text)

        self._bottom_panel_header.add_child(bottom_content)
        self._bottom_panel.add_child(self._bottom_panel_header)

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
        """设置键盘快捷键"""
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
        """设置鼠标位置跟踪 (用于边缘热区检测)"""
        def on_mouse(event):
            """处理鼠标移动事件"""
            if event.type == gui.MouseEvent.Type.MOVE:
                self._handle_mouse_move(event.x, event.y)
            return gui.SceneWidget.EventCallbackResult.HANDLED

        self._scene_widget.set_on_mouse(on_mouse)
        _logger.debug("Mouse tracking configured.")

    def _handle_mouse_move(self, x: int, y: int) -> None:
        """处理鼠标移动"""
        if self._window is None:
            return

        r = self._window.content_rect
        window_height = r.height

        # 检查左边缘热区 (鼠标在窗口左边缘附近且面板隐藏)
        if x <= self.EDGE_HOT_ZONE and not self._left_panel_visible:
            self._show_left_btn = True
        elif self._left_panel_visible or x > self.EDGE_HOT_ZONE + 10:
            self._show_left_btn = False

        # 检查下边缘热区 (鼠标在窗口下边缘附近且面板隐藏)
        # 注意：y 坐标从顶部开始
        if window_height - y <= self.EDGE_HOT_ZONE and not self._bottom_panel_visible:
            self._show_bottom_btn = True
        elif self._bottom_panel_visible or window_height - y > self.EDGE_HOT_ZONE + 10:
            self._show_bottom_btn = False

        # 更新按钮可见性
        self._update_expand_buttons_visibility()
        # 触发布局更新
        self._update_layout()

    def _update_expand_buttons_visibility(self) -> None:
        """更新展开按钮的可见性"""
        if self._left_expand_btn is not None:
            self._left_expand_btn.visible = self._show_left_btn
        if self._bottom_expand_btn is not None:
            self._bottom_expand_btn.visible = self._show_bottom_btn

    def _update_layout(self) -> None:
        """更新布局"""
        if self._window is not None:
            self._window.set_needs_layout()
            self._window.post_redraw()

    def _on_layout(self, layout_context) -> None:
        """布局回调 - 调整所有子组件的位置和大小"""
        r = self._window.content_rect
        em = self._window.theme.font_size
        btn_size = self.EXPAND_BUTTON_SIZE

        # 计算场景起始位置
        scene_x = 0
        scene_y = 0
        scene_width = r.width
        scene_height = r.height

        # 左侧面板布局
        if self._left_panel is not None:
            if self._left_panel_visible:
                # 面板可见
                self._left_panel.frame = gui.Rect(0, 0, self.LEFT_PANEL_WIDTH, r.height)
                scene_x = self.LEFT_PANEL_WIDTH
                scene_width = r.width - self.LEFT_PANEL_WIDTH
                # 左侧展开按钮不显示
                self._show_left_btn = False
            else:
                # 面板隐藏
                self._left_panel.frame = gui.Rect(0, 0, 0, 0)

        # 底部面板布局
        if self._bottom_panel is not None:
            if self._bottom_panel_visible:
                # 面板可见
                self._bottom_panel.frame = gui.Rect(0, r.height - self.BOTTOM_PANEL_HEIGHT, r.width, self.BOTTOM_PANEL_HEIGHT)
                scene_height = r.height - self.BOTTOM_PANEL_HEIGHT
                # 底部展开按钮不显示
                self._show_bottom_btn = False
            else:
                # 面板隐藏
                self._bottom_panel.frame = gui.Rect(0, 0, 0, 0)

        # 3D 场景
        if self._scene_widget is not None:
            self._scene_widget.frame = gui.Rect(scene_x, scene_y, scene_width, scene_height)

        # 展开按钮布局
        if self._left_expand_btn is not None:
            # 左侧按钮位于场景左边缘中央
            btn_y = r.height // 2 - btn_size // 2
            self._left_expand_btn.frame = gui.Rect(scene_x, btn_y, btn_size, btn_size)
            self._left_expand_btn.visible = self._show_left_btn

        if self._bottom_expand_btn is not None:
            # 底部按钮位于场景下边缘中央
            btn_x = r.width // 2 - btn_size // 2
            self._bottom_expand_btn.frame = gui.Rect(btn_x, scene_height - btn_size, btn_size, btn_size)
            self._bottom_expand_btn.visible = self._show_bottom_btn

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
