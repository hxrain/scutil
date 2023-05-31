"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# object: LogEntry
class LogEntry(TypingT):
    """
        Log entry.
    """
    def __init__(self):
        # Log entry source.
        self.source: str = str
        # Log entry severity.
        self.level: str = str
        # Logged text.
        self.text: str = str
        # Timestamp when this entry was added.
        self.timestamp: Runtime.Timestamp = Runtime.Timestamp
        # OPTIONAL, URL of the resource if known.
        self.url: str = str
        # OPTIONAL, Line number in the resource.
        self.lineNumber: int = int
        # OPTIONAL, JavaScript stack trace.
        self.stackTrace: Runtime.StackTrace = Runtime.StackTrace
        # OPTIONAL, Identifier of the network request associated with this entry.
        self.networkRequestId: Network.RequestId = Network.RequestId
        # OPTIONAL, Identifier of the worker associated with this entry.
        self.workerId: str = str
        # OPTIONAL, Call arguments.
        self.args: List[Runtime.RemoteObject] = [Runtime.RemoteObject]


# object: ViolationSetting
class ViolationSetting(TypingT):
    """
        Violation configuration setting.
    """
    def __init__(self):
        # Violation type.
        self.name: str = str
        # Time threshold to trigger upon.
        self.threshold: int = int


# event: entryAdded
class entryAdded(EventT):
    """
        Issued when new message was logged.
    """
    event="Log.entryAdded"
    def __init__(self):
        # The entry.
        self.entry: LogEntry = LogEntry


import cdp.Runtime as Runtime
import cdp.Network as Network
# ================================================================================
# Log Domain.
# ================================================================================
class Log(DomainT):
    """
        Provides access to log entries.
    """
    def __init__(self, drv):
        self.drv = drv


    # func: clear
    def clear(self,**kwargs):
        """
            Clears the log.
        """
        return self.drv.call(None,'Log.clear',**kwargs)


    # func: disable
    def disable(self,**kwargs):
        """
            Disables log domain, prevents further log entries from being reported to the client.
        """
        return self.drv.call(None,'Log.disable',**kwargs)


    # func: enable
    def enable(self,**kwargs):
        """
            Enables log domain, sends the entries collected so far to the client by means of the
            `entryAdded` notification.
        """
        return self.drv.call(None,'Log.enable',**kwargs)


    # func: startViolationsReport
    def startViolationsReport(self,config:List[ViolationSetting], **kwargs):
        """
            start violation reporting.
        Params:
            1. config: List[ViolationSetting]
                Configuration for violations.
        """
        return self.drv.call(None,'Log.startViolationsReport',config=config, **kwargs)


    # func: stopViolationsReport
    def stopViolationsReport(self,**kwargs):
        """
            Stop violation reporting.
        """
        return self.drv.call(None,'Log.stopViolationsReport',**kwargs)



