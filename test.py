import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView

class HTMLViewer(QMainWindow):
    def __init__(self, html_content):
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle("HTML Viewer")
        self.setGeometry(100, 100, 800, 600)

        # 创建 WebEngineView 组件
        self.webview = QWebEngineView()
        self.setCentralWidget(self.webview)

        # 在 WebEngineView 中加载 HTML 内容
        self.webview.setHtml(html_content)

if __name__ == "__main__":
    # 替换为你的服务器地址和端口，以及要获取的 HTML 文件路径
    server_host = '127.0.0.1'
    server_port = 8080
    target_url = f"http://{server_host}:{server_port}/1.html"

    # 发送 GET 请求获取 HTML 内容
    response = requests.get(target_url)
    html_content = response.text

    # 创建应用程序对象
    app = QApplication(sys.argv)

    # 创建 HTMLViewer 实例
    viewer = HTMLViewer(html_content)

    # 显示窗口
    viewer.show()

    # 运行应用程序
    sys.exit(app.exec_())
