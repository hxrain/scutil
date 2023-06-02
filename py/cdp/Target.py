"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: TargetID
TargetID = str


# typing: Unique identifier of attached debugging session.
SessionID = str


# object: TargetInfo
class TargetInfo(TypingT):
    """
        TargetInfo
    """
    def __init__(self):
        # targetId
        self.targetId: TargetID = TargetID
        # type
        self.type: str = str
        # title
        self.title: str = str
        # url
        self.url: str = str
        # Whether the target has an attached client.
        self.attached: bool = bool
        # OPTIONAL, Opener target Id
        self.openerId: TargetID = TargetID
        # Whether the opened window has access to the originating window.
        self.canAccessOpener: bool = bool
        # OPTIONAL, browserContextId
        self.browserContextId: Browser.BrowserContextID = Browser.BrowserContextID


# object: RemoteLocation
class RemoteLocation(TypingT):
    """
        RemoteLocation
    """
    def __init__(self):
        # host
        self.host: str = str
        # port
        self.port: int = int


# event: attachedToTarget
class attachedToTarget(EventT):
    """
        Issued when attached to target because of auto-attach or `attachToTarget` command.
    """
    event="Target.attachedToTarget"
    def __init__(self):
        # Identifier assigned to the session used to send/receive messages.
        self.sessionId: SessionID = SessionID
        # targetInfo
        self.targetInfo: TargetInfo = TargetInfo
        # waitingForDebugger
        self.waitingForDebugger: bool = bool


# event: detachedFromTarget
class detachedFromTarget(EventT):
    """
        Issued when detached from target for any reason (including `detachFromTarget` command). Can be
        issued multiple times per target if multiple sessions have been attached to it.
    """
    event="Target.detachedFromTarget"
    def __init__(self):
        # Detached session identifier.
        self.sessionId: SessionID = SessionID
        # OPTIONAL, Deprecated.
        self.targetId: TargetID = TargetID


# event: receivedMessageFromTarget
class receivedMessageFromTarget(EventT):
    """
        Notifies about a new protocol message received from the session (as reported in
        `attachedToTarget` event).
    """
    event="Target.receivedMessageFromTarget"
    def __init__(self):
        # Identifier of a session which sends a message.
        self.sessionId: SessionID = SessionID
        # message
        self.message: str = str
        # OPTIONAL, Deprecated.
        self.targetId: TargetID = TargetID


# event: targetCreated
class targetCreated(EventT):
    """
        Issued when a possible inspection target is created.
    """
    event="Target.targetCreated"
    def __init__(self):
        # targetInfo
        self.targetInfo: TargetInfo = TargetInfo


# event: targetDestroyed
class targetDestroyed(EventT):
    """
        Issued when a target is destroyed.
    """
    event="Target.targetDestroyed"
    def __init__(self):
        # targetId
        self.targetId: TargetID = TargetID


# event: targetCrashed
class targetCrashed(EventT):
    """
        Issued when a target has crashed.
    """
    event="Target.targetCrashed"
    def __init__(self):
        # targetId
        self.targetId: TargetID = TargetID
        # Termination status type.
        self.status: str = str
        # Termination error code.
        self.errorCode: int = int


# event: targetInfoChanged
class targetInfoChanged(EventT):
    """
        Issued when some information about a target has changed. This only happens between
        `targetCreated` and `targetDestroyed`.
    """
    event="Target.targetInfoChanged"
    def __init__(self):
        # targetInfo
        self.targetInfo: TargetInfo = TargetInfo


import cdp.Browser as Browser
# ================================================================================
# Target Domain.
# ================================================================================
class Target(DomainT):
    """
        Supports additional targets discovery and allows to attach to them.
    """
    def __init__(self, drv):
        self.drv = drv


    # func: activateTarget
    def activateTarget(self,targetId:TargetID, **kwargs):
        """
            Activates (focuses) the target.
        Params:
            1. targetId: TargetID
        """
        return self.drv.call(None,'Target.activateTarget',targetId=targetId, **kwargs)


    # return: attachToTargetReturn
    class attachToTargetReturn(ReturnT):
        def __init__(self):
            # Id assigned to the session.
            self.sessionId: SessionID = SessionID


    # func: attachToTarget
    def attachToTarget(self,targetId:TargetID, flatten:bool=None, **kwargs) -> attachToTargetReturn:
        """
            Attaches to the target with given id.
        Params:
            1. targetId: TargetID
            2. flatten: bool (OPTIONAL)
                Enables "flat" access to the session via specifying sessionId attribute in the commands.We plan to make this the default, deprecate non-flattened mode,and eventually retire it. See crbug.com/991325.
        Return: attachToTargetReturn
        """
        return self.drv.call(Target.attachToTargetReturn,'Target.attachToTarget',targetId=targetId, flatten=flatten, **kwargs)


    # return: attachToBrowserTargetReturn
    class attachToBrowserTargetReturn(ReturnT):
        def __init__(self):
            # Id assigned to the session.
            self.sessionId: SessionID = SessionID


    # func: attachToBrowserTarget
    def attachToBrowserTarget(self,**kwargs) -> attachToBrowserTargetReturn:
        """
            Attaches to the browser target, only uses flat sessionId mode.
        Return: attachToBrowserTargetReturn
        """
        return self.drv.call(Target.attachToBrowserTargetReturn,'Target.attachToBrowserTarget',**kwargs)


    # return: closeTargetReturn
    class closeTargetReturn(ReturnT):
        def __init__(self):
            # success
            self.success: bool = bool


    # func: closeTarget
    def closeTarget(self,targetId:TargetID, **kwargs) -> closeTargetReturn:
        """
            Closes the target. If the target is a page that gets closed too.
        Params:
            1. targetId: TargetID
        Return: closeTargetReturn
        """
        return self.drv.call(Target.closeTargetReturn,'Target.closeTarget',targetId=targetId, **kwargs)


    # func: exposeDevToolsProtocol
    def exposeDevToolsProtocol(self,targetId:TargetID, bindingName:str=None, **kwargs):
        """
            Inject object to the target's main frame that provides a communication
            channel with browser target.


            Injected object will be available as `window[bindingName]`.


            The object has the follwing API:
            - `binding.send(json)` - a method to send messages over the remote debugging protocol
            - `binding.onmessage = json => handleMessage(json)` - a callback that will be called for the protocol notifications and command responses.
        Params:
            1. targetId: TargetID
            2. bindingName: str (OPTIONAL)
                Binding name, 'cdp' if not specified.
        """
        return self.drv.call(None,'Target.exposeDevToolsProtocol',targetId=targetId, bindingName=bindingName, **kwargs)


    # return: createBrowserContextReturn
    class createBrowserContextReturn(ReturnT):
        def __init__(self):
            # The id of the context created.
            self.browserContextId: Browser.BrowserContextID = Browser.BrowserContextID


    # func: createBrowserContext
    def createBrowserContext(self,disposeOnDetach:bool=None, proxyServer:str=None, proxyBypassList:str=None, **kwargs) -> createBrowserContextReturn:
        """
            Creates a new empty BrowserContext. Similar to an incognito profile but you can have more than
            one.
        Params:
            1. disposeOnDetach: bool (OPTIONAL)
                If specified, disposes this context when debugging session disconnects.
            2. proxyServer: str (OPTIONAL)
                Proxy server, similar to the one passed to --proxy-server
            3. proxyBypassList: str (OPTIONAL)
                Proxy bypass list, similar to the one passed to --proxy-bypass-list
        Return: createBrowserContextReturn
        """
        return self.drv.call(Target.createBrowserContextReturn,'Target.createBrowserContext',disposeOnDetach=disposeOnDetach, proxyServer=proxyServer, proxyBypassList=proxyBypassList, **kwargs)


    # return: getBrowserContextsReturn
    class getBrowserContextsReturn(ReturnT):
        def __init__(self):
            # An array of browser context ids.
            self.browserContextIds: List[Browser.BrowserContextID] = [Browser.BrowserContextID]


    # func: getBrowserContexts
    def getBrowserContexts(self,**kwargs) -> getBrowserContextsReturn:
        """
            Returns all browser contexts created with `Target.createBrowserContext` method.
        Return: getBrowserContextsReturn
        """
        return self.drv.call(Target.getBrowserContextsReturn,'Target.getBrowserContexts',**kwargs)


    # return: createTargetReturn
    class createTargetReturn(ReturnT):
        def __init__(self):
            # The id of the page opened.
            self.targetId: TargetID = TargetID


    # func: createTarget
    def createTarget(self,url:str, width:int=None, height:int=None, browserContextId:Browser.BrowserContextID=None, enableBeginFrameControl:bool=None, newWindow:bool=None, background:bool=None, **kwargs) -> createTargetReturn:
        """
            Creates a new page.
        Params:
            1. url: str
                The initial URL the page will be navigated to.
            2. width: int (OPTIONAL)
                Frame width in DIP (headless chrome only).
            3. height: int (OPTIONAL)
                Frame height in DIP (headless chrome only).
            4. browserContextId: Browser.BrowserContextID (OPTIONAL)
                The browser context to create the page in.
            5. enableBeginFrameControl: bool (OPTIONAL)
                Whether BeginFrames for this target will be controlled via DevTools (headless chrome only,not supported on MacOS yet, false by default).
            6. newWindow: bool (OPTIONAL)
                Whether to create a new Window or Tab (chrome-only, false by default).
            7. background: bool (OPTIONAL)
                Whether to create the target in background or foreground (chrome-only,false by default).
        Return: createTargetReturn
        """
        return self.drv.call(Target.createTargetReturn,'Target.createTarget',url=url, width=width, height=height, browserContextId=browserContextId, enableBeginFrameControl=enableBeginFrameControl, newWindow=newWindow, background=background, **kwargs)


    # func: detachFromTarget
    def detachFromTarget(self,sessionId:SessionID=None, targetId:TargetID=None, **kwargs):
        """
            Detaches session with given id.
        Params:
            1. sessionId: SessionID (OPTIONAL)
                Session to detach.
            2. targetId: TargetID (OPTIONAL)
                Deprecated.
        """
        return self.drv.call(None,'Target.detachFromTarget',sessionId=sessionId, targetId=targetId, **kwargs)


    # func: disposeBrowserContext
    def disposeBrowserContext(self,browserContextId:Browser.BrowserContextID, **kwargs):
        """
            Deletes a BrowserContext. All the belonging pages will be closed without calling their
            beforeunload hooks.
        Params:
            1. browserContextId: Browser.BrowserContextID
        """
        return self.drv.call(None,'Target.disposeBrowserContext',browserContextId=browserContextId, **kwargs)


    # return: getTargetInfoReturn
    class getTargetInfoReturn(ReturnT):
        def __init__(self):
            # targetInfo
            self.targetInfo: TargetInfo = TargetInfo


    # func: getTargetInfo
    def getTargetInfo(self,targetId:TargetID=None, **kwargs) -> getTargetInfoReturn:
        """
            Returns information about a target.
        Params:
            1. targetId: TargetID (OPTIONAL)
        Return: getTargetInfoReturn
        """
        return self.drv.call(Target.getTargetInfoReturn,'Target.getTargetInfo',targetId=targetId, **kwargs)


    # return: getTargetsReturn
    class getTargetsReturn(ReturnT):
        def __init__(self):
            # The list of targets.
            self.targetInfos: List[TargetInfo] = [TargetInfo]


    # func: getTargets
    def getTargets(self,**kwargs) -> getTargetsReturn:
        """
            Retrieves a list of available targets.
        Return: getTargetsReturn
        """
        return self.drv.call(Target.getTargetsReturn,'Target.getTargets',**kwargs)


    # func: sendMessageToTarget
    def sendMessageToTarget(self,message:str, sessionId:SessionID=None, targetId:TargetID=None, **kwargs):
        """
            Sends protocol message over session with given id.
            Consider using flat mode instead; see commands attachToTarget, setAutoAttach,
            and crbug.com/991325.
        Params:
            1. message: str
            2. sessionId: SessionID (OPTIONAL)
                Identifier of the session.
            3. targetId: TargetID (OPTIONAL)
                Deprecated.
        """
        return self.drv.call(None,'Target.sendMessageToTarget',message=message, sessionId=sessionId, targetId=targetId, **kwargs)


    # func: setAutoAttach
    def setAutoAttach(self,autoAttach:bool, waitForDebuggerOnStart:bool, flatten:bool=None, **kwargs):
        """
            Controls whether to automatically attach to new targets which are considered to be related to
            this one. When turned on, attaches to all existing related targets as well. When turned off,
            automatically detaches from all currently attached targets.
        Params:
            1. autoAttach: bool
                Whether to auto-attach to related targets.
            2. waitForDebuggerOnStart: bool
                Whether to pause new targets when attaching to them. Use `Runtime.runIfWaitingForDebugger`to run paused targets.
            3. flatten: bool (OPTIONAL)
                Enables "flat" access to the session via specifying sessionId attribute in the commands.We plan to make this the default, deprecate non-flattened mode,and eventually retire it. See crbug.com/991325.
        """
        return self.drv.call(None,'Target.setAutoAttach',autoAttach=autoAttach, waitForDebuggerOnStart=waitForDebuggerOnStart, flatten=flatten, **kwargs)


    # func: setDiscoverTargets
    def setDiscoverTargets(self,discover:bool, **kwargs):
        """
            Controls whether to discover available targets and notify via
            `targetCreated/targetInfoChanged/targetDestroyed` events.
        Params:
            1. discover: bool
                Whether to discover available targets.
        """
        return self.drv.call(None,'Target.setDiscoverTargets',discover=discover, **kwargs)


    # func: setRemoteLocations
    def setRemoteLocations(self,locations:List[RemoteLocation], **kwargs):
        """
            Enables target discovery for the specified locations, when `setDiscoverTargets` was set to
            `true`.
        Params:
            1. locations: List[RemoteLocation]
                List of remote locations.
        """
        return self.drv.call(None,'Target.setRemoteLocations',locations=locations, **kwargs)



