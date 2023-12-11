import os
import socket


def handle_req(client_socket):
    recv_data = client_socket.recv(1024).decode("UTF-8")
    file_name = recv_data.split()[1].split("//")[1].replace('/', '')
    print("fileName: " + file_name)
    file_path = "./" + file_name.split(":")[0].replace('.', '_')
    try:
        file = open(file_path + "./index.html", 'rb')
        print("File is found in proxy server.")
        response_msg = file.read()
        client_socket.sendall(response_msg)
        print("Send, done.")
    except FileNotFoundError as e:
        print(f"File not found: {e}\nSend request to server...")
        try:
            proxy_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_name = file_name.split(":")[0]
            proxy_client_socket.connect((server_name, 80))
            proxy_client_socket.sendall(recv_data.encode("UTF-8"))
            response_msg = proxy_client_socket.recv(4069)
            print("File is found in server.")
            client_socket.sendall(response_msg)
            print("Send, done.")
            # cache
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            cache = open(file_path + "./index.html", 'w')
            cache.writelines(response_msg.decode("UTF-8").replace('\r\n', '\n'))
            cache.close()
            print("Cache, done.")
        except Exception as e:
            print(f"An error occurred: {e}\nConnect timeout.")
            raise

        raise


def start_proxy(port1):
    proxy_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server_socket.bind(("", port1))
    proxy_server_socket.listen(0)
    while True:
        try:
            print("Proxy is waiting for connecting...")
            client_socket, _ = proxy_server_socket.accept()
            print("Connect established")
            handle_req(client_socket)
            client_socket.close()
        except Exception as e:
            print("error: {0}".format(e))
            break
    proxy_server_socket.close()


if __name__ == '__main__':
    while True:
        port = None
        try:
            port = int(input("choose a port number over 1024:"))
        except ValueError:
            print("Please input an integer rather than {0}".format(type(port)))
            continue
        else:
            if port <= 1024:
                print("Please input an integer greater than 1024")
                continue
            else:
                break
    start_proxy(port)
