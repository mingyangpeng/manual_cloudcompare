"""
程序入口

使用方法:
    python main.py
"""

import open3d.visualization.gui as gui

from src.ui import MainWindow, MainWindowFactory


def main() -> None:
    """
    主函数 - 初始化并运行应用程序
    """
    # 初始化 Open3D GUI 应用程序
    app = gui.Application.instance
    app.initialize()

    # 创建主窗口
    window = MainWindowFactory.create_default()
    window.setup()

    # 设置窗口关闭回调
    def on_close():
        print("Application closing...")

    window.set_on_close_callback(on_close)

    # 运行主事件循环
    app.run()


if __name__ == "__main__":
    main()
