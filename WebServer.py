import socket
import mimetypes


def handle_request(request):
    # 解析请求
    request_lines = request.split('\r\n')
    print(request_lines)
    request_line = request_lines[0].split()

    # 获取请求的方法、路径和协议版本
    method = request_line[0]
    path = request_line[1]
    print(path)
    # 处理 GET 请求
    if method == 'GET':
        try:
            # 读取请求的文件内容
            with open('.' + path, 'rb') as file:
                content = file.read()
            mime_type, _ = mimetypes.guess_type(path)
            # 构建 HTTP 响应
            if mime_type == "image/png":
                text = "HTTP/1.1 200 OK\r\n\r\n"
                response = text.encode('utf-8') + content
            else:
                response = "HTTP/1.1 200 OK\r\n\r\n" + content.decode('utf-8')
                response = response.encode('utf-8')
                # print(response)
                print()
                # decode 是将字节串解码为字符串
        except IOError:
            # 文件不存在时返回 404 错误
            response = "HTTP/1.1 404 Not Found\r\n\r\n404 Not Found"
            response = response.encode('utf-8')
    else:
        # 不支持的方法返回 501 错误
        response = "HTTP/1.1 501 Not Implemented\r\n\r\nMethod Not Implemented"
        response = response.encode('utf-8')
    return response


def start_server(host1, port1):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # create TCP socket
    server_socket.bind((host1, port1))
    server_socket.listen(1)

    print(f"Serving on {host1}:{port1}...")

    while True:
        client_socket, _ = server_socket.accept()
        # client_socket是新的服务器套接字，与客户端的连接都使用这个新的套接字
        request = client_socket.recv(1024)
        # recv(1024): 这是套接字对象的 recv 方法，用于从连接中接收数据。参数 1024 指定一次最多接收的字节数。它表示从连接中尝试接收最多 1024 字节的数据.这里是字节序列
        request = request.decode('utf-8')
        # decode('utf-8') 的作用是将字节序列（bytes）解码为字符串
        # 字节序列（Bytes）是计算机中用于表示二进制数据的一种数据类型。在Python中，字节序列由bytes类型表示。它是不可变的序列，其中的每个元素都是0到255之间的整数，即一个字节。
        response = handle_request(request)
        client_socket.sendall(response)
        client_socket.close()


if __name__ == "__main__":
    host = '127.0.0.1'
    port = 8080
    start_server(host, port)
