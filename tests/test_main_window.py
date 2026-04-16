"""
测试模块1: 主窗口 (MainWindow)

测试用例:
    1. 主窗口初始化
    2. 组件创建
    3. 布局配置
    4. 回调函数
    5. 折叠功能
    6. 工厂方法
"""

import pytest


class TestMainWindow:
    """MainWindow 单元测试"""

    def test_init_default_values(self):
        """测试默认初始化值"""
        from src.ui.main_window import MainWindow

        window = MainWindow()

        assert window._title == "ManualCloudCompare"
        assert window._width == 1280
        assert window._height == 800

    def test_init_custom_values(self):
        """测试自定义初始化值"""
        from src.ui.main_window import MainWindow

        window = MainWindow(title="Test", width=1920, height=1080)

        assert window._title == "Test"
        assert window._width == 1920
        assert window._height == 1080

    def test_default_constants(self):
        """测试默认常量定义"""
        from src.ui.main_window import MainWindow

        assert MainWindow.DEFAULT_WIDTH == 1280
        assert MainWindow.DEFAULT_HEIGHT == 800
        assert MainWindow.LEFT_PANEL_WIDTH == 150
        assert MainWindow.BOTTOM_PANEL_HEIGHT == 100
        assert MainWindow.COLLAPSED_ICON_WIDTH == 18

    def test_property_accessors(self):
        """测试属性访问器抛出正确异常"""
        from src.ui.main_window import MainWindow

        window = MainWindow()

        with pytest.raises(RuntimeError, match="Window not initialized"):
            _ = window.window

        with pytest.raises(RuntimeError, match="SceneWidget not initialized"):
            _ = window.scene_widget

        with pytest.raises(RuntimeError, match="LeftPanel not initialized"):
            _ = window.left_panel

        with pytest.raises(RuntimeError, match="BottomPanel not initialized"):
            _ = window.bottom_panel

    def test_close_without_setup(self):
        """测试未初始化时关闭不抛异常"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.close()  # 应该静默处理

    def test_is_running_initial_state(self):
        """测试初始运行状态"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        assert window.is_running is False

    def test_append_console_log(self):
        """测试添加控制台日志"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        # 未初始化时调用应该不抛异常
        window.append_console_log("Test message")

    def test_clear_console(self):
        """测试清空控制台"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        # 未初始化时调用应该不抛异常
        window.clear_console()


class TestCollapseFeature:
    """折叠功能测试"""

    def test_init_collapsed_state(self):
        """测试初始折叠状态 (未初始化时返回 False)"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        assert window.is_left_panel_collapsed is False
        assert window.is_bottom_panel_collapsed is False

    def test_toggle_left_panel_without_setup(self):
        """测试未初始化时切换左侧面板不抛异常"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.toggle_left_panel()  # 应该静默处理

    def test_toggle_bottom_panel_without_setup(self):
        """测试未初始化时切换底部面板不抛异常"""
        from src.ui.main_window import MainWindow

        window = MainWindow()
        window.toggle_bottom_panel()  # 应该静默处理


class TestMainWindowFactory:
    """MainWindowFactory 测试"""

    def test_create_default(self):
        """测试创建默认配置窗口"""
        from src.ui.main_window import MainWindow, MainWindowFactory

        window = MainWindowFactory.create_default()

        assert isinstance(window, MainWindow)
        assert window._title == "ManualCloudCompare"
        assert window._width == 1280
        assert window._height == 800

    def test_create_fullscreen(self):
        """测试创建全屏窗口"""
        from src.ui.main_window import MainWindow, MainWindowFactory

        window = MainWindowFactory.create_fullscreen()

        assert isinstance(window, MainWindow)
        assert window._title == "ManualCloudCompare"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
