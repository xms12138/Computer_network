import socket
import webbrowser


def send_get_request(host, port, path):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((host, port))

        request = f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"

        client_socket.sendall(request.encode("utf-8"))

        # 接收服务器响应
        response = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            response += data

        # 关闭 socket
        client_socket.close()

        # 解析响应，提取 HTML 内容
        html_content = response.split(b'\r\n\r\n', 1)[1].decode("utf-8")
        print(html_content)
        # 将 HTML 内容保存到一个临时文件
        with open('temp_response.html', 'w', encoding='utf-8') as file:
            file.write(html_content)

        # 在默认浏览器中打开响应
        webbrowser.open('temp_response.html')

    except Exception as e:
        print(f"发生异常: {str(e)}")
        client_socket.close()


if __name__ == "__main__":
    target_host = "127.0.0.1"
    target_port = 8080
    target_path = "/1.html"
    send_get_request(target_host, target_port, target_path)
