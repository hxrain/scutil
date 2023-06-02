"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# --------------------------------------------------------------------------------
# Page Domain Typing.
# --------------------------------------------------------------------------------
# typing: Unique frame identifier.
FrameId = str


# typing: Indicates whether a frame has been identified as an ad.
AdFrameType = str
AdFrameTypeEnums = ['none', 'child', 'root']


# typing: Indicates whether the frame is a secure context and why it is the case.
SecureContextType = str
SecureContextTypeEnums = ['Secure', 'SecureLocalhost', 'InsecureScheme', 'InsecureAncestor']


# typing: Indicates whether the frame is cross-origin isolated and why it is the case.
CrossOriginIsolatedContextType = str
CrossOriginIsolatedContextTypeEnums = ['Isolated', 'NotIsolated', 'NotIsolatedFeatureDisabled']


# object: Frame
class Frame(TypingT):
    """
        Information about the Frame on the page.
    """
    def __init__(self):
        # Frame unique identifier.
        self.id: FrameId = FrameId
        # OPTIONAL, Parent frame identifier.
        self.parentId: str = str
        # Identifier of the loader associated with this frame.
        self.loaderId: Network.LoaderId = Network.LoaderId
        # OPTIONAL, Frame's name as specified in the tag.
        self.name: str = str
        # Frame document's URL without fragment.
        self.url: str = str
        # OPTIONAL, Frame document's URL fragment including the '#'.
        self.urlFragment: str = str
        # Frame document's registered domain, taking the public suffixes list into account.Extracted from the Frame's url.Example URLs: http://www.google.com/file.html -> "google.com"              http://a.b.co.uk/file.html      -> "b.co.uk"
        self.domainAndRegistry: str = str
        # Frame document's security origin.
        self.securityOrigin: str = str
        # Frame document's mimeType as determined by the browser.
        self.mimeType: str = str
        # OPTIONAL, If the frame failed to load, this contains the URL that could not be loaded. Note that unlike url above, this URL may contain a fragment.
        self.unreachableUrl: str = str
        # OPTIONAL, Indicates whether this frame was tagged as an ad.
        self.adFrameType: AdFrameType = AdFrameType
        # Indicates whether the main document is a secure context and explains why that is the case.
        self.secureContextType: SecureContextType = SecureContextType
        # Indicates whether this is a cross origin isolated context.
        self.crossOriginIsolatedContextType: CrossOriginIsolatedContextType = CrossOriginIsolatedContextType


# object: FrameResource
class FrameResource(TypingT):
    """
        Information about the Resource on the page.
    """
    def __init__(self):
        # Resource URL.
        self.url: str = str
        # Type of this resource.
        self.type: Network.ResourceType = Network.ResourceType
        # Resource mimeType as determined by the browser.
        self.mimeType: str = str
        # OPTIONAL, last-modified timestamp as reported by server.
        self.lastModified: Network.TimeSinceEpoch = Network.TimeSinceEpoch
        # OPTIONAL, Resource content size.
        self.contentSize: int = int
        # OPTIONAL, True if the resource failed to load.
        self.failed: bool = bool
        # OPTIONAL, True if the resource was canceled during loading.
        self.canceled: bool = bool


# object: FrameResourceTree
class FrameResourceTree(TypingT):
    """
        Information about the Frame hierarchy along with their cached resources.
    """
    def __init__(self):
        # Frame information for this tree item.
        self.frame: Frame = Frame
        # OPTIONAL, Child frames.
        self.childFrames: List[FrameResourceTree] = [FrameResourceTree]
        # Information about frame resources.
        self.resources: List[FrameResource] = [FrameResource]


# object: FrameTree
class FrameTree(TypingT):
    """
        Information about the Frame hierarchy.
    """
    def __init__(self):
        # Frame information for this tree item.
        self.frame: Frame = Frame
        # OPTIONAL, Child frames.
        self.childFrames: List[FrameTree] = [FrameTree]


# typing: Unique script identifier.
ScriptIdentifier = str


# typing: Transition type.
TransitionType = str
TransitionTypeEnums = ['link', 'typed', 'address_bar', 'auto_bookmark', 'auto_subframe', 'manual_subframe', 'generated', 'auto_toplevel', 'form_submit', 'reload', 'keyword', 'keyword_generated', 'other']


# object: NavigationEntry
class NavigationEntry(TypingT):
    """
        Navigation history entry.
    """
    def __init__(self):
        # Unique id of the navigation history entry.
        self.id: int = int
        # URL of the navigation history entry.
        self.url: str = str
        # URL that the user typed in the url bar.
        self.userTypedURL: str = str
        # Title of the navigation history entry.
        self.title: str = str
        # Transition type.
        self.transitionType: TransitionType = TransitionType


# object: ScreencastFrameMetadata
class ScreencastFrameMetadata(TypingT):
    """
        Screencast frame metadata.
    """
    def __init__(self):
        # Top offset in DIP.
        self.offsetTop: int = int
        # Page scale factor.
        self.pageScaleFactor: int = int
        # Device screen width in DIP.
        self.deviceWidth: int = int
        # Device screen height in DIP.
        self.deviceHeight: int = int
        # Position of horizontal scroll in CSS pixels.
        self.scrollOffsetX: int = int
        # Position of vertical scroll in CSS pixels.
        self.scrollOffsetY: int = int
        # OPTIONAL, Frame swap timestamp.
        self.timestamp: Network.TimeSinceEpoch = Network.TimeSinceEpoch


# typing: Javascript dialog type.
DialogType = str
DialogTypeEnums = ['alert', 'confirm', 'prompt', 'beforeunload']


# object: AppManifestError
class AppManifestError(TypingT):
    """
        Error while paring app manifest.
    """
    def __init__(self):
        # Error message.
        self.message: str = str
        # If criticial, this is a non-recoverable parse error.
        self.critical: int = int
        # Error line.
        self.line: int = int
        # Error column.
        self.column: int = int


# object: AppManifestParsedProperties
class AppManifestParsedProperties(TypingT):
    """
        Parsed app manifest properties.
    """
    def __init__(self):
        # Computed scope value
        self.scope: str = str


# object: LayoutViewport
class LayoutViewport(TypingT):
    """
        Layout viewport position and dimensions.
    """
    def __init__(self):
        # Horizontal offset relative to the document (CSS pixels).
        self.pageX: int = int
        # Vertical offset relative to the document (CSS pixels).
        self.pageY: int = int
        # Width (CSS pixels), excludes scrollbar if present.
        self.clientWidth: int = int
        # Height (CSS pixels), excludes scrollbar if present.
        self.clientHeight: int = int


# object: VisualViewport
class VisualViewport(TypingT):
    """
        Visual viewport position, dimensions, and scale.
    """
    def __init__(self):
        # Horizontal offset relative to the layout viewport (CSS pixels).
        self.offsetX: int = int
        # Vertical offset relative to the layout viewport (CSS pixels).
        self.offsetY: int = int
        # Horizontal offset relative to the document (CSS pixels).
        self.pageX: int = int
        # Vertical offset relative to the document (CSS pixels).
        self.pageY: int = int
        # Width (CSS pixels), excludes scrollbar if present.
        self.clientWidth: int = int
        # Height (CSS pixels), excludes scrollbar if present.
        self.clientHeight: int = int
        # Scale relative to the ideal viewport (size at width=device-width).
        self.scale: int = int
        # OPTIONAL, Page zoom factor (CSS to device independent pixels ratio).
        self.zoom: int = int


# object: Viewport
class Viewport(TypingT):
    """
        Viewport for capturing screenshot.
    """
    def __init__(self):
        # X offset in device independent pixels (dip).
        self.x: int = int
        # Y offset in device independent pixels (dip).
        self.y: int = int
        # Rectangle width in device independent pixels (dip).
        self.width: int = int
        # Rectangle height in device independent pixels (dip).
        self.height: int = int
        # Page scale factor.
        self.scale: int = int


# object: FontFamilies
class FontFamilies(TypingT):
    """
        Generic font families collection.
    """
    def __init__(self):
        # OPTIONAL, The standard font-family.
        self.standard: str = str
        # OPTIONAL, The fixed font-family.
        self.fixed: str = str
        # OPTIONAL, The serif font-family.
        self.serif: str = str
        # OPTIONAL, The sansSerif font-family.
        self.sansSerif: str = str
        # OPTIONAL, The cursive font-family.
        self.cursive: str = str
        # OPTIONAL, The fantasy font-family.
        self.fantasy: str = str
        # OPTIONAL, The pictograph font-family.
        self.pictograph: str = str


# object: FontSizes
class FontSizes(TypingT):
    """
        Default font sizes.
    """
    def __init__(self):
        # OPTIONAL, Default standard font size.
        self.standard: int = int
        # OPTIONAL, Default fixed font size.
        self.fixed: int = int


# typing: ClientNavigationReason
ClientNavigationReason = str
ClientNavigationReasonEnums = ['formSubmissionGet', 'formSubmissionPost', 'httpHeaderRefresh', 'scriptInitiated', 'metaTagRefresh', 'pageBlockInterstitial', 'reload', 'anchorClick']


# typing: ClientNavigationDisposition
ClientNavigationDisposition = str
ClientNavigationDispositionEnums = ['currentTab', 'newTab', 'newWindow', 'download']


# object: InstallabilityErrorArgument
class InstallabilityErrorArgument(TypingT):
    """
        InstallabilityErrorArgument
    """
    def __init__(self):
        # Argument name (e.g. name:'minimum-icon-size-in-pixels').
        self.name: str = str
        # Argument value (e.g. value:'64').
        self.value: str = str


# object: InstallabilityError
class InstallabilityError(TypingT):
    """
        The installability error
    """
    def __init__(self):
        # The error id (e.g. 'manifest-missing-suitable-icon').
        self.errorId: str = str
        # The list of error arguments (e.g. {name:'minimum-icon-size-in-pixels', value:'64'}).
        self.errorArguments: List[InstallabilityErrorArgument] = [InstallabilityErrorArgument]


# typing: The referring-policy used for the navigation.
ReferrerPolicy = str
ReferrerPolicyEnums = ['noReferrer', 'noReferrerWhenDowngrade', 'origin', 'originWhenCrossOrigin', 'sameOrigin', 'strictOrigin', 'strictOriginWhenCrossOrigin', 'unsafeUrl']


# --------------------------------------------------------------------------------
# Page Domain Event.
# --------------------------------------------------------------------------------
# event: domContentEventFired
class domContentEventFired(EventT):
    """
        domContentEventFired
    """
    event="Page.domContentEventFired"
    def __init__(self):
        # timestamp
        self.timestamp: Network.MonotonicTime = Network.MonotonicTime


# event: fileChooserOpened
class fileChooserOpened(EventT):
    """
        Emitted only when `page.interceptFileChooser` is enabled.
    """
    event="Page.fileChooserOpened"
    def __init__(self):
        # Id of the frame containing input node.
        self.frameId: FrameId = FrameId
        # Input node id.
        self.backendNodeId: DOM.BackendNodeId = DOM.BackendNodeId
        modeEnums = ['selectSingle', 'selectMultiple']
        # Input mode.
        self.mode: str = str


# event: frameAttached
class frameAttached(EventT):
    """
        Fired when frame has been attached to its parent.
    """
    event="Page.frameAttached"
    def __init__(self):
        # Id of the frame that has been attached.
        self.frameId: FrameId = FrameId
        # Parent frame identifier.
        self.parentFrameId: FrameId = FrameId
        # OPTIONAL, JavaScript stack trace of when frame was attached, only set if frame initiated from script.
        self.stack: Runtime.StackTrace = Runtime.StackTrace


# event: frameClearedScheduledNavigation
class frameClearedScheduledNavigation(EventT):
    """
        Fired when frame no longer has a scheduled navigation.
    """
    event="Page.frameClearedScheduledNavigation"
    def __init__(self):
        # Id of the frame that has cleared its scheduled navigation.
        self.frameId: FrameId = FrameId


# event: frameDetached
class frameDetached(EventT):
    """
        Fired when frame has been detached from its parent.
    """
    event="Page.frameDetached"
    def __init__(self):
        # Id of the frame that has been detached.
        self.frameId: FrameId = FrameId


# event: frameNavigated
class frameNavigated(EventT):
    """
        Fired once navigation of the frame has completed. Frame is now associated with the new loader.
    """
    event="Page.frameNavigated"
    def __init__(self):
        # Frame object.
        self.frame: Frame = Frame


# event: frameResized
class frameResized(EventT):
    """
        frameResized
    """
    event="Page.frameResized"
    def __init__(self):
        pass


# event: frameRequestedNavigation
class frameRequestedNavigation(EventT):
    """
        Fired when a renderer-initiated navigation is requested.
        Navigation may still be cancelled after the event is issued.
    """
    event="Page.frameRequestedNavigation"
    def __init__(self):
        # Id of the frame that is being navigated.
        self.frameId: FrameId = FrameId
        # The reason for the navigation.
        self.reason: ClientNavigationReason = ClientNavigationReason
        # The destination URL for the requested navigation.
        self.url: str = str
        # The disposition for the navigation.
        self.disposition: ClientNavigationDisposition = ClientNavigationDisposition


# event: frameScheduledNavigation
class frameScheduledNavigation(EventT):
    """
        Fired when frame schedules a potential navigation.
    """
    event="Page.frameScheduledNavigation"
    def __init__(self):
        # Id of the frame that has scheduled a navigation.
        self.frameId: FrameId = FrameId
        # Delay (in seconds) until the navigation is scheduled to begin. The navigation is notguaranteed to start.
        self.delay: int = int
        # The reason for the navigation.
        self.reason: ClientNavigationReason = ClientNavigationReason
        # The destination URL for the scheduled navigation.
        self.url: str = str


# event: frameStartedLoading
class frameStartedLoading(EventT):
    """
        Fired when frame has started loading.
    """
    event="Page.frameStartedLoading"
    def __init__(self):
        # Id of the frame that has started loading.
        self.frameId: FrameId = FrameId


# event: frameStoppedLoading
class frameStoppedLoading(EventT):
    """
        Fired when frame has stopped loading.
    """
    event="Page.frameStoppedLoading"
    def __init__(self):
        # Id of the frame that has stopped loading.
        self.frameId: FrameId = FrameId


# event: downloadWillBegin
class downloadWillBegin(EventT):
    """
        Fired when page is about to start a download.
    """
    event="Page.downloadWillBegin"
    def __init__(self):
        # Id of the frame that caused download to begin.
        self.frameId: FrameId = FrameId
        # Global unique identifier of the download.
        self.guid: str = str
        # URL of the resource being downloaded.
        self.url: str = str
        # Suggested file name of the resource (the actual name of the file saved on disk may differ).
        self.suggestedFilename: str = str


# event: downloadProgress
class downloadProgress(EventT):
    """
        Fired when download makes progress. Last call has |done| == true.
    """
    event="Page.downloadProgress"
    def __init__(self):
        # Global unique identifier of the download.
        self.guid: str = str
        # Total expected bytes to download.
        self.totalBytes: int = int
        # Total bytes received.
        self.receivedBytes: int = int
        stateEnums = ['inProgress', 'completed', 'canceled']
        # Download status.
        self.state: str = str


# event: interstitialHidden
class interstitialHidden(EventT):
    """
        Fired when interstitial page was hidden
    """
    event="Page.interstitialHidden"
    def __init__(self):
        pass


# event: interstitialShown
class interstitialShown(EventT):
    """
        Fired when interstitial page was shown
    """
    event="Page.interstitialShown"
    def __init__(self):
        pass


# event: javascriptDialogClosed
class javascriptDialogClosed(EventT):
    """
        Fired when a JavaScript initiated dialog (alert, confirm, prompt, or onbeforeunload) has been
        closed.
    """
    event="Page.javascriptDialogClosed"
    def __init__(self):
        # Whether dialog was confirmed.
        self.result: bool = bool
        # User input in case of prompt.
        self.userInput: str = str


# event: javascriptDialogOpening
class javascriptDialogOpening(EventT):
    """
        Fired when a JavaScript initiated dialog (alert, confirm, prompt, or onbeforeunload) is about to
        open.
    """
    event="Page.javascriptDialogOpening"
    def __init__(self):
        # Frame url.
        self.url: str = str
        # Message that will be displayed by the dialog.
        self.message: str = str
        # Dialog type.
        self.type: DialogType = DialogType
        # True iff browser is capable showing or acting on the given dialog. When browser has nodialog handler for given target, calling alert while Page domain is engaged will stallthe page execution. Execution can be resumed via calling Page.handleJavaScriptDialog.
        self.hasBrowserHandler: bool = bool
        # OPTIONAL, Default dialog prompt.
        self.defaultPrompt: str = str


# event: lifecycleEvent
class lifecycleEvent(EventT):
    """
        Fired for top level page lifecycle events such as navigation, load, paint, etc.
    """
    event="Page.lifecycleEvent"
    def __init__(self):
        # Id of the frame.
        self.frameId: FrameId = FrameId
        # Loader identifier. Empty string if the request is fetched from worker.
        self.loaderId: Network.LoaderId = Network.LoaderId
        # name
        self.name: str = str
        # timestamp
        self.timestamp: Network.MonotonicTime = Network.MonotonicTime


# event: loadEventFired
class loadEventFired(EventT):
    """
        loadEventFired
    """
    event="Page.loadEventFired"
    def __init__(self):
        # timestamp
        self.timestamp: Network.MonotonicTime = Network.MonotonicTime


# event: navigatedWithinDocument
class navigatedWithinDocument(EventT):
    """
        Fired when same-document navigation happens, e.g. due to history API usage or anchor navigation.
    """
    event="Page.navigatedWithinDocument"
    def __init__(self):
        # Id of the frame.
        self.frameId: FrameId = FrameId
        # Frame's new url.
        self.url: str = str


# event: screencastFrame
class screencastFrame(EventT):
    """
        Compressed image data requested by the `startScreencast`.
    """
    event="Page.screencastFrame"
    def __init__(self):
        # Base64-encoded compressed image.
        self.data: str = str
        # Screencast frame metadata.
        self.metadata: ScreencastFrameMetadata = ScreencastFrameMetadata
        # Frame number.
        self.sessionId: int = int


# event: screencastVisibilityChanged
class screencastVisibilityChanged(EventT):
    """
        Fired when the page with currently enabled screencast was shown or hidden `.
    """
    event="Page.screencastVisibilityChanged"
    def __init__(self):
        # True if the page is visible.
        self.visible: bool = bool


# event: windowOpen
class windowOpen(EventT):
    """
        Fired when a new window is going to be opened, via window.open(), link click, form submission,
        etc.
    """
    event="Page.windowOpen"
    def __init__(self):
        # The URL for the new window.
        self.url: str = str
        # Window name.
        self.windowName: str = str
        # An array of enabled window features.
        self.windowFeatures: List[str] = [str]
        # Whether or not it was triggered by user gesture.
        self.userGesture: bool = bool


# event: compilationCacheProduced
class compilationCacheProduced(EventT):
    """
        Issued for every compilation cache generated. Is only available
        if Page.setGenerateCompilationCache is enabled.
    """
    event="Page.compilationCacheProduced"
    def __init__(self):
        # url
        self.url: str = str
        # Base64-encoded data
        self.data: str = str


from cdp import Debugger
from cdp import DOM
from cdp import IO
from cdp import Network
from cdp import Runtime
from cdp import Emulation
# ================================================================================
# Page Domain Class.
# ================================================================================
class Page(DomainT):
    """
        Actions and events related to the inspected page belong to the page domain.
    """
    def __init__(self, drv):
        self.drv = drv


    # return: addScriptToEvaluateOnLoadReturn
    class addScriptToEvaluateOnLoadReturn(ReturnT):
        def __init__(self):
            # Identifier of the added script.
            self.identifier: ScriptIdentifier = ScriptIdentifier


    # func: addScriptToEvaluateOnLoad
    def addScriptToEvaluateOnLoad(self,scriptSource:str, **kwargs) -> addScriptToEvaluateOnLoadReturn:
        """
            Deprecated, please use addScriptToEvaluateOnNewDocument instead.
        Params:
            1. scriptSource: str
        Return: addScriptToEvaluateOnLoadReturn
        """
        return self.drv.call(Page.addScriptToEvaluateOnLoadReturn,'Page.addScriptToEvaluateOnLoad',scriptSource=scriptSource, **kwargs)


    # return: addScriptToEvaluateOnNewDocumentReturn
    class addScriptToEvaluateOnNewDocumentReturn(ReturnT):
        def __init__(self):
            # Identifier of the added script.
            self.identifier: ScriptIdentifier = ScriptIdentifier


    # func: addScriptToEvaluateOnNewDocument
    def addScriptToEvaluateOnNewDocument(self,source:str, worldName:str=None, **kwargs) -> addScriptToEvaluateOnNewDocumentReturn:
        """
            Evaluates given script in every frame upon creation (before loading frame's scripts).
        Params:
            1. source: str
            2. worldName: str (OPTIONAL)
                If specified, creates an isolated world with the given name and evaluates given script in it.This world name will be used as the ExecutionContextDescription::name when the correspondingevent is emitted.
        Return: addScriptToEvaluateOnNewDocumentReturn
        """
        return self.drv.call(Page.addScriptToEvaluateOnNewDocumentReturn,'Page.addScriptToEvaluateOnNewDocument',source=source, worldName=worldName, **kwargs)


    # func: bringToFront
    def bringToFront(self,**kwargs):
        """
            Brings page to front (activates tab).
        """
        return self.drv.call(None,'Page.bringToFront',**kwargs)


    # return: captureScreenshotReturn
    class captureScreenshotReturn(ReturnT):
        def __init__(self):
            # Base64-encoded image data.
            self.data: str = str


    # func: captureScreenshot
    def captureScreenshot(self,format:str=None, quality:int=None, clip:Viewport=None, fromSurface:bool=None, **kwargs) -> captureScreenshotReturn:
        """
            Capture page screenshot.
        Params:
            formatEnums = ['jpeg', 'png']
            1. format: str (OPTIONAL)
                Image compression format (defaults to png).
            2. quality: int (OPTIONAL)
                Compression quality from range [0..100] (jpeg only).
            3. clip: Viewport (OPTIONAL)
                Capture the screenshot of a given region only.
            4. fromSurface: bool (OPTIONAL)
                Capture the screenshot from the surface, rather than the view. Defaults to true.
        Return: captureScreenshotReturn
        """
        return self.drv.call(Page.captureScreenshotReturn,'Page.captureScreenshot',format=format, quality=quality, clip=clip, fromSurface=fromSurface, **kwargs)


    # return: captureSnapshotReturn
    class captureSnapshotReturn(ReturnT):
        def __init__(self):
            # Serialized page data.
            self.data: str = str


    # func: captureSnapshot
    def captureSnapshot(self,format:str=None, **kwargs) -> captureSnapshotReturn:
        """
            Returns a snapshot of the page as a string. For MHTML format, the serialization includes
            iframes, shadow DOM, external resources, and element-inline styles.
        Params:
            formatEnums = ['mhtml']
            1. format: str (OPTIONAL)
                Format (defaults to mhtml).
        Return: captureSnapshotReturn
        """
        return self.drv.call(Page.captureSnapshotReturn,'Page.captureSnapshot',format=format, **kwargs)


    # func: clearDeviceMetricsOverride
    def clearDeviceMetricsOverride(self,**kwargs):
        """
            Clears the overriden device metrics.
        """
        return self.drv.call(None,'Page.clearDeviceMetricsOverride',**kwargs)


    # func: clearDeviceOrientationOverride
    def clearDeviceOrientationOverride(self,**kwargs):
        """
            Clears the overridden Device Orientation.
        """
        return self.drv.call(None,'Page.clearDeviceOrientationOverride',**kwargs)


    # func: clearGeolocationOverride
    def clearGeolocationOverride(self,**kwargs):
        """
            Clears the overriden Geolocation Position and Error.
        """
        return self.drv.call(None,'Page.clearGeolocationOverride',**kwargs)


    # return: createIsolatedWorldReturn
    class createIsolatedWorldReturn(ReturnT):
        def __init__(self):
            # Execution context of the isolated world.
            self.executionContextId: Runtime.ExecutionContextId = Runtime.ExecutionContextId


    # func: createIsolatedWorld
    def createIsolatedWorld(self,frameId:FrameId, worldName:str=None, grantUniveralAccess:bool=None, **kwargs) -> createIsolatedWorldReturn:
        """
            Creates an isolated world for the given frame.
        Params:
            1. frameId: FrameId
                Id of the frame in which the isolated world should be created.
            2. worldName: str (OPTIONAL)
                An optional name which is reported in the Execution Context.
            3. grantUniveralAccess: bool (OPTIONAL)
                Whether or not universal access should be granted to the isolated world. This is a powerfuloption, use with caution.
        Return: createIsolatedWorldReturn
        """
        return self.drv.call(Page.createIsolatedWorldReturn,'Page.createIsolatedWorld',frameId=frameId, worldName=worldName, grantUniveralAccess=grantUniveralAccess, **kwargs)


    # func: deleteCookie
    def deleteCookie(self,cookieName:str, url:str, **kwargs):
        """
            Deletes browser cookie with given name, domain and path.
        Params:
            1. cookieName: str
                Name of the cookie to remove.
            2. url: str
                URL to match cooke domain and path.
        """
        return self.drv.call(None,'Page.deleteCookie',cookieName=cookieName, url=url, **kwargs)


    # func: disable
    def disable(self,**kwargs):
        """
            Disables page domain notifications.
        """
        return self.drv.call(None,'Page.disable',**kwargs)


    # func: enable
    def enable(self,**kwargs):
        """
            Enables page domain notifications.
        """
        return self.drv.call(None,'Page.enable',**kwargs)


    # return: getAppManifestReturn
    class getAppManifestReturn(ReturnT):
        def __init__(self):
            # Manifest location.
            self.url: str = str
            # errors
            self.errors: List[AppManifestError] = [AppManifestError]
            # OPTIONAL, Manifest content.
            self.data: str = str
            # OPTIONAL, Parsed manifest properties
            self.parsed: AppManifestParsedProperties = AppManifestParsedProperties


    # func: getAppManifest
    def getAppManifest(self,**kwargs) -> getAppManifestReturn:
        """
        Return: getAppManifestReturn
        """
        return self.drv.call(Page.getAppManifestReturn,'Page.getAppManifest',**kwargs)


    # return: getInstallabilityErrorsReturn
    class getInstallabilityErrorsReturn(ReturnT):
        def __init__(self):
            # installabilityErrors
            self.installabilityErrors: List[InstallabilityError] = [InstallabilityError]


    # func: getInstallabilityErrors
    def getInstallabilityErrors(self,**kwargs) -> getInstallabilityErrorsReturn:
        """
        Return: getInstallabilityErrorsReturn
        """
        return self.drv.call(Page.getInstallabilityErrorsReturn,'Page.getInstallabilityErrors',**kwargs)


    # return: getManifestIconsReturn
    class getManifestIconsReturn(ReturnT):
        def __init__(self):
            # OPTIONAL, primaryIcon
            self.primaryIcon: str = str


    # func: getManifestIcons
    def getManifestIcons(self,**kwargs) -> getManifestIconsReturn:
        """
        Return: getManifestIconsReturn
        """
        return self.drv.call(Page.getManifestIconsReturn,'Page.getManifestIcons',**kwargs)


    # return: getCookiesReturn
    class getCookiesReturn(ReturnT):
        def __init__(self):
            # Array of cookie objects.
            self.cookies: List[Network.Cookie] = [Network.Cookie]


    # func: getCookies
    def getCookies(self,**kwargs) -> getCookiesReturn:
        """
            Returns all browser cookies. Depending on the backend support, will return detailed cookie
            information in the `cookies` field.
        Return: getCookiesReturn
        """
        return self.drv.call(Page.getCookiesReturn,'Page.getCookies',**kwargs)


    # return: getFrameTreeReturn
    class getFrameTreeReturn(ReturnT):
        def __init__(self):
            # Present frame tree structure.
            self.frameTree: FrameTree = FrameTree


    # func: getFrameTree
    def getFrameTree(self,**kwargs) -> getFrameTreeReturn:
        """
            Returns present frame tree structure.
        Return: getFrameTreeReturn
        """
        return self.drv.call(Page.getFrameTreeReturn,'Page.getFrameTree',**kwargs)


    # return: getLayoutMetricsReturn
    class getLayoutMetricsReturn(ReturnT):
        def __init__(self):
            # Metrics relating to the layout viewport.
            self.layoutViewport: LayoutViewport = LayoutViewport
            # Metrics relating to the visual viewport.
            self.visualViewport: VisualViewport = VisualViewport
            # Size of scrollable area.
            self.contentSize: DOM.Rect = DOM.Rect


    # func: getLayoutMetrics
    def getLayoutMetrics(self,**kwargs) -> getLayoutMetricsReturn:
        """
            Returns metrics relating to the layouting of the page, such as viewport bounds/scale.
        Return: getLayoutMetricsReturn
        """
        return self.drv.call(Page.getLayoutMetricsReturn,'Page.getLayoutMetrics',**kwargs)


    # return: getNavigationHistoryReturn
    class getNavigationHistoryReturn(ReturnT):
        def __init__(self):
            # Index of the current navigation history entry.
            self.currentIndex: int = int
            # Array of navigation history entries.
            self.entries: List[NavigationEntry] = [NavigationEntry]


    # func: getNavigationHistory
    def getNavigationHistory(self,**kwargs) -> getNavigationHistoryReturn:
        """
            Returns navigation history for the current page.
        Return: getNavigationHistoryReturn
        """
        return self.drv.call(Page.getNavigationHistoryReturn,'Page.getNavigationHistory',**kwargs)


    # func: resetNavigationHistory
    def resetNavigationHistory(self,**kwargs):
        """
            Resets navigation history for the current page.
        """
        return self.drv.call(None,'Page.resetNavigationHistory',**kwargs)


    # return: getResourceContentReturn
    class getResourceContentReturn(ReturnT):
        def __init__(self):
            # Resource content.
            self.content: str = str
            # True, if content was served as base64.
            self.base64Encoded: bool = bool


    # func: getResourceContent
    def getResourceContent(self,frameId:FrameId, url:str, **kwargs) -> getResourceContentReturn:
        """
            Returns content of the given resource.
        Params:
            1. frameId: FrameId
                Frame id to get resource for.
            2. url: str
                URL of the resource to get content for.
        Return: getResourceContentReturn
        """
        return self.drv.call(Page.getResourceContentReturn,'Page.getResourceContent',frameId=frameId, url=url, **kwargs)


    # return: getResourceTreeReturn
    class getResourceTreeReturn(ReturnT):
        def __init__(self):
            # Present frame / resource tree structure.
            self.frameTree: FrameResourceTree = FrameResourceTree


    # func: getResourceTree
    def getResourceTree(self,**kwargs) -> getResourceTreeReturn:
        """
            Returns present frame / resource tree structure.
        Return: getResourceTreeReturn
        """
        return self.drv.call(Page.getResourceTreeReturn,'Page.getResourceTree',**kwargs)


    # func: handleJavaScriptDialog
    def handleJavaScriptDialog(self,accept:bool, promptText:str=None, **kwargs):
        """
            Accepts or dismisses a JavaScript initiated dialog (alert, confirm, prompt, or onbeforeunload).
        Params:
            1. accept: bool
                Whether to accept or dismiss the dialog.
            2. promptText: str (OPTIONAL)
                The text to enter into the dialog prompt before accepting. Used only if this is a promptdialog.
        """
        return self.drv.call(None,'Page.handleJavaScriptDialog',accept=accept, promptText=promptText, **kwargs)


    # return: navigateReturn
    class navigateReturn(ReturnT):
        def __init__(self):
            # Frame id that has navigated (or failed to navigate)
            self.frameId: FrameId = FrameId
            # OPTIONAL, Loader identifier.
            self.loaderId: Network.LoaderId = Network.LoaderId
            # OPTIONAL, User friendly error message, present if and only if navigation has failed.
            self.errorText: str = str


    # func: navigate
    def navigate(self,url:str, referrer:str=None, transitionType:TransitionType=None, frameId:FrameId=None, referrerPolicy:ReferrerPolicy=None, **kwargs) -> navigateReturn:
        """
            Navigates current page to the given URL.
        Params:
            1. url: str
                URL to navigate the page to.
            2. referrer: str (OPTIONAL)
                Referrer URL.
            3. transitionType: TransitionType (OPTIONAL)
                Intended transition type.
            4. frameId: FrameId (OPTIONAL)
                Frame id to navigate, if not specified navigates the top frame.
            5. referrerPolicy: ReferrerPolicy (OPTIONAL)
                Referrer-policy used for the navigation.
        Return: navigateReturn
        """
        return self.drv.call(Page.navigateReturn,'Page.navigate',url=url, referrer=referrer, transitionType=transitionType, frameId=frameId, referrerPolicy=referrerPolicy, **kwargs)


    # func: navigateToHistoryEntry
    def navigateToHistoryEntry(self,entryId:int, **kwargs):
        """
            Navigates current page to the given history entry.
        Params:
            1. entryId: int
                Unique id of the entry to navigate to.
        """
        return self.drv.call(None,'Page.navigateToHistoryEntry',entryId=entryId, **kwargs)


    # return: printToPDFReturn
    class printToPDFReturn(ReturnT):
        def __init__(self):
            # Base64-encoded pdf data. Empty if |returnAsStream| is specified.
            self.data: str = str
            # OPTIONAL, A handle of the stream that holds resulting PDF data.
            self.stream: IO.StreamHandle = IO.StreamHandle


    # func: printToPDF
    def printToPDF(self,landscape:bool=None, displayHeaderFooter:bool=None, printBackground:bool=None, scale:int=None, paperWidth:int=None, paperHeight:int=None, marginTop:int=None, marginBottom:int=None, marginLeft:int=None, marginRight:int=None, pageRanges:str=None, ignoreInvalidPageRanges:bool=None, headerTemplate:str=None, footerTemplate:str=None, preferCSSPageSize:bool=None, transferMode:str=None, **kwargs) -> printToPDFReturn:
        """
            Print page as PDF.
        Params:
            1. landscape: bool (OPTIONAL)
                Paper orientation. Defaults to false.
            2. displayHeaderFooter: bool (OPTIONAL)
                Display header and footer. Defaults to false.
            3. printBackground: bool (OPTIONAL)
                Print background graphics. Defaults to false.
            4. scale: int (OPTIONAL)
                Scale of the webpage rendering. Defaults to 1.
            5. paperWidth: int (OPTIONAL)
                Paper width in inches. Defaults to 8.5 inches.
            6. paperHeight: int (OPTIONAL)
                Paper height in inches. Defaults to 11 inches.
            7. marginTop: int (OPTIONAL)
                Top margin in inches. Defaults to 1cm (~0.4 inches).
            8. marginBottom: int (OPTIONAL)
                Bottom margin in inches. Defaults to 1cm (~0.4 inches).
            9. marginLeft: int (OPTIONAL)
                Left margin in inches. Defaults to 1cm (~0.4 inches).
            10. marginRight: int (OPTIONAL)
                Right margin in inches. Defaults to 1cm (~0.4 inches).
            11. pageRanges: str (OPTIONAL)
                Paper ranges to print, e.g., '1-5, 8, 11-13'. Defaults to the empty string, which meansprint all pages.
            12. ignoreInvalidPageRanges: bool (OPTIONAL)
                Whether to silently ignore invalid but successfully parsed page ranges, such as '3-2'.Defaults to false.
            13. headerTemplate: str (OPTIONAL)
                HTML template for the print header. Should be valid HTML markup with followingclasses used to inject printing values into them:- `date`: formatted print date- `title`: document title- `url`: document location- `pageNumber`: current page number- `totalPages`: total pages in the documentFor example, `<span class=title></span>` would generate span containing the title.
            14. footerTemplate: str (OPTIONAL)
                HTML template for the print footer. Should use the same format as the `headerTemplate`.
            15. preferCSSPageSize: bool (OPTIONAL)
                Whether or not to prefer page size as defined by css. Defaults to false,in which case the content will be scaled to fit the paper size.
            transferModeEnums = ['ReturnAsBase64', 'ReturnAsStream']
            16. transferMode: str (OPTIONAL)
                return as stream
        Return: printToPDFReturn
        """
        return self.drv.call(Page.printToPDFReturn,'Page.printToPDF',landscape=landscape, displayHeaderFooter=displayHeaderFooter, printBackground=printBackground, scale=scale, paperWidth=paperWidth, paperHeight=paperHeight, marginTop=marginTop, marginBottom=marginBottom, marginLeft=marginLeft, marginRight=marginRight, pageRanges=pageRanges, ignoreInvalidPageRanges=ignoreInvalidPageRanges, headerTemplate=headerTemplate, footerTemplate=footerTemplate, preferCSSPageSize=preferCSSPageSize, transferMode=transferMode, **kwargs)


    # func: reload
    def reload(self,ignoreCache:bool=None, scriptToEvaluateOnLoad:str=None, **kwargs):
        """
            Reloads given page optionally ignoring the cache.
        Params:
            1. ignoreCache: bool (OPTIONAL)
                If true, browser cache is ignored (as if the user pressed Shift+refresh).
            2. scriptToEvaluateOnLoad: str (OPTIONAL)
                If set, the script will be injected into all frames of the inspected page after reload.Argument will be ignored if reloading dataURL origin.
        """
        return self.drv.call(None,'Page.reload',ignoreCache=ignoreCache, scriptToEvaluateOnLoad=scriptToEvaluateOnLoad, **kwargs)


    # func: removeScriptToEvaluateOnLoad
    def removeScriptToEvaluateOnLoad(self,identifier:ScriptIdentifier, **kwargs):
        """
            Deprecated, please use removeScriptToEvaluateOnNewDocument instead.
        Params:
            1. identifier: ScriptIdentifier
        """
        return self.drv.call(None,'Page.removeScriptToEvaluateOnLoad',identifier=identifier, **kwargs)


    # func: removeScriptToEvaluateOnNewDocument
    def removeScriptToEvaluateOnNewDocument(self,identifier:ScriptIdentifier, **kwargs):
        """
            Removes given script from the list.
        Params:
            1. identifier: ScriptIdentifier
        """
        return self.drv.call(None,'Page.removeScriptToEvaluateOnNewDocument',identifier=identifier, **kwargs)


    # func: screencastFrameAck
    def screencastFrameAck(self,sessionId:int, **kwargs):
        """
            Acknowledges that a screencast frame has been received by the frontend.
        Params:
            1. sessionId: int
                Frame number.
        """
        return self.drv.call(None,'Page.screencastFrameAck',sessionId=sessionId, **kwargs)


    # return: searchInResourceReturn
    class searchInResourceReturn(ReturnT):
        def __init__(self):
            # List of search matches.
            self.result: List[Debugger.SearchMatch] = [Debugger.SearchMatch]


    # func: searchInResource
    def searchInResource(self,frameId:FrameId, url:str, query:str, caseSensitive:bool=None, isRegex:bool=None, **kwargs) -> searchInResourceReturn:
        """
            Searches for given string in resource content.
        Params:
            1. frameId: FrameId
                Frame id for resource to search in.
            2. url: str
                URL of the resource to search in.
            3. query: str
                String to search for.
            4. caseSensitive: bool (OPTIONAL)
                If true, search is case sensitive.
            5. isRegex: bool (OPTIONAL)
                If true, treats string parameter as regex.
        Return: searchInResourceReturn
        """
        return self.drv.call(Page.searchInResourceReturn,'Page.searchInResource',frameId=frameId, url=url, query=query, caseSensitive=caseSensitive, isRegex=isRegex, **kwargs)


    # func: setAdBlockingEnabled
    def setAdBlockingEnabled(self,enabled:bool, **kwargs):
        """
            Enable Chrome's experimental ad filter on all sites.
        Params:
            1. enabled: bool
                Whether to block ads.
        """
        return self.drv.call(None,'Page.setAdBlockingEnabled',enabled=enabled, **kwargs)


    # func: setBypassCSP
    def setBypassCSP(self,enabled:bool, **kwargs):
        """
            Enable page Content Security Policy by-passing.
        Params:
            1. enabled: bool
                Whether to bypass page CSP.
        """
        return self.drv.call(None,'Page.setBypassCSP',enabled=enabled, **kwargs)


    # func: setDeviceMetricsOverride
    def setDeviceMetricsOverride(self,width:int, height:int, deviceScaleFactor:int, mobile:bool, scale:int=None, screenWidth:int=None, screenHeight:int=None, positionX:int=None, positionY:int=None, dontSetVisibleSize:bool=None, screenOrientation:Emulation.ScreenOrientation=None, viewport:Viewport=None, **kwargs):
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
            11. screenOrientation: Emulation.ScreenOrientation (OPTIONAL)
                Screen orientation override.
            12. viewport: Viewport (OPTIONAL)
                The viewport dimensions and scale. If not set, the override is cleared.
        """
        return self.drv.call(None,'Page.setDeviceMetricsOverride',width=width, height=height, deviceScaleFactor=deviceScaleFactor, mobile=mobile, scale=scale, screenWidth=screenWidth, screenHeight=screenHeight, positionX=positionX, positionY=positionY, dontSetVisibleSize=dontSetVisibleSize, screenOrientation=screenOrientation, viewport=viewport, **kwargs)


    # func: setDeviceOrientationOverride
    def setDeviceOrientationOverride(self,alpha:int, beta:int, gamma:int, **kwargs):
        """
            Overrides the Device Orientation.
        Params:
            1. alpha: int
                Mock alpha
            2. beta: int
                Mock beta
            3. gamma: int
                Mock gamma
        """
        return self.drv.call(None,'Page.setDeviceOrientationOverride',alpha=alpha, beta=beta, gamma=gamma, **kwargs)


    # func: setFontFamilies
    def setFontFamilies(self,fontFamilies:FontFamilies, **kwargs):
        """
            Set generic font families.
        Params:
            1. fontFamilies: FontFamilies
                Specifies font families to set. If a font family is not specified, it won't be changed.
        """
        return self.drv.call(None,'Page.setFontFamilies',fontFamilies=fontFamilies, **kwargs)


    # func: setFontSizes
    def setFontSizes(self,fontSizes:FontSizes, **kwargs):
        """
            Set default font sizes.
        Params:
            1. fontSizes: FontSizes
                Specifies font sizes to set. If a font size is not specified, it won't be changed.
        """
        return self.drv.call(None,'Page.setFontSizes',fontSizes=fontSizes, **kwargs)


    # func: setDocumentContent
    def setDocumentContent(self,frameId:FrameId, html:str, **kwargs):
        """
            Sets given markup as the document's HTML.
        Params:
            1. frameId: FrameId
                Frame id to set HTML for.
            2. html: str
                HTML content to set.
        """
        return self.drv.call(None,'Page.setDocumentContent',frameId=frameId, html=html, **kwargs)


    # func: setDownloadBehavior
    def setDownloadBehavior(self,behavior:str, downloadPath:str=None, **kwargs):
        """
            Set the behavior when downloading a file.
        Params:
            behaviorEnums = ['deny', 'allow', 'default']
            1. behavior: str
                Whether to allow all or deny all download requests, or use default Chrome behavior ifavailable (otherwise deny).
            2. downloadPath: str (OPTIONAL)
                The default path to save downloaded files to. This is requred if behavior is set to 'allow'
        """
        return self.drv.call(None,'Page.setDownloadBehavior',behavior=behavior, downloadPath=downloadPath, **kwargs)


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
        return self.drv.call(None,'Page.setGeolocationOverride',latitude=latitude, longitude=longitude, accuracy=accuracy, **kwargs)


    # func: setLifecycleEventsEnabled
    def setLifecycleEventsEnabled(self,enabled:bool, **kwargs):
        """
            Controls whether page will emit lifecycle events.
        Params:
            1. enabled: bool
                If true, starts emitting lifecycle events.
        """
        return self.drv.call(None,'Page.setLifecycleEventsEnabled',enabled=enabled, **kwargs)


    # func: setTouchEmulationEnabled
    def setTouchEmulationEnabled(self,enabled:bool, configuration:str=None, **kwargs):
        """
            Toggles mouse event-based touch event emulation.
        Params:
            1. enabled: bool
                Whether the touch event emulation should be enabled.
            configurationEnums = ['mobile', 'desktop']
            2. configuration: str (OPTIONAL)
                Touch/gesture events configuration. Default: current platform.
        """
        return self.drv.call(None,'Page.setTouchEmulationEnabled',enabled=enabled, configuration=configuration, **kwargs)


    # func: startScreencast
    def startScreencast(self,format:str=None, quality:int=None, maxWidth:int=None, maxHeight:int=None, everyNthFrame:int=None, **kwargs):
        """
            Starts sending each frame using the `screencastFrame` event.
        Params:
            formatEnums = ['jpeg', 'png']
            1. format: str (OPTIONAL)
                Image compression format.
            2. quality: int (OPTIONAL)
                Compression quality from range [0..100].
            3. maxWidth: int (OPTIONAL)
                Maximum screenshot width.
            4. maxHeight: int (OPTIONAL)
                Maximum screenshot height.
            5. everyNthFrame: int (OPTIONAL)
                Send every n-th frame.
        """
        return self.drv.call(None,'Page.startScreencast',format=format, quality=quality, maxWidth=maxWidth, maxHeight=maxHeight, everyNthFrame=everyNthFrame, **kwargs)


    # func: stopLoading
    def stopLoading(self,**kwargs):
        """
            Force the page stop all navigations and pending resource fetches.
        """
        return self.drv.call(None,'Page.stopLoading',**kwargs)


    # func: crash
    def crash(self,**kwargs):
        """
            Crashes renderer on the IO thread, generates minidumps.
        """
        return self.drv.call(None,'Page.crash',**kwargs)


    # func: close
    def close(self,**kwargs):
        """
            Tries to close page, running its beforeunload hooks, if any.
        """
        return self.drv.call(None,'Page.close',**kwargs)


    # func: setWebLifecycleState
    def setWebLifecycleState(self,state:str, **kwargs):
        """
            Tries to update the web lifecycle state of the page.
            It will transition the page to the given state according to:
            https://github.com/WICG/web-lifecycle/
        Params:
            stateEnums = ['frozen', 'active']
            1. state: str
                Target lifecycle state
        """
        return self.drv.call(None,'Page.setWebLifecycleState',state=state, **kwargs)


    # func: stopScreencast
    def stopScreencast(self,**kwargs):
        """
            Stops sending each frame in the `screencastFrame`.
        """
        return self.drv.call(None,'Page.stopScreencast',**kwargs)


    # func: setProduceCompilationCache
    def setProduceCompilationCache(self,enabled:bool, **kwargs):
        """
            Forces compilation cache to be generated for every subresource script.
        Params:
            1. enabled: bool
        """
        return self.drv.call(None,'Page.setProduceCompilationCache',enabled=enabled, **kwargs)


    # func: addCompilationCache
    def addCompilationCache(self,url:str, data:str, **kwargs):
        """
            Seeds compilation cache for given url. Compilation cache does not survive
            cross-process navigation.
        Params:
            1. url: str
            2. data: str
                Base64-encoded data
        """
        return self.drv.call(None,'Page.addCompilationCache',url=url, data=data, **kwargs)


    # func: clearCompilationCache
    def clearCompilationCache(self,**kwargs):
        """
            Clears seeded compilation cache.
        """
        return self.drv.call(None,'Page.clearCompilationCache',**kwargs)


    # func: generateTestReport
    def generateTestReport(self,message:str, group:str=None, **kwargs):
        """
            Generates a report for testing.
        Params:
            1. message: str
                Message to be displayed in the report.
            2. group: str (OPTIONAL)
                Specifies the endpoint group to deliver the report to.
        """
        return self.drv.call(None,'Page.generateTestReport',message=message, group=group, **kwargs)


    # func: waitForDebugger
    def waitForDebugger(self,**kwargs):
        """
            Pauses page execution. Can be resumed using generic Runtime.runIfWaitingForDebugger.
        """
        return self.drv.call(None,'Page.waitForDebugger',**kwargs)


    # func: setInterceptFileChooserDialog
    def setInterceptFileChooserDialog(self,enabled:bool, **kwargs):
        """
            Intercept file chooser requests and transfer control to protocol clients.
            When file chooser interception is enabled, native file chooser dialog is not shown.
            Instead, a protocol event `Page.fileChooserOpened` is emitted.
        Params:
            1. enabled: bool
        """
        return self.drv.call(None,'Page.setInterceptFileChooserDialog',enabled=enabled, **kwargs)



