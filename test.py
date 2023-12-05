# import os
# import struct
# import time
# import select
# import socket
#
# ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request messages
# ICMP_ECHO_REPLY = 0  # ICMP type code for echo reply messages
# ICMP_Type_Unreachable = 11  # unacceptable host
# ICMP_Type_Overtime = 3  # request overtime
# ID = 0  # ID of icmp_header
# SEQUENCE = 0  # sequence of ping_request_msg
#
#
# def checksum(strings):
#     csum = 0
#     countTo = (len(strings) / 2) * 2
#     count = 0
#     while count < countTo:
#         thisVal = strings[count + 1] * 256 + strings[count]
#         csum = csum + thisVal
#         csum = csum & 0xffffffff
#         count = count + 2
#     if countTo < len(strings):
#         csum = csum + strings[len(strings) - 1]
#         csum = csum & 0xffffffff
#     csum = (csum >> 16) + (csum & 0xffff)
#     csum = csum + (csum >> 16)
#     answer = ~csum
#     answer = answer & 0xffff
#     answer = answer >> 8 | (answer << 8 & 0xff00)
#     return answer
#
#
# def receiveOnePing(icmpSocket, ID, timeout):
#     # 1. Wait for the socket to receive a reply
#     timeBeginReceive = time.time()
#     whatReady = select.select([icmpSocket], [], [], timeout)
#     # 目的是等待 icmpSocket 上是否有可读事件（即是否有数据可接收）发生。如果有可读事件，则 whatReady 将包含一个非空的列表，否则，它将为空列表。
#     timeInRecev = time.time() - timeBeginReceive
#     if not whatReady[0]:   # 判断whatReady是否为空
#         return -1
#     timeReceived = time.time()
#     # 2. Once received, record time of receipt, otherwise, handle a timeout
#     recPacket, addr = icmpSocket.recvfrom(1024)
#     # 接收来自 icmpSocket 套接字的最多 1024 字节的数据，并将接收到的数据存储在 recPacket 变量中，发送方的地址存储在 addr 变量中。
#
#     # 3. Compare the time of receipt to time of sending, producing the total network delay
#     byte_in_double = struct.calcsize("!d")
#     # 使用 struct 模块中的 calcsize 函数，根据指定的格式字符串来计算对应类型的大小。在这里，"!d" 表示一个双精度浮点数（double）的网络字节顺序（big-endian）。
#     # byte_in_double 的值将是双精度浮点数的字节数。
#     timeSent = struct.unpack("!d", recPacket[28: 28 + byte_in_double])[0]
#     # 这行代码的目的是从接收到的 ICMP 回复数据包中提取时间戳信息，并将其解析为一个双精度浮点数。
#     totalDelay = timeReceived - timeSent
#     # 4. Unpack the packet header for useful information, including the ID
#     rec_header = recPacket[20:28]
#     # 它表示从 recPacket 中提取索引为 20 到 27 的字节（不包括第 28 个字节）的子串。
#     replyType, replyCode, replyCkecksum, replyId, replySequence = struct.unpack('!bbHHh', rec_header)
#     # 5. Check that the ID matches between the request and reply
#     if ID == replyId and replyType == ICMP_ECHO_REPLY:
#         # 6. Return total network delay
#         return totalDelay
#     elif timeInRecev > timeout or replyType == ICMP_Type_Overtime:
#         return -3  # ttl overtime/timeout
#     elif replyType == ICMP_Type_Unreachable:
#         return -11  # unreachable
#     else:
#         print("request over time")
#         return -1
#
#
# def sendOnePing(icmpSocket, destinationAddress, ID):  # icmpSocket是在do_one_ping里创建的套接字对象icmp_Socket
#     icmp_checksum = 0
#     # 1. Build ICMP header
#     icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
#     # 这个部分使用 struct.pack 函数将多个值打包成二进制数据。具体来说，'!bbHHh' 是格式字符串，指定了将要打包的数据的类型和顺序。按顺序解释：
#     # ICMP_ECHO_REQUEST: 对应 'b'，一个字节，表示 ICMP 报文的类型。
#     # 0: 对应 'b'，一个字节，表示 ICMP 报文的代码。
#     # icmp_checksum: 对应 'H'，一个无符号短整型，表示校验和（checksum）。
#     # ID: 对应 'H'，一个无符号短整型，表示标识符（ID）。
#     # SEQUENCE: 对应 'h'，一个有符号短整型，表示序列号（SEQUENCE）。
#     # 这个 struct.pack 操作的结果是将这些数值以二进制形式打包成一个 ICMP 请求报文的头部。
#     time_send = struct.pack('!d', time.time())
#     # 因此，struct.pack('!d', time.time()) 将当前时间戳打包成一个符合网络字节序的双精度浮点数的二进制表示。
#     # 这个操作通常用于记录发送 ICMP 请求报文的时间，以便后续计算往返时间（Round-Trip Time, RTT）等网络性能指标。
#
#     # 2. Checksum ICMP packet using given function
#     icmp_checksum = checksum(icmp_header + time_send)
#     # 3. Insert checksum into packet
#     icmp_header = struct.pack('!bbHHh', ICMP_ECHO_REQUEST, 0, icmp_checksum, ID, SEQUENCE)
#
#     # ICMP数据包的校验和通常包括整个ICMP头部和数据负载。对于ICMP Echo请求（Ping）数据包，ICMP头部包括以下字段：
#     # 类型（1字节）： 指定ICMP消息的类型（例如，ICMP Echo请求）。
#     # 代码（1字节）： 提供有关ICMP消息的附加信息（例如，Echo请求的代码通常为0）。
#     # 校验和（2字节）： 此字段最初设置为0，稍后用计算得到的校验和填充。
#     # 标识符（2字节）： 用于将Echo请求与相应的Echo应答进行匹配。
#     # 序列号（2字节）： 每次发送Echo请求时递增。
#     # 除了ICMP头部，ICMP数据包的数据负载也包括在校验和计算中。对于ICMP Echo请求，数据负载通常是时间戳或其他数据
#
#     # 4. Send packet using socket
#     icmp_packet = icmp_header + time_send
#     icmpSocket.sendto(icmp_packet, (destinationAddress, 0))
#
#
# def doOnePing(destinationAddress, timeout):
#     # 1. Create ICMP socket
#     icmpName = socket.getprotobyname('icmp')
#     # 这个函数根据协议名称（'icmp'）获取协议号。在这里，它获取 ICMP 协议的协议号。
#     icmp_Socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmpName)
#     # 这个语句创建了一个新的套接字。参数 socket.AF_INET 指定了地址族（IPv4），socket.SOCK_RAW 表示这是一个原始套接字，而 icmpName 参数指定了使用的协议（ICMP）。
#
#     # 2. Call sendOnePing function
#     sendOnePing(icmp_Socket, destinationAddress, ID)
#     # 3. Call receiveOnePing function
#     totalDelay = receiveOnePing(icmp_Socket, ID, timeout)
#     # 4. Close ICMP socket
#     icmp_Socket.close()
#     # 5. Return total network delay
#     return totalDelay
#
#
# def ping(host, count, timeout):
#     send = 0
#     lost = 0
#     receive = 0
#     maxTime = 0
#     minTime = 1000
#     sumTime = 0
#     # 1. Look up hostname, resolving it to an IP address
#     desIp = socket.gethostbyname(host)
#     global ID
#     ID = os.getpid()
#     # 使用 Python 的 os 模块中的 getpid() 函数获取当前进程的进程ID（Process ID）
#     for i in range(0, count):
#         global SEQUENCE
#         SEQUENCE = i
#         # 2. Call doOnePing function, approximately every second
#         delay = doOnePing(desIp, timeout) * 1000
#         send += 1
#         if delay > 0:
#             receive += 1
#             if maxTime < delay:
#                 maxTime = delay
#             if minTime > delay:
#                 minTime = delay
#             sumTime += delay
#             # 3. Print out the returned delay
#             print("Receive from: " + str(desIp) + ", delay = " + str(int(delay)) + "ms")
#         else:
#             lost += 1
#             print("Fail to connect. ", end="")
#             if delay == -11:
#                 # type = 11, target unreachable
#                 print("Target net/host/port/protocol is unreachable.")
#             elif delay == -3:
#                 # type = 3, ttl overtime
#                 print("Request overtime.")
#             else:
#                 # otherwise, overtime
#                 print("Request overtime.")
#         time.sleep(1)
#     # 4. Continue this process until stopped
#     if receive != 0:
#         avgTime = sumTime / receive
#         recvRate = receive / send * 100.0
#         print(
#             "\nSend: {0}, success: {1}, lost: {2}, rate of success: {3}%.".format(send, receive, lost, recvRate))
#         print(
#             "MaxTime = {0}ms, MinTime = {1}ms, AvgTime = {2}ms".format(int(maxTime), int(minTime), int(avgTime)))
#     else:
#         print("\nSend: {0}, success: {1}, lost: {2}, rate of success: 0.0%".format(send, receive, lost))
#
#
# if __name__ == '__main__':
#     while True:
#         try:
#             hostName = input("Input ip/name of the host you want: ")
#             count = int(input("How many times you want to detect: "))
#             timeout = int(input("Input timeout: "))
#             ping(hostName, count, timeout)
#             break
#         except Exception as e:
#             print(e)
#             continue
