import paramiko
from io import BytesIO


class SFTPClient:

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

    def opend(self):
        return self.sftp is not None

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


class ssh_take_t:
    """进行文件下载"""

    def __init__(self):
        self.clts = {}

    def take(self, host, rmtfile, user=None, pwd=None):
        """下载指定服务器上的指定路径文件.返回值:(文件内容,错误消息),错误消息为空正常."""
        if host not in self.clts:
            self.clts[host] = SFTPClient(host)
            if user or pwd:
                self.clts[host].init(host, user, pwd)

        clt = self.clts[host]
        if not clt.opend():
            msg = clt.open()
            if msg:
                return None, msg

        dat, msg = clt.data_get(rmtfile, 'utf-8')
        if msg:
            clt.close()
            return None, msg

        return dat, ''


class SSHClient:
    """SSH客户端功能对象"""

    def __init__(self, ip=None, username='root', password='123456,', port=22):
        self.clts = {}
        self.ssh = None
        self.init(ip, username, password, port)

    def init(self, ip, username='root', password='123456,', port=22):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def close(self):
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def open(self):
        """打开sftp连接"""
        self.close()
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(hostname=str(self.ip), port=int(self.port), username=self.username, password=self.password)
            return ''
        except Exception as e:
            self.close()
            return str(e)

    def opend(self):
        return self.ssh is not None

    def exec(self, cmd):
        """运行指定服务器上的指定路径文件.返回值:(输出内容,错误消息),错误消息为空正常."""
        dat = None
        msg = ''
        try:
            si, so, se = self.ssh.exec_command(cmd)
            dat = so.readlines()
            msg = se.readlines()
        except Exception as e:
            return None, [str(e)]
        return dat, msg


class ssh_exec_t:
    """在指定服务器上运行指定的命令"""

    def __init__(self):
        self.clts = {}

    def exec(self, host, cmd, user=None, pwd=None):
        """下载指定服务器上的指定路径文件.返回值:(文件内容,错误消息),错误消息为空正常."""
        if host not in self.clts:
            self.clts[host] = SSHClient(host)
            if user or pwd:
                self.clts[host].init(host, user, pwd)

        clt = self.clts[host]
        if not clt.opend():
            msg = clt.open()
            if msg:
                return None, [msg]

        dat, msg = clt.exec(cmd)
        if dat is None:
            clt.close()
            return None, msg

        return dat, msg

