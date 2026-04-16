"""
主窗口模块 - ManualCloudCompare

职责: 系统主容器，使用 Open3D Window 管理所有子组件
依赖: o3d.visualization.gui, o3d.visualization.rendering (Open3D 0.19+)

功能特性:
    - 左侧面板支持向左完全折叠
    - 底部面板支持向下完全折叠
    - 折叠状态自动保存
    - 快捷键支持 (L=左侧, B=底部)
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
    - 左侧面板 (DB树 + 属性窗口) - 支持折叠
    - 底部控制台面板 - 支持折叠
    """

    # 默认窗口尺寸
    DEFAULT_WIDTH: int = 1280
    DEFAULT_HEIGHT: int = 800

    # 左侧面板展开宽度 (像素)
    LEFT_PANEL_WIDTH: int = 250

    # 底部面板展开高度 (像素)
    BOTTOM_PANEL_HEIGHT: int = 150

    # 折叠后残留宽度/高度 (用于折叠按钮可见)
    COLLAPSED_SIZE: int = 5

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
        self._bottom_panel: Optional[gui.ScrollableVert] = None

        # 折叠按钮
        self._left_toggle_btn: Optional[gui.Button] = None
        self._bottom_toggle_btn: Optional[gui.Button] = None

        # 折叠状态
        self._left_panel_collapsed: bool = False
        self._bottom_panel_collapsed: bool = False

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
    def bottom_panel(self) -> gui.ScrollableVert:
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
        return self._left_panel_collapsed

    @property
    def is_bottom_panel_collapsed(self) -> bool:
        """获取底部面板折叠状态"""
        return self._bottom_panel_collapsed

    # =========================================================================
    # 公共方法
    # =========================================================================

    def setup(self) -> None:
        """
        设置窗口 - 初始化所有组件并建立层级关系
        """
        # 1. 创建主窗口
        self._create_window()

        # 2. 创建折叠按钮
        self._create_toggle_buttons()

        # 3. 创建 3D 场景控件
        self._create_scene_widget()

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

    def get_bottom_panel(self) -> gui.ScrollableVert:
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
        self._left_panel_collapsed = not self._left_panel_collapsed
        self._update_toggle_button_text()
        self._force_layout_update()
        _logger.debug(f"Left panel collapsed: {self._left_panel_collapsed}")

    def toggle_bottom_panel(self) -> None:
        """切换底部面板折叠状态"""
        self._bottom_panel_collapsed = not self._bottom_panel_collapsed
        self._update_toggle_button_text()
        self._force_layout_update()
        _logger.debug(f"Bottom panel collapsed: {self._bottom_panel_collapsed}")

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

    def _create_toggle_buttons(self) -> None:
        """创建折叠按钮"""
        self._left_toggle_btn = gui.Button("◀")
        self._left_toggle_btn.set_on_clicked(self.toggle_left_panel)

        self._bottom_toggle_btn = gui.Button("▲")
        self._bottom_toggle_btn.set_on_clicked(self.toggle_bottom_panel)

        self._window.add_child(self._left_toggle_btn)
        self._window.add_child(self._bottom_toggle_btn)
        _logger.debug("Toggle buttons created.")

    def _update_toggle_button_text(self) -> None:
        """更新折叠按钮文本"""
        if self._left_toggle_btn is not None:
            self._left_toggle_btn.text = "▶" if self._left_panel_collapsed else "◀"
        if self._bottom_toggle_btn is not None:
            self._bottom_toggle_btn.text = "▼" if self._bottom_panel_collapsed else "▲"

    def _create_scene_widget(self) -> None:
        """创建 3D 场景渲染控件"""
        self._scene_widget = gui.SceneWidget()
        # 关键：使用 rendering.Open3DScene 创建场景
        self._scene_widget.scene = rendering.Open3DScene(self._window.renderer)
        self._scene_widget.set_view_controls(gui.SceneWidget.Controls.ROTATE_CAMERA)
        self._window.add_child(self._scene_widget)
        _logger.debug("SceneWidget created.")

    def _create_left_panel(self) -> None:
        """创建左侧面板 (DB树 + 属性窗口)"""
        em = self._window.theme.font_size
        self._left_panel = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 0, 0))

        # DB 树区域
        db_tree_header = gui.CollapsableVert("DB Tree", 0, gui.Margins(0, 0, 0, 0))
        db_tree_header.set_is_open(True)

        # DB 树占位符
        db_tree_placeholder = gui.Label("[Point Cloud List]")
        db_tree_placeholder.background_color = gui.Color(0.9, 0.9, 0.9)
        db_tree_header.add_child(db_tree_placeholder)

        self._left_panel.add_child(db_tree_header)

        # 分隔
        self._left_panel.add_child(gui.Label(""))

        # 属性区域
        property_header = gui.CollapsableVert("Properties", 0, gui.Margins(0, 0, 0, 0))
        property_header.set_is_open(True)

        # 属性占位符
        property_placeholder = gui.Label("[Property Info]")
        property_placeholder.background_color = gui.Color(0.9, 0.9, 0.85)
        property_header.add_child(property_placeholder)

        self._left_panel.add_child(property_header)

        self._window.add_child(self._left_panel)
        _logger.debug("Left panel created.")

    def _create_bottom_panel(self) -> None:
        """创建底部控制台面板"""
        em = self._window.theme.font_size
        self._bottom_panel = gui.ScrollableVert(0, gui.Margins(0.25 * em, 0.1 * em, 0, 0))

        # 控制台标题
        console_header = gui.Label("Console")
        console_header.background_color = gui.Color(0.85, 0.85, 0.85)
        self._bottom_panel.add_child(console_header)

        # 控制台文本
        self._console_text = gui.TextEdit()
        self._console_text.text_value = "Welcome to ManualCloudCompare v0.1.0\n" + "-" * 40 + "\n"
        self._bottom_panel.add_child(self._console_text)

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

        # 设置光照
        scene.scene.set_sun_light([-0.5, 1.0, 0.5], [0.8, 0.8, 0.8], 50000)
        scene.scene.enable_sun_light(True)

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

    def _force_layout_update(self) -> None:
        """强制触发布局更新"""
        if self._window is not None:
            # 通过设置最小尺寸触发重新布局
            current_size = self._window.size
            self._window.size = (current_size[0] + 1, current_size[1])
            self._window.size = current_size

    def _on_layout(self, layout_context) -> None:
        """布局回调 - 调整所有子组件的位置和大小"""
        r = self._window.content_rect
        em = self._window.theme.font_size

        # 计算左侧面板实际宽度
        left_width = self.COLLAPSED_SIZE if self._left_panel_collapsed else self.LEFT_PANEL_WIDTH

        # 计算底部面板实际高度
        bottom_height = self.COLLAPSED_SIZE if self._bottom_panel_collapsed else self.BOTTOM_PANEL_HEIGHT

        # 3D 场景占据除了左侧和底部之外的全部区域
        scene_width = r.width - left_width
        scene_height = r.height - bottom_height
        self._scene_widget.frame = gui.Rect(
            left_width, 0, scene_width, scene_height
        )

        # 左侧面板
        self._left_panel.frame = gui.Rect(0, 0, left_width, scene_height)

        # 底部面板
        self._bottom_panel.frame = gui.Rect(0, r.height - bottom_height, r.width, bottom_height)

        # 折叠按钮位置
        btn_size = int(1.5 * em)

        # 左侧折叠按钮 (垂直放置)
        self._left_toggle_btn.frame = gui.Rect(0, r.height // 2 - btn_size, btn_size, btn_size)

        # 底部折叠按钮 (水平放置)
        self._bottom_toggle_btn.frame = gui.Rect(r.width // 2 - btn_size, r.height - bottom_height, btn_size, btn_size)

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
        """创建全屏主窗口"""
        screen_size = gui.Application.instance.desktop_size
        return MainWindow(
            title="ManualCloudCompare",
            width=screen_size.width,
            height=screen_size.height,
        )
