"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# --------------------------------------------------------------------------------
# Emulation Domain Typing.
# --------------------------------------------------------------------------------
# object: ScreenOrientation
class ScreenOrientation(TypingT):
    """
        Screen orientation.
    """
    def __init__(self):
        # Orientation type.
        self.type: str = str
        # Orientation angle.
        self.angle: int = int


# object: DisplayFeature
class DisplayFeature(TypingT):
    """
        DisplayFeature
    """
    def __init__(self):
        # Orientation of a display feature in relation to screen
        self.orientation: str = str
        # The offset from the screen origin in either the x (for verticalorientation) or y (for horizontal orientation) direction.
        self.offset: int = int
        # A display feature may mask content such that it is not physicallydisplayed - this length along with the offset describes this area.A display feature that only splits content will have a 0 mask_length.
        self.maskLength: int = int


# object: MediaFeature
class MediaFeature(TypingT):
    """
        MediaFeature
    """
    def __init__(self):
        # name
        self.name: str = str
        # value
        self.value: str = str


# typing: advance: If the scheduler runs out of immediate work, the virtual time base may fast forward toallow the next delayed task (if any) to run; pause: The virtual time base may not advance;pauseIfNetworkFetchesPending: The virtual time base may not advance if there are any pendingresource fetches.
VirtualTimePolicy = str
VirtualTimePolicyEnums = ['advance', 'pause', 'pauseIfNetworkFetchesPending']


# object: UserAgentBrandVersion
class UserAgentBrandVersion(TypingT):
    """
        Used to specify User Agent Cient Hints to emulate. See https://wicg.github.io/ua-client-hints
    """
    def __init__(self):
        # brand
        self.brand: str = str
        # version
        self.version: str = str


# object: UserAgentMetadata
class UserAgentMetadata(TypingT):
    """
        Used to specify User Agent Cient Hints to emulate. See https://wicg.github.io/ua-client-hints
    """
    def __init__(self):
        # brands
        self.brands: List[UserAgentBrandVersion] = [UserAgentBrandVersion]
        # fullVersion
        self.fullVersion: str = str
        # platform
        self.platform: str = str
        # platformVersion
        self.platformVersion: str = str
        # architecture
        self.architecture: str = str
        # model
        self.model: str = str
        # mobile
        self.mobile: bool = bool


# --------------------------------------------------------------------------------
# Emulation Domain Event.
# --------------------------------------------------------------------------------
# event: virtualTimeBudgetExpired
class virtualTimeBudgetExpired(EventT):
    """
        Notification sent after the virtual time budget for the current VirtualTimePolicy has run out.
    """
    event="Emulation.virtualTimeBudgetExpired"
    def __init__(self):
        pass


from cdp import DOM
from cdp import Page
from cdp import Runtime
from cdp import Network
# ================================================================================
# Emulation Domain Class.
# ================================================================================
class Emulation(DomainT):
    """
        This domain emulates different environments for the page.
    """
    def __init__(self, drv):
        self.drv = drv


    # return: canEmulateReturn
    class canEmulateReturn(ReturnT):
        def __init__(self):
            # True if emulation is supported.
            self.result: bool = bool


    # func: canEmulate
    def canEmulate(self,**kwargs) -> canEmulateReturn:
        """
            Tells whether emulation is supported.
        Return: canEmulateReturn
        """
        return self.drv.call(Emulation.canEmulateReturn,'Emulation.canEmulate',**kwargs)


    # func: clearDeviceMetricsOverride
    def clearDeviceMetricsOverride(self,**kwargs):
        """
            Clears the overriden device metrics.
        """
        return self.drv.call(None,'Emulation.clearDeviceMetricsOverride',**kwargs)


    # func: clearGeolocationOverride
    def clearGeolocationOverride(self,**kwargs):
        """
            Clears the overriden Geolocation Position and Error.
        """
        return self.drv.call(None,'Emulation.clearGeolocationOverride',**kwargs)


    # func: resetPageScaleFactor
    def resetPageScaleFactor(self,**kwargs):
        """
            Requests that page scale factor is reset to initial values.
        """
        return self.drv.call(None,'Emulation.resetPageScaleFactor',**kwargs)


    # func: setFocusEmulationEnabled
    def setFocusEmulationEnabled(self,enabled:bool, **kwargs):
        """
            Enables or disables simulating a focused and active page.
        Params:
            1. enabled: bool
                Whether to enable to disable focus emulation.
        """
        return self.drv.call(None,'Emulation.setFocusEmulationEnabled',enabled=enabled, **kwargs)


    # func: setCPUThrottlingRate
    def setCPUThrottlingRate(self,rate:int, **kwargs):
        """
            Enables CPU throttling to emulate slow CPUs.
        Params:
            1. rate: int
                Throttling rate as a slowdown factor (1 is no throttle, 2 is 2x slowdown, etc).
        """
        return self.drv.call(None,'Emulation.setCPUThrottlingRate',rate=rate, **kwargs)


    # func: setDefaultBackgroundColorOverride
    def setDefaultBackgroundColorOverride(self,color:DOM.RGBA=None, **kwargs):
        """
            Sets or clears an override of the default background color of the frame. This override is used
            if the content does not specify one.
        Params:
            1. color: DOM.RGBA (OPTIONAL)
                RGBA of the default background color. If not specified, any existing override will becleared.
        """
        return self.drv.call(None,'Emulation.setDefaultBackgroundColorOverride',color=color, **kwargs)


    # func: setDeviceMetricsOverride
    def setDeviceMetricsOverride(self,width:int, height:int, deviceScaleFactor:int, mobile:bool, scale:int=None, screenWidth:int=None, screenHeight:int=None, positionX:int=None, positionY:int=None, dontSetVisibleSize:bool=None, screenOrientation:ScreenOrientation=None, viewport:Page.Viewport=None, displayFeature:DisplayFeature=None, **kwargs):
        """
            Overrides the values of device screen dimensions (window.screen.width, window.screen.height,
            window.innerWidth, window.innerHeight, and "device-width"/"device-height"-related CSS media
            query results).
        Params:
            1. width: int
                Overriding width value in pixels (minimum 0, maximum 10000000). 0 disables the override.
            2. height: int
                Overriding height value in pixels (minimum 0, maximum 10000000). 0 disables the override.
            3. deviceScaleFactor: int
                Overriding device scale factor value. 0 disables the override.
            4. mobile: bool
                Whether to emulate mobile device. This includes viewport meta tag, overlay scrollbars, textautosizing and more.
            5. scale: int (OPTIONAL)
                Scale to apply to resulting view image.
            6. screenWidth: int (OPTIONAL)
                Overriding screen width value in pixels (minimum 0, maximum 10000000).
            7. screenHeight: int (OPTIONAL)
                Overriding screen height value in pixels (minimum 0, maximum 10000000).
            8. positionX: int (OPTIONAL)
                Overriding view X position on screen in pixels (minimum 0, maximum 10000000).
            9. positionY: int (OPTIONAL)
                Overriding view Y position on screen in pixels (minimum 0, maximum 10000000).
            10. dontSetVisibleSize: bool (OPTIONAL)
                Do not set visible view size, rely upon explicit setVisibleSize call.
            11. screenOrientation: ScreenOrientation (OPTIONAL)
                Screen orientation override.
            12. viewport: Page.Viewport (OPTIONAL)
                If set, the visible area of the page will be overridden to this viewport. This viewportchange is not observed by the page, e.g. viewport-relative elements do not change positions.
            13. displayFeature: DisplayFeature (OPTIONAL)
                If set, the display feature of a multi-segment screen. If not set, multi-segment supportis turned-off.
        """
        return self.drv.call(None,'Emulation.setDeviceMetricsOverride',width=width, height=height, deviceScaleFactor=deviceScaleFactor, mobile=mobile, scale=scale, screenWidth=screenWidth, screenHeight=screenHeight, positionX=positionX, positionY=positionY, dontSetVisibleSize=dontSetVisibleSize, screenOrientation=screenOrientation, viewport=viewport, displayFeature=displayFeature, **kwargs)


    # func: setScrollbarsHidden
    def setScrollbarsHidden(self,hidden:bool, **kwargs):
        """
        Params:
            1. hidden: bool
                Whether scrollbars should be always hidden.
        """
        return self.drv.call(None,'Emulation.setScrollbarsHidden',hidden=hidden, **kwargs)


    # func: setDocumentCookieDisabled
    def setDocumentCookieDisabled(self,disabled:bool, **kwargs):
        """
        Params:
            1. disabled: bool
                Whether document.coookie API should be disabled.
        """
        return self.drv.call(None,'Emulation.setDocumentCookieDisabled',disabled=disabled, **kwargs)


    # func: setEmitTouchEventsForMouse
    def setEmitTouchEventsForMouse(self,enabled:bool, configuration:str=None, **kwargs):
        """
        Params:
            1. enabled: bool
                Whether touch emulation based on mouse input should be enabled.
            configurationEnums = ['mobile', 'desktop']
            2. configuration: str (OPTIONAL)
                Touch/gesture events configuration. Default: current platform.
        """
        return self.drv.call(None,'Emulation.setEmitTouchEventsForMouse',enabled=enabled, configuration=configuration, **kwargs)


    # func: setEmulatedMedia
    def setEmulatedMedia(self,media:str=None, features:List[MediaFeature]=None, **kwargs):
        """
            Emulates the given media type or media feature for CSS media queries.
        Params:
            1. media: str (OPTIONAL)
                Media type to emulate. Empty string disables the override.
            2. features: List[MediaFeature] (OPTIONAL)
                Media features to emulate.
        """
        return self.drv.call(None,'Emulation.setEmulatedMedia',media=media, features=features, **kwargs)


    # func: setEmulatedVisionDeficiency
    def setEmulatedVisionDeficiency(self,type:str, **kwargs):
        """
            Emulates the given vision deficiency.
        Params:
            typeEnums = ['none', 'achromatopsia', 'blurredVision', 'deuteranopia', 'protanopia', 'tritanopia']
            1. type: str
                Vision deficiency to emulate.
        """
        return self.drv.call(None,'Emulation.setEmulatedVisionDeficiency',type=type, **kwargs)


    # func: setGeolocationOverride
    def setGeolocationOverride(self,latitude:int=None, longitude:int=None, accuracy:int=None, **kwargs):
        """
            Overrides the Geolocation Position or Error. Omitting any of the parameters emulates position
            unavailable.
        Params:
            1. latitude: int (OPTIONAL)
                Mock latitude
            2. longitude: int (OPTIONAL)
                Mock longitude
            3. accuracy: int (OPTIONAL)
                Mock accuracy
        """
        return self.drv.call(None,'Emulation.setGeolocationOverride',latitude=latitude, longitude=longitude, accuracy=accuracy, **kwargs)


    # func: setIdleOverride
    def setIdleOverride(self,isUserActive:bool, isScreenUnlocked:bool, **kwargs):
        """
            Overrides the Idle state.
        Params:
            1. isUserActive: bool
                Mock isUserActive
            2. isScreenUnlocked: bool
                Mock isScreenUnlocked
        """
        return self.drv.call(None,'Emulation.setIdleOverride',isUserActive=isUserActive, isScreenUnlocked=isScreenUnlocked, **kwargs)


    # func: clearIdleOverride
    def clearIdleOverride(self,**kwargs):
        """
            Clears Idle state overrides.
        """
        return self.drv.call(None,'Emulation.clearIdleOverride',**kwargs)


    # func: setNavigatorOverrides
    def setNavigatorOverrides(self,platform:str, **kwargs):
        """
            Overrides value returned by the javascript navigator object.
        Params:
            1. platform: str
                The platform navigator.platform should return.
        """
        return self.drv.call(None,'Emulation.setNavigatorOverrides',platform=platform, **kwargs)


    # func: setPageScaleFactor
    def setPageScaleFactor(self,pageScaleFactor:int, **kwargs):
        """
            Sets a specified page scale factor.
        Params:
            1. pageScaleFactor: int
                Page scale factor.
        """
        return self.drv.call(None,'Emulation.setPageScaleFactor',pageScaleFactor=pageScaleFactor, **kwargs)


    # func: setScriptExecutionDisabled
    def setScriptExecutionDisabled(self,value:bool, **kwargs):
        """
            Switches script execution in the page.
        Params:
            1. value: bool
                Whether script execution should be disabled in the page.
        """
        return self.drv.call(None,'Emulation.setScriptExecutionDisabled',value=value, **kwargs)


    # func: setTouchEmulationEnabled
    def setTouchEmulationEnabled(self,enabled:bool, maxTouchPoints:int=None, **kwargs):
        """
            Enables touch on platforms which do not support them.
        Params:
            1. enabled: bool
                Whether the touch event emulation should be enabled.
            2. maxTouchPoints: int (OPTIONAL)
                Maximum touch points supported. Defaults to one.
        """
        return self.drv.call(None,'Emulation.setTouchEmulationEnabled',enabled=enabled, maxTouchPoints=maxTouchPoints, **kwargs)


    # return: setVirtualTimePolicyReturn
    class setVirtualTimePolicyReturn(ReturnT):
        def __init__(self):
            # Absolute timestamp at which virtual time was first enabled (up time in milliseconds).
            self.virtualTimeTicksBase: int = int


    # func: setVirtualTimePolicy
    def setVirtualTimePolicy(self,policy:VirtualTimePolicy, budget:int=None, maxVirtualTimeTaskStarvationCount:int=None, waitForNavigation:bool=None, initialVirtualTime:Network.TimeSinceEpoch=None, **kwargs) -> setVirtualTimePolicyReturn:
        """
            Turns on virtual time for all frames (replacing real-time with a synthetic time source) and sets
            the current virtual time policy.  Note this supersedes any previous time budget.
        Params:
            1. policy: VirtualTimePolicy
            2. budget: int (OPTIONAL)
                If set, after this many virtual milliseconds have elapsed virtual time will be paused and avirtualTimeBudgetExpired event is sent.
            3. maxVirtualTimeTaskStarvationCount: int (OPTIONAL)
                If set this specifies the maximum number of tasks that can be run before virtual is forcedforwards to prevent deadlock.
            4. waitForNavigation: bool (OPTIONAL)
                If set the virtual time policy change should be deferred until any frame starts navigating.Note any previous deferred policy change is superseded.
            5. initialVirtualTime: Network.TimeSinceEpoch (OPTIONAL)
                If set, base::Time::Now will be overriden to initially return this value.
        Return: setVirtualTimePolicyReturn
        """
        return self.drv.call(Emulation.setVirtualTimePolicyReturn,'Emulation.setVirtualTimePolicy',policy=policy, budget=budget, maxVirtualTimeTaskStarvationCount=maxVirtualTimeTaskStarvationCount, waitForNavigation=waitForNavigation, initialVirtualTime=initialVirtualTime, **kwargs)


    # func: setLocaleOverride
    def setLocaleOverride(self,locale:str=None, **kwargs):
        """
            Overrides default host system locale with the specified one.
        Params:
            1. locale: str (OPTIONAL)
                ICU style C locale (e.g. "en_US"). If not specified or empty, disables the override andrestores default host system locale.
        """
        return self.drv.call(None,'Emulation.setLocaleOverride',locale=locale, **kwargs)


    # func: setTimezoneOverride
    def setTimezoneOverride(self,timezoneId:str, **kwargs):
        """
            Overrides default host system timezone with the specified one.
        Params:
            1. timezoneId: str
                The timezone identifier. If empty, disables the override andrestores default host system timezone.
        """
        return self.drv.call(None,'Emulation.setTimezoneOverride',timezoneId=timezoneId, **kwargs)


    # func: setVisibleSize
    def setVisibleSize(self,width:int, height:int, **kwargs):
        """
            Resizes the frame/viewport of the page. Note that this does not affect the frame's container
            (e.g. browser window). Can be used to produce screenshots of the specified size. Not supported
            on Android.
        Params:
            1. width: int
                Frame width (DIP).
            2. height: int
                Frame height (DIP).
        """
        return self.drv.call(None,'Emulation.setVisibleSize',width=width, height=height, **kwargs)


    # func: setUserAgentOverride
    def setUserAgentOverride(self,userAgent:str, acceptLanguage:str=None, platform:str=None, userAgentMetadata:UserAgentMetadata=None, **kwargs):
        """
            Allows overriding user agent with the given string.
        Params:
            1. userAgent: str
                User agent to use.
            2. acceptLanguage: str (OPTIONAL)
                Browser langugage to emulate.
            3. platform: str (OPTIONAL)
                The platform navigator.platform should return.
            4. userAgentMetadata: UserAgentMetadata (OPTIONAL)
                To be sent in Sec-CH-UA-* headers and returned in navigator.userAgentData
        """
        return self.drv.call(None,'Emulation.setUserAgentOverride',userAgent=userAgent, acceptLanguage=acceptLanguage, platform=platform, userAgentMetadata=userAgentMetadata, **kwargs)



