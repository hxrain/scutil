# -*- coding: utf-8 -*-

# kafka-python
import json
import time
import ssl
from kafka import KafkaConsumer
from kafka import KafkaProducer


class sasl_plain:
    """用于身份验证的信息记录"""

    def __init__(self, user, pwd):
        self.user = user
        self.pwd = pwd
        self.security_protocol = 'SASL_PLAINTEXT'  # 安全加密模式
        self.sasl_mechanism = 'PLAIN'
        self.ssl_cafile = None  # ssl/ca证书文件
        self.ssl_keyfile = None  # ssl/key文件
        self.ssl_content = None  # ssl上下文

    def load_ssl_ca(self, cafile):
        """使用ssl上下文模式,装载ca文件"""
        self.security_protocol = 'SASL_SSL'
        try:
            self.ssl_content = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            self.ssl_content.verify_mode = ssl.CERT_REQUIRED
            self.ssl_content.load_verify_locations(cafile)
            return ''
        except Exception as e:
            msg = 'load ssl ca <%s> fail: %s' % (cafile, str(e))
            print(msg)
            return msg


class sender:
    """kafka消息生产者客户端,发送消息到服务器"""

    def __init__(self, host, topic, auth=None):
        self.mq = None
        self.host = host
        self.topic = topic
        self.auth = auth
        msg = self.open()
        if msg:
            print(msg)

    def is_valid(self):
        return self.mq is not None

    def open(self):
        if self.mq is not None:
            return ''

        cfg = {
            'max_request_size': 16 * 1024 * 1024,
            'buffer_memory': 64 * 1024 * 1024,
            'batch_size': 2 * 1024 * 1024,
            'compression_type': 'gzip'
        }

        try:
            if isinstance(self.auth, sasl_plain):
                self.mq = KafkaProducer(bootstrap_servers=self.host, sasl_mechanism=self.auth.sasl_mechanism, security_protocol=self.auth.security_protocol,
                                        ssl_cafile=self.auth.ssl_cafile, ssl_context=self.auth.ssl_content, ssl_keyfile=self.auth.ssl_keyfile,
                                        sasl_plain_username=self.auth.user, sasl_plain_password=self.auth.pwd, **cfg)
            else:
                self.mq = KafkaProducer(bootstrap_servers=self.host)
        except Exception as e:
            return str(e)
        return ''

    def put(self, data, timeout=10, partition=None, topic=None, key=None):
        """发送数据到指定的主题与分区,并在超时时间内进行等待.返回值:空串正常;否则为错误信息"""
        if topic is None:
            topic = self.topic

        msg = self.open()
        if msg:
            return msg

        try:
            # 对待发送数据进行必要的序列化
            if isinstance(data, dict):
                data = json.dumps(data, ensure_ascii=False)
            # 发起数据的提交
            r = self.mq.send(topic, data.encode('utf-8'), key=key, partition=partition)
            # 等待服务器响应
            if timeout:
                r.get(timeout)

            return ''
        except Exception as e:
            return str(e)

    def commit(self, timeout=None):
        """立即刷新发送缓冲区,强制推送消息到服务器"""
        msg = self.open()
        if msg:
            return msg

        try:
            self.mq.flush(timeout)
            return ''
        except Exception as e:
            return str(e)

    def close(self):
        if self.mq is None:
            return
        self.commit()
        self.mq.close()
        self.mq = None

au=sasl_plain('admin','yuchen979')
au.sasl_mechanism='SCRAM-SHA-256'
sr=sender(['172.17.100.139:9092'],'qlm-info',au)
sr.open()

class receiver:
    """kafka消费者客户端,从服务器接收消息"""

    def __init__(self, Host, topic, GroupID=None, auth=None, logger=None):
        self.mq = None
        self.host = Host
        self.topic = topic
        self.groupid = GroupID
        self.auth = auth
        msg = self.open()
        if msg:
            if logger:
                logger.warning('%s kafka connect fail: %s' % (Host, msg))
            else:
                print(msg)

    def is_valid(self):
        return self.mq is not None

    def open(self):
        if self.mq is not None:
            return ''

        try:
            if isinstance(self.auth, sasl_plain):
                self.mq = KafkaConsumer(self.topic, bootstrap_servers=self.host, group_id=self.groupid, sasl_mechanism="PLAIN", security_protocol='SASL_PLAINTEXT',
                                        sasl_plain_username=self.auth.user, sasl_plain_password=self.auth.pwd)
            else:
                self.mq = KafkaConsumer(self.topic, bootstrap_servers=self.host, group_id=self.groupid)
        except Exception as e:
            return str(e)
        return ''

    @staticmethod
    def conv_info(rcvdata):
        rst = []
        for key in rcvdata:
            lst = rcvdata[key]
            for d in lst:
                info = {'topic': key.topic, 'partition': key.partition, 'offset': d.offset, 'timestamp': d.timestamp, 'key': d.key, 'value': d.value}
                rst.append(info)
        return rst

    def get(self, timeout=0.5, ack=True):
        """从服务器拉取消息,在指定的超时时间内.返回值:字典为结果;字符串为错误信息"""
        msg = self.open()
        if msg:
            return None, msg

        try:
            dat = self.mq.poll(timeout_ms=timeout * 1000, update_offsets=ack)
            return self.conv_info(dat), ''
        except Exception as e:
            return None, str(e)

    def commit(self, offsets=None):
        """如果get方法没有给出ack=True,则需要调用本方法手动提交本次消费的偏移量;返回值:空串正常;否则为错误消息."""
        msg = self.open()
        if msg:
            return msg

        try:
            self.mq.commit(offsets)
            return ''
        except Exception as e:
            return str(e)

    def close(self):
        if self.mq is None:
            return
        self.mq.close()
        self.mq = None


class mq_pusher_t:
    """对kafka发送者进行业务包装,组成完整的发送功能对象"""

    def __init__(self, addr, topic, logger=None, auth=None):
        self.sender = sender(addr.split(','), topic, auth)
        self.logger = logger
        self.total = 0  # 推送的总数
        self.round = 0  # 推送的轮次
        self.count = 0  # 本次推送数
        # logging.getLogger("kafka").setLevel(logging.INFO) #调整kafka客户端日志输出级别

    def ready(self):
        """每轮调用之前,进行计数器调整"""
        self.round += 1

    def put(self, datas):
        """进行逐条推送.返回值:None完成;其他为推送失败的信息对象"""
        bt = time.time()
        self.count = 0
        for dat in datas:
            if dat:
                msg = self.sender.put(dat)
                if msg != '':
                    if self.logger:
                        self.logger.warning('mq push fail <%s>' % msg)
                    return dat
                self.total += 1
                self.count += 1
        ut = time.time() - bt
        if self.logger:
            self.logger.info('ROUND<%d>|COUNT(%d)|TOTAL(%d):time(%d ms)' % (self.round, self.count, self.total, int(ut * 1000)))
        return None

    def put2(self, datas):
        """进行批量提交推送.返回值:(dat,idx);dat为None完成,其他为推送失败的信息对象"""
        bt = time.time()
        self.count = 0
        for idx, dat in enumerate(datas):
            if dat:
                msg = self.sender.put(dat, timeout=None)  # 逐条提交时不进行应答等待
                if msg != '':
                    if self.logger:
                        self.logger.warning('mq push fail <%s>' % msg)
                    return dat, idx
                self.total += 1
                self.count += 1
        self.sender.commit()  # 等待批量提交完成.
        ut = time.time() - bt
        if self.logger:
            self.logger.info('ROUND<%d>|COUNT(%d)|TOTAL(%d):time(%d ms)' % (self.round, self.count, self.total, int(ut * 1000)))
        return None, -1

    def close(self):
        self.sender.close()


def make_kafka_pusher(user, pswd, addr, topic, logger=None):
    """kafka推送器初始化函数"""
    if user or pswd:
        mqauth = sasl_plain(user, pswd)
    else:
        mqauth = None
    return mq_pusher_t(addr, topic, logger, mqauth)
