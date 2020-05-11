# kafka-python
import json

from kafka import KafkaConsumer
from kafka import KafkaProducer


class sender:
    def __init__(self, host, topic):
        self.mq = KafkaProducer(bootstrap_servers=host)
        self.topic = topic
        pass

    def put(self, data, timeout=10, partition=None, topic=None):
        """发送数据到指定的主题与分区,并在超时时间内进行等待.返回值:空串正常;否则为错误信息"""
        if topic is None:
            topic = self.topic

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

    def close(self):
        if self.mq is None:
            return
        self.mq.flush()
        self.mq.close()
        self.mq = None


class recver:
    def __init__(self, Host, topic, GroupID=None):
        self.mq = KafkaConsumer(topic, bootstrap_servers=Host, group_id=GroupID)
        pass

    def get(self, timeout=0.1):
        """从服务器拉取消息,在指定的超时时间内.返回值:字典为结果;字符串为错误信息"""
        try:
            return self.mq.poll(timeout_ms=timeout * 1000)
        except Exception as e:
            return str(e)

    def close(self):
        if self.mq is None:
            return
        self.mq.close()
        self.mq = None
