# kafka-python
import json

from kafka import KafkaConsumer
from kafka import KafkaProducer


class sasl_plain:
    """用于身份验证的信息记录"""

    def __init__(self, user, pwd):
        self.user = user
        self.pwd = pwd


class sender:
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
            'max_request_size': 8 * 1024 * 1024,
            'buffer_memory': 64 * 1024 * 1024,
            'batch_size': 2 * 1024 *1024
        }

        try:
            if isinstance(self.auth, sasl_plain):
                self.mq = KafkaProducer(bootstrap_servers=self.host, sasl_mechanism="PLAIN", security_protocol='SASL_PLAINTEXT',
                                        sasl_plain_username=self.auth.user, sasl_plain_password=self.auth.pwd, **cfg)
            else:
                self.mq = KafkaProducer(bootstrap_servers=self.host)
        except Exception as e:
            return str(e)
        return ''

    def put(self, data, timeout=10, partition=None, topic=None):
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
            r = self.mq.send(topic, data.encode('utf-8'), partition)
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


class receiver:
    def __init__(self, Host, topic, GroupID=None, auth=None):
        self.mq = None
        self.host = Host
        self.topic = topic
        self.groupid = GroupID
        self.auth = auth
        msg = self.open()
        if msg:
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
                self.mq = KafkaConsumer(self.topic, bootstrap_servers=self.host, group_id=groupid)
        except Exception as e:
            return str(e)
        return ''

    def get(self, timeout=0.1, ack=True):
        """从服务器拉取消息,在指定的超时时间内.返回值:字典为结果;字符串为错误信息"""
        msg = self.open()
        if msg:
            return msg

        try:
            return self.mq.poll(timeout_ms=timeout * 1000, update_offsets=ack)
        except Exception as e:
            return str(e)

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
