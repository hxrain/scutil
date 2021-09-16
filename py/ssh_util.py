import paramiko
from io import BytesIO


class SSHClient:

    def __init__(self, ip=None, username='root', password='123456,', port=22):
        self.sftp = None
        self.transport = None
        self.init(ip, username, password, port)

    def init(self, ip, username='root', password='123456,', port=22):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def open(self):
        """打开sftp连接"""
        self.close()
        try:
            self.transport = paramiko.Transport((str(self.ip), int(self.port)))
            self.transport.connect(username=self.username, password=self.password)
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            return ''
        except Exception as e:
            return str(e)

    def file_put(self, localhost_file, server_file):
        """将本地文件上传至服务器"""
        try:
            self.sftp.put(localhost_file, server_file)
            return ''
        except Exception as e:
            return str(e)

    def data_put(self, data, server_file):
        """将本地文件上传至服务器"""
        try:
            fl = BytesIO(data)
            self.sftp.putfo(fl, server_file)
            return ''
        except Exception as e:
            return str(e)

    def file_get(self, localhost_file, server_file):
        """将服务器文件下载至本地"""
        try:
            self.sftp.get(server_file, localhost_file)
            return ''
        except Exception as e:
            return str(e)

    def data_get(self, server_file, encode=''):
        """将服务器文件下载至本地,返回值(data,msg),msg为空正常."""
        try:
            fl = BytesIO()
            self.sftp.getfo(server_file, fl)
            if encode:
                return fl.getvalue().decode(encode), ''
            else:
                return fl.getvalue(), ''
        except Exception as e:
            return None, str(e)

    def close(self):
        if self.sftp:
            self.sftp = None
        if self.transport:
            self.transport.close()
            self.transport = None
