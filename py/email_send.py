import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


class email_sender_t():
    """基于smtp进行邮件发送的功能封装"""

    def __init__(self, smtp_host, smtp_port=25, is_ssl=False):
        """告知邮件服务器地址"""
        self.host = smtp_host
        self.port = smtp_port
        if is_ssl:
            self.smtp = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            self.smtp = smtplib.SMTP()
        self.message = None
        self.addr_from = None
        self.addr_to = []

    def make_content(self, subject, txt, type='plain', has_att=False):
        """设置主题/正文"""
        if has_att:
            self.message = MIMEMultipart()
            self.message.attach(MIMEText(txt, type, 'utf-8'))
        else:
            self.message = MIMEText(txt, type, 'utf-8')
        self.message['Subject'] = Header(subject, 'utf-8')
        self.addr_to = []

    def make_addr_from(self, addr_from, addr_alias=''):
        """设置发送者地址信息"""
        if addr_alias:
            f = "<%s>%s" % (addr_from, addr_alias)
        else:
            f = "%s" % (addr_from)
        self.message['From'] = Header(f, 'utf-8')
        self.addr_from = addr_from

    def make_addr_to(self, addr_to, addr_alias=''):
        """设置接收者地址信息"""
        if addr_alias:
            f = "<%s>%s" % (addr_to, addr_alias)
        else:
            f = "%s" % (addr_to)
        self.message['To'] = Header(f, 'utf-8')
        self.addr_to.append(addr_to)

    def make_attach(self, fname, data_bytes):
        """添加数据附件"""
        if isinstance(self.message, MIMEMultipart):
            att = MIMEText(data_bytes, 'base64', 'utf-8')
            att["Content-Type"] = 'application/octet-stream'
            att["Content-Disposition"] = 'attachment; filename="%s"' % (fname)
            self.message.attach(att)
        else:
            raise Exception('email attach is disabled.')

    def make_attach_file(self, fname, fpath='./'):
        """添加文件附件"""
        self.make_attach(fname, open('%s%s' % (fpath, fname), 'rb').read())

    def send(self, user, pwd):
        """发送邮件,返回值:告知错误信息,正常应为空."""
        try:
            self.smtp.connect(self.host, self.port)
            self.smtp.login(user, pwd)
            self.smtp.sendmail(self.addr_from, self.addr_to, self.message.as_string())
            self.smtp.quit()
            return ''
        except smtplib.SMTPException as e:
            return str(e)


# 快捷发送邮件功能函数:接收邮箱,发送者邮箱,发送者口令;标题,正文;smtp服务器地址与端口,是否使用ssl模式.
# 返回值:告知错误信息
def send(to_addr, from_addr, from_pwd, title, content,
         smtp_addr='smtp.exmail.qq.com', smtp_port=465, is_ssl=True):
    mail = email_sender_t(smtp_addr, smtp_port, is_ssl)
    mail.make_content(title, content)
    mail.make_addr_from(from_addr)
    mail.make_addr_to(to_addr)
    return mail.send(from_addr, from_pwd)


# 快捷发送邮件附件函数:接收邮箱,发送者邮箱,发送者口令;标题,正文;smtp服务器地址与端口,是否使用ssl模式.
# 返回值:告知错误信息
def send_att(to_addr, from_addr, from_pwd, title, content, filename, filepath='./',
             smtp_addr='smtp.exmail.qq.com', smtp_port=465, is_ssl=True):
    mail = email_sender_t(smtp_addr, smtp_port, is_ssl)
    mail.make_content(title, content, has_att=True)
    mail.make_addr_from(from_addr)
    mail.make_addr_to(to_addr)
    mail.make_attach_file(filename, filepath)
    return mail.send(from_addr, from_pwd)
