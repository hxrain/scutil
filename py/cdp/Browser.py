"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: BrowserContextID
BrowserContextID = str


# typing: WindowID
WindowID = int


# typing: The state of the browser window.
WindowState = str
WindowStateEnums = ['normal', 'minimized', 'maximized', 'fullscreen']


# object: Bounds
class Bounds(TypingT):
    """
        Browser window bounds information
    """
    def __init__(self):
        # OPTIONAL, The offset from the left edge of the screen to the window in pixels.
        self.left: int = int
        # OPTIONAL, The offset from the top edge of the screen to the window in pixels.
        self.top: int = int
        # OPTIONAL, The window width in pixels.
        self.width: int = int
        # OPTIONAL, The window height in pixels.
        self.height: int = int
        # OPTIONAL, The window state. Default to normal.
        self.windowState: WindowState = WindowState


# typing: PermissionType
PermissionType = str
PermissionTypeEnums = ['accessibilityEvents', 'audioCapture', 'backgroundSync', 'backgroundFetch', 'clipboardReadWrite', 'clipboardSanitizedWrite', 'durableStorage', 'flash', 'geolocation', 'midi', 'midiSysex', 'nfc', 'notifications', 'paymentHandler', 'periodicBackgroundSync', 'protectedMediaIdentifier', 'sensors', 'videoCapture', 'idleDetection', 'wakeLockScreen', 'wakeLockSystem']


# typing: PermissionSetting
PermissionSetting = str
PermissionSettingEnums = ['granted', 'denied', 'prompt']


# object: PermissionDescriptor
class PermissionDescriptor(TypingT):
    """
        Definition of PermissionDescriptor defined in the Permissions API:
        https://w3c.github.io/permissions/#dictdef-permissiondescriptor.
    """
    def __init__(self):
        # Name of permission.See https://cs.chromium.org/chromium/src/third_party/blink/renderer/modules/permissions/permission_descriptor.idl for valid permission names.
        self.name: str = str
        # OPTIONAL, For "midi" permission, may also specify sysex control.
        self.sysex: bool = bool
        # OPTIONAL, For "push" permission, may specify userVisibleOnly.Note that userVisibleOnly = true is the only currently supported type.
        self.userVisibleOnly: bool = bool
        # OPTIONAL, For "wake-lock" permission, must specify type as either "screen" or "system".
        self.type: str = str
        # OPTIONAL, For "clipboard" permission, may specify allowWithoutSanitization.
        self.allowWithoutSanitization: bool = bool


# object: Bucket
class Bucket(TypingT):
    """
        Chrome histogram bucket.
    """
    def __init__(self):
        # Minimum value (inclusive).
        self.low: int = int
        # Maximum value (exclusive).
        self.high: int = int
        # Number of samples.
        self.count: int = int


# object: Histogram
class Histogram(TypingT):
    """
        Chrome histogram.
    """
    def __init__(self):
        # Name.
        self.name: str = str
        # Sum of sample values.
        self.sum: int = int
        # Total number of samples.
        self.count: int = int
        # Buckets.
        self.buckets: List[Bucket] = [Bucket]


import cdp.Target as Target
# ================================================================================
# Browser Domain.
# ================================================================================
class Browser(DomainT):
    """
        The Browser domain defines methods and events for browser managing.
    """
    def __init__(self, drv):
        self.drv = drv


    # func: setPermission
    def setPermission(self,permission:PermissionDescriptor, setting:PermissionSetting, origin:str=None, browserContextId:BrowserContextID=None, **kwargs):
        """
            Set permission settings for given origin.
        Params:
            1. permission: PermissionDescriptor
                Descriptor of permission to override.
            2. setting: PermissionSetting
                Setting of the permission.
            3. origin: str (OPTIONAL)
                Origin the permission applies to, all origins if not specified.
            4. browserContextId: BrowserContextID (OPTIONAL)
                Context to override. When omitted, default browser context is used.
        """
        return self.drv.call(None,'Browser.setPermission',permission=permission, setting=setting, origin=origin, browserContextId=browserContextId, **kwargs)


    # func: grantPermissions
    def grantPermissions(self,permissions:List[PermissionType], origin:str=None, browserContextId:BrowserContextID=None, **kwargs):
        """
            Grant specific permissions to the given origin and reject all others.
        Params:
            1. permissions: List[PermissionType]
            2. origin: str (OPTIONAL)
                Origin the permission applies to, all origins if not specified.
            3. browserContextId: BrowserContextID (OPTIONAL)
                BrowserContext to override permissions. When omitted, default browser context is used.
        """
        return self.drv.call(None,'Browser.grantPermissions',permissions=permissions, origin=origin, browserContextId=browserContextId, **kwargs)


    # func: resetPermissions
    def resetPermissions(self,browserContextId:BrowserContextID=None, **kwargs):
        """
            Reset all permission management for all origins.
        Params:
            1. browserContextId: BrowserContextID (OPTIONAL)
                BrowserContext to reset permissions. When omitted, default browser context is used.
        """
        return self.drv.call(None,'Browser.resetPermissions',browserContextId=browserContextId, **kwargs)


    # func: setDownloadBehavior
    def setDownloadBehavior(self,behavior:str, browserContextId:BrowserContextID=None, downloadPath:str=None, **kwargs):
        """
            Set the behavior when downloading a file.
        Params:
            behaviorEnums = ['deny', 'allow', 'allowAndName', 'default']
            1. behavior: str
                Whether to allow all or deny all download requests, or use default Chrome behavior ifavailable (otherwise deny). |allowAndName| allows download and names files according totheir dowmload guids.
            2. browserContextId: BrowserContextID (OPTIONAL)
                BrowserContext to set download behavior. When omitted, default browser context is used.
            3. downloadPath: str (OPTIONAL)
                The default path to save downloaded files to. This is requred if behavior is set to 'allow'or 'allowAndName'.
        """
        return self.drv.call(None,'Browser.setDownloadBehavior',behavior=behavior, browserContextId=browserContextId, downloadPath=downloadPath, **kwargs)


    # func: close
    def close(self,**kwargs):
        """
            Close browser gracefully.
        """
        return self.drv.call(None,'Browser.close',**kwargs)


    # func: crash
    def crash(self,**kwargs):
        """
            Crashes browser on the main thread.
        """
        return self.drv.call(None,'Browser.crash',**kwargs)


    # func: crashGpuProcess
    def crashGpuProcess(self,**kwargs):
        """
            Crashes GPU process.
        """
        return self.drv.call(None,'Browser.crashGpuProcess',**kwargs)


    # return: getVersionReturn
    class getVersionReturn(ReturnT):
        def __init__(self):
            # Protocol version.
            self.protocolVersion: str = str
            # Product name.
            self.product: str = str
            # Product revision.
            self.revision: str = str
            # User-Agent.
            self.userAgent: str = str
            # V8 version.
            self.jsVersion: str = str


    # func: getVersion
    def getVersion(self,**kwargs) -> getVersionReturn:
        """
            Returns version information.
        Return: getVersionReturn
        """
        return self.drv.call(Browser.getVersionReturn,'Browser.getVersion',**kwargs)


    # return: getBrowserCommandLineReturn
    class getBrowserCommandLineReturn(ReturnT):
        def __init__(self):
            # Commandline parameters
            self.arguments: List[str] = [str]


    # func: getBrowserCommandLine
    def getBrowserCommandLine(self,**kwargs) -> getBrowserCommandLineReturn:
        """
            Returns the command line switches for the browser process if, and only if
            --enable-automation is on the commandline.
        Return: getBrowserCommandLineReturn
        """
        return self.drv.call(Browser.getBrowserCommandLineReturn,'Browser.getBrowserCommandLine',**kwargs)


    # return: getHistogramsReturn
    class getHistogramsReturn(ReturnT):
        def __init__(self):
            # Histograms.
            self.histograms: List[Histogram] = [Histogram]


    # func: getHistograms
    def getHistograms(self,query:str=None, delta:bool=None, **kwargs) -> getHistogramsReturn:
        """
            Get Chrome histograms.
        Params:
            1. query: str (OPTIONAL)
                Requested substring in name. Only histograms which have query as asubstring in their name are extracted. An empty or absent query returnsall histograms.
            2. delta: bool (OPTIONAL)
                If true, retrieve delta since last call.
        Return: getHistogramsReturn
        """
        return self.drv.call(Browser.getHistogramsReturn,'Browser.getHistograms',query=query, delta=delta, **kwargs)


    # return: getHistogramReturn
    class getHistogramReturn(ReturnT):
        def __init__(self):
            # Histogram.
            self.histogram: Histogram = Histogram


    # func: getHistogram
    def getHistogram(self,name:str, delta:bool=None, **kwargs) -> getHistogramReturn:
        """
            Get a Chrome histogram by name.
        Params:
            1. name: str
                Requested histogram name.
            2. delta: bool (OPTIONAL)
                If true, retrieve delta since last call.
        Return: getHistogramReturn
        """
        return self.drv.call(Browser.getHistogramReturn,'Browser.getHistogram',name=name, delta=delta, **kwargs)


    # return: getWindowBoundsReturn
    class getWindowBoundsReturn(ReturnT):
        def __init__(self):
            # Bounds information of the window. When window state is 'minimized', the restored windowposition and size are returned.
            self.bounds: Bounds = Bounds


    # func: getWindowBounds
    def getWindowBounds(self,windowId:WindowID, **kwargs) -> getWindowBoundsReturn:
        """
            Get position and size of the browser window.
        Params:
            1. windowId: WindowID
                Browser window id.
        Return: getWindowBoundsReturn
        """
        return self.drv.call(Browser.getWindowBoundsReturn,'Browser.getWindowBounds',windowId=windowId, **kwargs)


    # return: getWindowForTargetReturn
    class getWindowForTargetReturn(ReturnT):
        def __init__(self):
            # Browser window id.
            self.windowId: WindowID = WindowID
            # Bounds information of the window. When window state is 'minimized', the restored windowposition and size are returned.
            self.bounds: Bounds = Bounds


    # func: getWindowForTarget
    def getWindowForTarget(self,targetId:Target.TargetID=None, **kwargs) -> getWindowForTargetReturn:
        """
            Get the browser window that contains the devtools target.
        Params:
            1. targetId: Target.TargetID (OPTIONAL)
                Devtools agent host id. If called as a part of the session, associated targetId is used.
        Return: getWindowForTargetReturn
        """
        return self.drv.call(Browser.getWindowForTargetReturn,'Browser.getWindowForTarget',targetId=targetId, **kwargs)


    # func: setWindowBounds
    def setWindowBounds(self,windowId:WindowID, bounds:Bounds, **kwargs):
        """
            Set position and/or size of the browser window.
        Params:
            1. windowId: WindowID
                Browser window id.
            2. bounds: Bounds
                New window bounds. The 'minimized', 'maximized' and 'fullscreen' states cannot be combinedwith 'left', 'top', 'width' or 'height'. Leaves unspecified fields unchanged.
        """
        return self.drv.call(None,'Browser.setWindowBounds',windowId=windowId, bounds=bounds, **kwargs)


    # func: setDockTile
    def setDockTile(self,badgeLabel:str=None, image:str=None, **kwargs):
        """
            Set dock tile details, platform-specific.
        Params:
            1. badgeLabel: str (OPTIONAL)
            2. image: str (OPTIONAL)
                Png encoded image.
        """
        return self.drv.call(None,'Browser.setDockTile',badgeLabel=badgeLabel, image=image, **kwargs)



