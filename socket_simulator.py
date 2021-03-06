import multiprocessing
import random
import socket
import threading
from Queue import Empty
from collections import Counter

import time

import gc

from ip import IPDatagram
from logger import LOG
from tcp import TCPSegment


class SocketSimulator:
    def __init__(self, host=None, timeout=180, tick=2):
        # IP
        self.host = host
        self.ip_src = socket.inet_aton(self.host.intList[0].ip_addr)
        self.ip_dest = ''
        # port
        self.port_src = random.randint(0x7530, 0xffff)
        self.port_dest = 80
        # TCP
        self.tcp_seq = random.randint(0x0001, 0xffff)
        self.tcp_ack_seq = 0
        self.prev_data = ''
        self.tcp_cwind = 1024
        # size of the receive buffer
        self.tcp_adwind = 65535
        self.recv_buf = []
        self.tmp_buf = {}
        self.tick = tick
        self.max_retry = timeout / tick
        self.metrics = Counter(send=0, recv=0, erecv=0,
                               retry=0, cksumfail=0)
        self.ack_queue = multiprocessing.Queue()
        self.fin_queue = multiprocessing.Queue()
        self.receiving_tcp = threading.Thread(target=self.receive_tcp)
        self.receiving_tcp.start()

    def receive_tcp(self):
        while True:
            tcp_data = self.recv()
            if tcp_data:
                print self.host.name + ":received message:" + tcp_data

    def connect(self, (dest_ip, port)):
        '''
        Connect to the given hostname and port
        '''
        self.ip_dest = socket.inet_aton(dest_ip)
        self.port_dest = port
        # 3-way handshake
        self._tcp_handshake()
        print "........client........%s has connected with %s........." %\
              (self.host.name, socket.inet_ntoa(self.ip_dest))

    def send(self, data=''):
        '''
        Send all the given data, the TCP congestion control
        goes here, so that data might be sliced
        '''
        send_length = 0
        total_len = len(data)
        while send_length < total_len:
            self.tcp_cwind += 1/self.tcp_cwind
            self._send(data[send_length:(send_length + self.tcp_cwind)], ack=1, psh=1)
            # update TCP seq
            if (send_length + self.tcp_cwind) > total_len:
                self.tcp_seq += (total_len - send_length)
            else:
                self.tcp_seq += self.tcp_cwind
            send_length += self.tcp_cwind
        return total_len

    def recv(self, bufsize=8192):
        '''
        Receive the data with the given buffer size,
        the receiving buffer gets maintained here
        '''
        receive_length = 0
        tcp_data = ''
        times = 1 + bufsize / self.tcp_adwind
        fin = False
        while times:
            while receive_length < self.tcp_adwind:
                tcp_segment = self._recv(self.max_retry)
                if tcp_segment is None:
                    raise RuntimeError('Connection timeout')
                if not tcp_segment.tcp_fpsh:
                    if tcp_segment.tcp_fack:
                        self.ack_queue.put(tcp_segment)
                    if tcp_segment.tcp_ffin:
                        self.fin_queue.put(tcp_segment)
                    return None
                elif tcp_segment.tcp_fack:
                    if tcp_segment.tcp_seq == self.tcp_ack_seq:
                        LOG.debug('Recv in-order TCP segment')
                        receive_length += self._enbuf(tcp_segment)
                        self._send(ack=1)
                        if tcp_segment.tcp_ffin:
                            fin = True
                            break
                        while self.tcp_ack_seq in self.tmp_buf:
                            tcp_segment = self.tmp_buf[self.tcp_ack_seq]
                            receive_length += self._enbuf(tcp_segment)
                            if tcp_segment.tcp_ffin:
                                fin = True
                                break
                        self._send(ack=1)
                        if tcp_segment.data:
                            self.host.chat_window.message_queue.put(tcp_segment.data)
                        if fin:
                            self.fin_queue.put(tcp_segment)
                            break
                    elif (tcp_segment.tcp_seq > self.tcp_ack_seq) and \
                            (tcp_segment.tcp_seq not in self.tmp_buf):
                        LOG.debug('Recv out-of-order TCP segment')
                        self.tmp_buf[tcp_segment.tcp_seq] = tcp_segment
                else:
                    continue
            tcp_data = ''.join([tcp_data, self._debuf()])
            if fin:
                return tcp_data
            times -= 1
        return tcp_data

    def close(self):
        '''
        Tear down the raw socket connection
        '''
        self._tcp_teardown()
        # clear all queues
        while not self.ack_queue.empty():
            self.ack_queue.get()
        while not self.fin_queue.empty():
            self.fin_queue.get()
        self.host.chat_window.current_socket = None

    def _tcp_handshake(self):
        '''
        Wrap the TCP 3-way handshake procedure
        '''
        self._send(syn=1)
        tcp_segment = self.recv_non_psh(self.ack_queue)
        # check timeout
        if tcp_segment is None:
            raise RuntimeError('TCP handshake failed, connection timeout')
        # check server ACK | SYN
        if not (tcp_segment.tcp_fack and tcp_segment.tcp_fsyn):
            raise RuntimeError('TCP handshake failed, bad server response')
        # save next ACK seq
        self.tcp_seq = tcp_segment.tcp_ack_seq
        self.tcp_ack_seq = tcp_segment.tcp_seq + 1
        self._send(ack=1)

    def _send(self, data='', retry=False, urg=0, ack=0, psh=0,
              rst=0, syn=0, fin=0):
        '''
        Send the given data within a packet the set TCP flags,
        return the number of bytes sent.
        '''

        if retry:
            self.tcp_cwind /= 2
            return self.host.send_datagram(self.prev_data)
        else:
            # build TCP segment
            tcp_segment = TCPSegment(ip_src_addr=self.ip_src,
                                     ip_dest_addr=self.ip_dest,
                                     tcp_src_port=self.port_src,
                                     tcp_dest_port=self.port_dest,
                                     tcp_seq=self.tcp_seq,
                                     tcp_ack_seq=self.tcp_ack_seq,
                                     tcp_furg=urg, tcp_fack=ack, tcp_fpsh=psh,
                                     tcp_frst=rst, tcp_fsyn=syn, tcp_ffin=fin,
                                     tcp_adwind=self.tcp_cwind, data=data)
            ip_data = tcp_segment.pack()
            print self.host.name + ":client send TCP: " + tcp_segment.__repr__()
            # build IP datagram
            ip_datagram = IPDatagram(ip_src_addr=self.ip_src,
                                     ip_dest_addr=self.ip_dest,
                                     data=ip_data)

            eth_data = ip_datagram.pack()
            self.metrics['send'] += 1
            self.prev_data = eth_data
            return self.host.send_datagram(eth_data)

    def _recv(self, max_retry, bufsize=1500):
        '''
        Receive a packet with the given buffer size, will not retry
        for per-packet failure until using up max retry
        '''
        while max_retry:
            self.metrics['recv'] += 1
            # wait with timeout for the readable socket
            # socket is ready to read, no timeout
            try:
                # process Ethernet frame
                ip_bytes = self.host.tcp_ip_queue.get()
                ip_datagram = IPDatagram(self.ip_src, self.ip_dest)
                ip_datagram.unpack(ip_bytes)
                # IP filtering
                if not self._ip_expected(ip_datagram):
                    continue
                # IP checksum
                if not ip_datagram.verify_checksum():
                    return self._retry(bufsize, max_retry)
                # process TCP segment
                ip_data = ip_datagram.data
                tcp_segment = TCPSegment(self.ip_src, self.ip_dest)
                tcp_segment.unpack(ip_data)
                tcp_segment.pack()
                print self.host.name + ": client receive TCP: " + tcp_segment.__repr__()
                # TCP filtering
                if not self._tcp_expected(tcp_segment):
                    continue
                # TCP checksum
                # if not tcp_segment.verify_checksum():
                #     self.metrics['cksumfail'] += 1
                #     return self._retry(bufsize, max_retry)
                LOG.debug('Recv: %s' % tcp_segment)
                self.metrics['erecv'] += 1
                return tcp_segment
            # timeout, re-_send and re-_recv
            except Empty:
                return self._retry(bufsize, max_retry)
        return None

    def recv_non_psh(self, queue):
        time.sleep(0.1)
        while True:
            try:
                tcp_segment = queue.get(0)
                if tcp_segment.tcp_dest_port == self.port_src:
                    return tcp_segment
            except Empty:
                pass
            finally:
                time.sleep(0.1)

    def _ip_expected(self, ip_datagram):
        '''
        Return True if the received ip_datagram is the
        expected one.
        1. ip_ver should be 4
        2. ip_src_addr should be the expected dest machine
        3. ip_proto identifier should be TCP(6)
        '''
        if ip_datagram.ip_ver != 4:
            return False
        elif ip_datagram.ip_src_addr != self.ip_dest:
            return False
        elif ip_datagram.ip_proto != socket.IPPROTO_TCP:
            return False
        else:
            return True

    def _retry(self, bufsize, max_retry):
        '''
        Re-_send and re-_recv with the max retry -1
        Mutual recursion with self._recv(bufsize)
        '''
        self.metrics['retry'] += 1
        max_retry -= 1
        self._send(retry=True, ack=1)
        return self._recv(bufsize, max_retry)

    def _enbuf(self, tcp_segment):
        '''
        Put the in-order TCP payload into recv buffer
        '''
        self.recv_buf.append(tcp_segment.data)
        elen = len(tcp_segment.data)
        self.tcp_seq = tcp_segment.tcp_ack_seq
        self.tcp_ack_seq += elen
        # self._send(ack=1)
        return elen

    def _debuf(self):
        '''
        Dump all cached TCP payload out from the recv buffer
        '''
        tcp_data = ''
        for data_slice in self.recv_buf:
            tcp_data = ''.join([tcp_data, data_slice])
        del self.recv_buf[:]
        self.tmp_buf.clear()
        return tcp_data

    def _tcp_expected(self, tcp_segment):
        '''
        Return True if the received tcp_segment is the
        expected one.
        1. tcp_src_port should be the local dest port
        2. tcp_dest_port should be the local src port
        3. raise error if server resets the connection
        4. checksum must be valid
        '''
        if tcp_segment.tcp_src_port != self.port_dest:
            return False
        elif tcp_segment.tcp_dest_port != self.port_src:
            return False
        elif tcp_segment.tcp_frst:
            raise RuntimeError('Connection reset by server')
        else:
            return True

    def dump_metrics(self):
        '''
        Dump the metrics counters for debug usage
        '''
        dump = '\n'.join('\t%s: %d' % (k, v) for (k, v)
                         in self.metrics.items())
        return dump, self.metrics

    def _tcp_teardown(self):
        '''
        Tear down the stateful TCP connection before explicitly
        closing the raw socket
        '''
        self._send(fin=1, ack=1)
        tcp_segment = self.recv_non_psh(self.ack_queue)
        # check timeout
        if tcp_segment is None:
            raise RuntimeError('TCP teardown failed, connection timeout')
        # check server ACK
        if not tcp_segment.tcp_fack:
            raise RuntimeError('TCP teardown failed, server not ACK to FIN')
        tcp_segment = self.recv_non_psh(self.fin_queue)
        # check server FIN
        if not tcp_segment.tcp_ffin:
            raise RuntimeError('TCP teardown failed, server not FIN')
        self.tcp_seq = tcp_segment.tcp_ack_seq
        self.tcp_ack_seq = tcp_segment.tcp_seq + 1
        self._send(ack=1)
