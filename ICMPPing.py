import os
import struct
import time
import select
import socket


ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_Type_Unreachable = 3  # unacceptable host
ICMP_Type_Overtime = 11  # request overtime
ID = 0  # ID of icmp_header
SEQUENCE = 0  # sequence of ping_request_msg
big_end_sequence = '!bbHHh'


def checksum(strings):
    csum = 0
    count_to = (len(strings) / 2) * 2
    counts = 0
    while counts < count_to:
        this_val = strings[counts + 1] * 256 + strings[counts]
        csum = csum + this_val
        csum = csum & 0xffffffff
        counts = counts + 2
    if count_to < len(strings):
        csum = csum + strings[len(strings) - 1]
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receive_one_ping(icmp_socket, id_number, time_out):
    # 1. Wait for the socket to receive a reply
    time_begin_receive = time.time()
    if_got = select.select([icmp_socket], [], [], time_out)
    time_during_receive = time.time() - time_begin_receive
    if not if_got[0]:
        return -1
    # 如果 if_got[0] 为假（表示在超时时间内没有可读事件发生），则返回 -1。这可能表示接收操作超时，没有接收到数据。
    time_received = time.time()
    # 2. Once received, record time of receipt, otherwise, handle a time_out
    rec_packet, _ = (icmp_socket.recvfrom(1024))
    # 3. Compare the time of receipt to time of sending, producing the total network delay
    byte_in_double = struct.calcsize("!d")
    time_sent = struct.unpack("!d", rec_packet[28: 28 + byte_in_double])[0]
    total_delay = time_received - time_sent
    # 4. Unpack the packet header for useful information, including the id_number
    rec_header = rec_packet[20:28]
    reply_type, _, _, reply_id, _ = struct.unpack(big_end_sequence, rec_header)

    # 5. Check that the id_number matches between the request and reply
    if id_number == reply_id and reply_type == ICMP_ECHO_REPLY:
        # 6. Return total network delay
        return total_delay
    elif time_during_receive > time_out or reply_type == ICMP_Type_Overtime:
        return -11  # ttl overtime/time_out
    elif reply_type == ICMP_Type_Unreachable:
        return -3  # unreachable
    else:
        print("request over time")
        return -1


def send_one_ping(icmp_socket, destination_address, id_number):
    icmp_checksum = 0
    # 1. Build ICMP header
    icmp_header = struct.pack(big_end_sequence, ICMP_ECHO_REQUEST, 0, icmp_checksum, id_number, SEQUENCE)

    # 这个部分使用 struct.pack 函数将多个值打包成二进制数据。具体来说，'!bbHHh' 是格式字符串，指定了将要打包的数据的类型和顺序。按顺序解释：
    # ICMP_ECHO_REQUEST: 对应 'b'，一个字节，表示 ICMP 报文的类型。
    # 0: 对应 'b'，一个字节，表示 ICMP 报文的代码。
    # icmp_checksum: 对应 'H'，一个无符号短整型，表示校验和（checksum）。
    # id_number: 对应 'H'，一个无符号短整型，表示标识符（id_number）。
    # SEQUENCE: 对应 'h'，一个有符号短整型，表示序列号（SEQUENCE）。
    # 这个 struct.pack 操作的结果是将这些数值以二进制形式打包成一个 ICMP 请求报文的头部。
    time_send = struct.pack('!d', time.time())
    # 因此，struct.pack('!d', time.time()) 将当前时间戳打包成一个符合网络字节序的双精度浮点数的二进制表示。
    # 这个操作通常用于记录发送 ICMP 请求报文的时间，以便后续计算往返时间（Round-Trip Time, RTT）等网络性能指标。

    # 2. Checksum ICMP packet using given function
    icmp_checksum = checksum(icmp_header + time_send)
    # 3. Insert checksum into packet
    icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, id_number, SEQUENCE)
    # 4. Send packet using socket
    icmp_packet = icmp_header + time_send
    icmp_socket.sendto(icmp_packet, (destination_address, 80))
    # 使用 icmp_socket 套接字对象发送 ICMP 请求报文 (icmp_packet) 到指定的目标地址和端口。


def do_one_ping(destination_address, time_out):  # destinationAddress是目的服务器的ip地址
    # 1. Create ICMP socket
    icmp_name = socket.getprotobyname('icmp')
    # 这个函数根据协议名称（'icmp'）获取协议号。在这里，它获取 ICMP 协议的协议号。
    icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_name)
    # 这个语句创建了一个新的套接字。参数 socket.AF_INET 指定了地址族（IPv4），socket.SOCK_RAW 表示这是一个原始套接字，而 icmpName 参数指定了使用的协议（ICMP）。
    # 2. Call sendOnePing function
    send_one_ping(icmp_socket, destination_address, ID)
    # 3. Call receiveOnePing function
    total_delay = receive_one_ping(icmp_socket, ID, time_out)
    # 4. Close ICMP socket
    icmp_socket.close()
    # 5. Return total network delay
    return total_delay


def ping(host, counts, time_out):
    send = 0
    lost = 0
    receive = 0
    max_time = 0
    min_time = 1000
    sum_time = 0
    # 1. Look up hostname, resolving it to an IP address
    destination_ip = socket.gethostbyname(host)
    global ID
    ID = os.getpid()
    # 使用 Python 的 os 模块中的 getpid() 函数获取当前进程的进程ID（Process ID）
    for i in range(0, counts):
        global SEQUENCE
        SEQUENCE = i
        # 2. Call doOnePing function, approximately every second
        delay = do_one_ping(destination_ip, time_out) * 1000
        send += 1
        if delay > 0:
            receive += 1
            if max_time < delay:
                max_time = delay
            if min_time > delay:
                min_time = delay
            sum_time += delay
            # 3. Print out the returned delay
            print("Receive from: " + str(destination_ip) + ", delay = " + str(int(delay)) + "ms")
        else:
            lost += 1
            print("Fail to connect. ", end="")
            if delay == -3:
                # type = 3, target unreachable
                print("Target net/host/port/protocol is unreachable.")
            elif delay == -11:
                # type = 11, ttl overtime
                print("Request overtime.")
            else:
                # otherwise, overtime
                print("Request overtime.")
        time.sleep(1)
    printing(receive, sum_time, send, lost, max_time, min_time)


def printing(receive, sum_time, send, lost, max_time, min_time):
    if receive != 0:
        avg_time = sum_time / receive
        recv_rate = receive / send * 100.0
        print(
            "\nSend: {0}, success: {1}, lost: {2}, rate of success: {3}%.".format(send, receive, lost, recv_rate))
        print(
            "MaxTime = {0}ms, MinTime = {1}ms, AvgTime = {2}ms".format(int(max_time), int(min_time), int(avg_time)))
    else:
        print("\nSend: {0}, success: {1}, lost: {2}, rate of success: 0.0%".format(send, receive, lost))


if __name__ == '__main__':
    while True:
        try:
            hostName = input("Input ip/name of the host you want: ")
            count = int(input("How many times you want to detect: "))
            timeout = int(input("Input timeout: "))
            ping(hostName, count, timeout)
            break
        except Exception as e:
            print(e)
            continue
