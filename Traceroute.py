import os
import struct
import time
import select
import socket
from _socket import IPPROTO_IP, IP_TTL
from socket import timeout

ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
ICMP_Type_Unreachable = 3  # unacceptable host
ICMP_Type_Overtime = 11  # request overtime
MAX_HOPS = 30
TIMEOUT = 3  # 设置了每个跳数的超时时间
big_end_sequence = '!bbHh'
TRIES = 5  # 每一跳的尝试次数


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


def build_packet():
    icmp_checksum = 0
    # 1. Build ICMP header
    icmp_header = struct.pack(big_end_sequence, ICMP_ECHO_REQUEST, 0, icmp_checksum, 1)

    # 这个部分使用 struct.pack 函数将多个值打包成二进制数据。具体来说，'!bbHHh' 是格式字符串，指定了将要打包的数据的类型和顺序。按顺序解释：
    # ICMP_ECHO_REQUEST: 对应 'b'，一个字节，表示 ICMP 报文的类型。
    # 0: 对应 'b'，一个字节，表示 ICMP 报文的代码。
    # icmp_checksum: 对应 'H'，一个无符号短整型，表示校验和（checksum）。
    # 这个 struct.pack 操作的结果是将这些数值以二进制形式打包成一个 ICMP 请求报文的头部。
    time_send = struct.pack('!d', time.time())
    # 因此，struct.pack('!d', time.time()) 将当前时间戳打包成一个符合网络字节序的双精度浮点数的二进制表示。
    # 这个操作通常用于记录发送 ICMP 请求报文的时间，以便后续计算往返时间（Round-Trip Time, RTT）等网络性能指标。

    # 2. Checksum ICMP packet using given function
    icmp_checksum = checksum(icmp_header + time_send)
    # 3. Insert checksum into packet
    icmp_header = struct.pack(big_end_sequence, ICMP_ECHO_REQUEST, 0, icmp_checksum, 1)
    # 4. Send packet using socket
    icmp_packet = icmp_header + time_send
    return icmp_packet


def get_route(hostname):
    time_left = TIMEOUT  # 设置剩余时间为超时时间
    # 对每个跳数进行循环，最大跳数为MAX_HOPS
    for ttl in range(1, MAX_HOPS):
        # 每个跳数尝试的次数为TRIES
        for tries in range(TRIES):
            # 解析目标主机名为IP地址
            destination_ip = socket.gethostbyname(hostname)
            icmp_name = socket.getprotobyname('icmp')
            icmp_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_name)
            # 设置套接字的超时时间
            icmp_socket.settimeout(TIMEOUT)
            # 绑定套接字到任意端口
            icmp_socket.bind(("", 0))
            # 设置IP头部的TTL字段
            icmp_socket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            try:
                # 发送ICMP包到目标地址
                icmp_socket.sendto(build_packet(), (destination_ip, 0))
                # 记录发送时间
                t = time.time()
                # 开始等待响应
                time_begin_receive = time.time()
                if_got = select.select([icmp_socket], [], [], TIMEOUT)
                time_during_receive = time.time() - time_begin_receive
                # 检查是否超时
                if not if_got[0]:
                    print("  *        *        *    Request timed out.")
                rec_packet, addr = (icmp_socket.recvfrom(1024))
                # 记录接收时间
                time_received = time.time()
                # 更新剩余时间
                time_left = time_left - time_during_receive
                # 再次检查超时
                if time_left <= 0:
                    print("  *        *        *    Request timed out.")
            except timeout:
                # 超时则继续尝试
                continue
            else:
                # rec_packet, addr = (icmp_socket.recvfrom(1024))
                # 提取响应包中的ICMP类型和代码
                byte_in_double = struct.calcsize("!d")
                time_sent = struct.unpack("!d", rec_packet[26: 26 + byte_in_double])[0]
                rec_header = rec_packet[20:26]
                types, _, _, _ = struct.unpack(big_end_sequence, rec_header)
                # 根据ICMP类型处理响应
                if types == 11:
                    # 类型为11（TTL超时）时计算往返时间
                    print("  %d    rtt=%.0f ms    %s" % (ttl, (time_received - t) * 1000, addr[0]))
                elif types == 3:
                    # 类型为3（目标不可达）时计算往返时间
                    print("  %d    rtt=%.0f ms    %s" % (ttl, (time_received - t) * 1000, addr[0]))
                elif types == 0:
                    # 类型为0（回显应答）时计算往返时间，并结束traceroute
                    print("  %d    rtt=%.0f ms    %s" % (ttl, (time_received - time_sent) * 1000, addr[0]))
                    return
                else:
                    # 其他类型打印错误信息
                    print("error")
                break
            finally:
                icmp_socket.close()


if __name__ == '__main__':
    # 调用get_route函数进行traceroute，目标是baidu.com
    get_route("lancaster.com")
