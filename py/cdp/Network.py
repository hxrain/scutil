"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# --------------------------------------------------------------------------------
# Network Domain Typing.
# --------------------------------------------------------------------------------
# typing: Resource type as it was perceived by the rendering engine.
ResourceType = str
ResourceTypeEnums = ['Document', 'Stylesheet', 'Image', 'Media', 'Font', 'Script', 'TextTrack', 'XHR', 'Fetch', 'EventSource', 'WebSocket', 'Manifest', 'SignedExchange', 'Ping', 'CSPViolationReport', 'Other']


# typing: Unique loader identifier.
LoaderId = str


# typing: Unique request identifier.
RequestId = str


# typing: Unique intercepted request identifier.
InterceptionId = str


# typing: Network level fetch failure reason.
ErrorReason = str
ErrorReasonEnums = ['Failed', 'Aborted', 'TimedOut', 'AccessDenied', 'ConnectionClosed', 'ConnectionReset', 'ConnectionRefused', 'ConnectionAborted', 'ConnectionFailed', 'NameNotResolved', 'InternetDisconnected', 'AddressUnreachable', 'BlockedByClient', 'BlockedByResponse']


# typing: UTC time in seconds, counted from January 1, 1970.
TimeSinceEpoch = int


# typing: Monotonically increasing time in seconds since an arbitrary point in the past.
MonotonicTime = int


# object: Headers
class Headers(TypingT):
    """
        Request / response headers as keys / values of JSON object.
    """
    def __init__(self):
        pass


# typing: The underlying connection technology that the browser is supposedly using.
ConnectionType = str
ConnectionTypeEnums = ['none', 'cellular2g', 'cellular3g', 'cellular4g', 'bluetooth', 'ethernet', 'wifi', 'wimax', 'other']


# typing: Represents the cookie's 'SameSite' status:https://tools.ietf.org/html/draft-west-first-party-cookies
CookieSameSite = str
CookieSameSiteEnums = ['Strict', 'Lax', 'None']


# typing: Represents the cookie's 'Priority' status:https://tools.ietf.org/html/draft-west-cookie-priority-00
CookiePriority = str
CookiePriorityEnums = ['Low', 'Medium', 'High']


# object: ResourceTiming
class ResourceTiming(TypingT):
    """
        Timing information for the request.
    """
    def __init__(self):
        # Timing's requestTime is a baseline in seconds, while the other numbers are ticks inmilliseconds relatively to this requestTime.
        self.requestTime: int = int
        # Started resolving proxy.
        self.proxyStart: int = int
        # Finished resolving proxy.
        self.proxyEnd: int = int
        # Started DNS address resolve.
        self.dnsStart: int = int
        # Finished DNS address resolve.
        self.dnsEnd: int = int
        # Started connecting to the remote host.
        self.connectStart: int = int
        # Connected to the remote host.
        self.connectEnd: int = int
        # Started SSL handshake.
        self.sslStart: int = int
        # Finished SSL handshake.
        self.sslEnd: int = int
        # Started running ServiceWorker.
        self.workerStart: int = int
        # Finished Starting ServiceWorker.
        self.workerReady: int = int
        # Started fetch event.
        self.workerFetchStart: int = int
        # Settled fetch event respondWith promise.
        self.workerRespondWithSettled: int = int
        # Started sending request.
        self.sendStart: int = int
        # Finished sending request.
        self.sendEnd: int = int
        # Time the server started pushing request.
        self.pushStart: int = int
        # Time the server finished pushing request.
        self.pushEnd: int = int
        # Finished receiving response headers.
        self.receiveHeadersEnd: int = int


# typing: Loading priority of a resource request.
ResourcePriority = str
ResourcePriorityEnums = ['VeryLow', 'Low', 'Medium', 'High', 'VeryHigh']


# object: PostDataEntry
class PostDataEntry(TypingT):
    """
        Post data entry for HTTP request
    """
    def __init__(self):
        # OPTIONAL, bytes
        self.bytes: str = str


# object: Request
class Request(TypingT):
    """
        HTTP request data.
    """
    def __init__(self):
        # Request URL (without fragment).
        self.url: str = str
        # OPTIONAL, Fragment of the requested URL starting with hash, if present.
        self.urlFragment: str = str
        # HTTP request method.
        self.method: str = str
        # HTTP request headers.
        self.headers: Headers = Headers
        # OPTIONAL, HTTP POST request data.
        self.postData: str = str
        # OPTIONAL, True when the request has POST data. Note that postData might still be omitted when this flag is true when the data is too long.
        self.hasPostData: bool = bool
        # OPTIONAL, Request body elements. This will be converted from base64 to binary
        self.postDataEntries: List[PostDataEntry] = [PostDataEntry]
        # OPTIONAL, The mixed content type of the request.
        self.mixedContentType: Security.MixedContentType = Security.MixedContentType
        # Priority of the resource request at the time request is sent.
        self.initialPriority: ResourcePriority = ResourcePriority
        # The referrer policy of the request, as defined in https://www.w3.org/TR/referrer-policy/
        self.referrerPolicy: str = str
        # OPTIONAL, Whether is loaded via link preload.
        self.isLinkPreload: bool = bool


# object: SignedCertificateTimestamp
class SignedCertificateTimestamp(TypingT):
    """
        Details of a signed certificate timestamp (SCT).
    """
    def __init__(self):
        # Validation status.
        self.status: str = str
        # Origin.
        self.origin: str = str
        # Log name / description.
        self.logDescription: str = str
        # Log ID.
        self.logId: str = str
        # Issuance date.
        self.timestamp: TimeSinceEpoch = TimeSinceEpoch
        # Hash algorithm.
        self.hashAlgorithm: str = str
        # Signature algorithm.
        self.signatureAlgorithm: str = str
        # Signature data.
        self.signatureData: str = str


# object: SecurityDetails
class SecurityDetails(TypingT):
    """
        Security details about a request.
    """
    def __init__(self):
        # Protocol name (e.g. "TLS 1.2" or "QUIC").
        self.protocol: str = str
        # Key Exchange used by the connection, or the empty string if not applicable.
        self.keyExchange: str = str
        # OPTIONAL, (EC)DH group used by the connection, if applicable.
        self.keyExchangeGroup: str = str
        # Cipher name.
        self.cipher: str = str
        # OPTIONAL, TLS MAC. Note that AEAD ciphers do not have separate MACs.
        self.mac: str = str
        # Certificate ID value.
        self.certificateId: Security.CertificateId = Security.CertificateId
        # Certificate subject name.
        self.subjectName: str = str
        # Subject Alternative Name (SAN) DNS names and IP addresses.
        self.sanList: List[str] = [str]
        # Name of the issuing CA.
        self.issuer: str = str
        # Certificate valid from date.
        self.validFrom: TimeSinceEpoch = TimeSinceEpoch
        # Certificate valid to (expiration) date
        self.validTo: TimeSinceEpoch = TimeSinceEpoch
        # List of signed certificate timestamps (SCTs).
        self.signedCertificateTimestampList: List[SignedCertificateTimestamp] = [SignedCertificateTimestamp]
        # Whether the request complied with Certificate Transparency policy
        self.certificateTransparencyCompliance: CertificateTransparencyCompliance = CertificateTransparencyCompliance


# typing: Whether the request complied with Certificate Transparency policy.
CertificateTransparencyCompliance = str
CertificateTransparencyComplianceEnums = ['unknown', 'not-compliant', 'compliant']


# typing: The reason why request was blocked.
BlockedReason = str
BlockedReasonEnums = ['other', 'csp', 'mixed-content', 'origin', 'inspector', 'subresource-filter', 'content-type', 'collapsed-by-client', 'coep-frame-resource-needs-coep-header', 'coop-sandboxed-iframe-cannot-navigate-to-coop-page', 'corp-not-same-origin', 'corp-not-same-origin-after-defaulted-to-same-origin-by-coep', 'corp-not-same-site']


# typing: Source of serviceworker response.
ServiceWorkerResponseSource = str
ServiceWorkerResponseSourceEnums = ['cache-storage', 'http-cache', 'fallback-code', 'network']


# object: Response
class Response(TypingT):
    """
        HTTP response data.
    """
    def __init__(self):
        # Response URL. This URL can be different from CachedResource.url in case of redirect.
        self.url: str = str
        # HTTP response status code.
        self.status: int = int
        # HTTP response status text.
        self.statusText: str = str
        # HTTP response headers.
        self.headers: Headers = Headers
        # OPTIONAL, HTTP response headers text.
        self.headersText: str = str
        # Resource mimeType as determined by the browser.
        self.mimeType: str = str
        # OPTIONAL, Refined HTTP request headers that were actually transmitted over the network.
        self.requestHeaders: Headers = Headers
        # OPTIONAL, HTTP request headers text.
        self.requestHeadersText: str = str
        # Specifies whether physical connection was actually reused for this request.
        self.connectionReused: bool = bool
        # Physical connection id that was actually used for this request.
        self.connectionId: int = int
        # OPTIONAL, Remote IP address.
        self.remoteIPAddress: str = str
        # OPTIONAL, Remote port.
        self.remotePort: int = int
        # OPTIONAL, Specifies that the request was served from the disk cache.
        self.fromDiskCache: bool = bool
        # OPTIONAL, Specifies that the request was served from the ServiceWorker.
        self.fromServiceWorker: bool = bool
        # OPTIONAL, Specifies that the request was served from the prefetch cache.
        self.fromPrefetchCache: bool = bool
        # Total number of bytes received for this request so far.
        self.encodedDataLength: int = int
        # OPTIONAL, Timing information for the given request.
        self.timing: ResourceTiming = ResourceTiming
        # OPTIONAL, Response source of response from ServiceWorker.
        self.serviceWorkerResponseSource: ServiceWorkerResponseSource = ServiceWorkerResponseSource
        # OPTIONAL, The time at which the returned response was generated.
        self.responseTime: TimeSinceEpoch = TimeSinceEpoch
        # OPTIONAL, Cache Storage Cache Name.
        self.cacheStorageCacheName: str = str
        # OPTIONAL, Protocol used to fetch this request.
        self.protocol: str = str
        # Security state of the request resource.
        self.securityState: Security.SecurityState = Security.SecurityState
        # OPTIONAL, Security details for the request.
        self.securityDetails: SecurityDetails = SecurityDetails


# object: WebSocketRequest
class WebSocketRequest(TypingT):
    """
        WebSocket request data.
    """
    def __init__(self):
        # HTTP request headers.
        self.headers: Headers = Headers


# object: WebSocketResponse
class WebSocketResponse(TypingT):
    """
        WebSocket response data.
    """
    def __init__(self):
        # HTTP response status code.
        self.status: int = int
        # HTTP response status text.
        self.statusText: str = str
        # HTTP response headers.
        self.headers: Headers = Headers
        # OPTIONAL, HTTP response headers text.
        self.headersText: str = str
        # OPTIONAL, HTTP request headers.
        self.requestHeaders: Headers = Headers
        # OPTIONAL, HTTP request headers text.
        self.requestHeadersText: str = str


# object: WebSocketFrame
class WebSocketFrame(TypingT):
    """
        WebSocket message data. This represents an entire WebSocket message, not just a fragmented frame as the name suggests.
    """
    def __init__(self):
        # WebSocket message opcode.
        self.opcode: int = int
        # WebSocket message mask.
        self.mask: bool = bool
        # WebSocket message payload data.If the opcode is 1, this is a text message and payloadData is a UTF-8 string.If the opcode isn't 1, then payloadData is a base64 encoded string representing binary data.
        self.payloadData: str = str


# object: CachedResource
class CachedResource(TypingT):
    """
        Information about the cached resource.
    """
    def __init__(self):
        # Resource URL. This is the url of the original network request.
        self.url: str = str
        # Type of this resource.
        self.type: ResourceType = ResourceType
        # OPTIONAL, Cached response data.
        self.response: Response = Response
        # Cached response body size.
        self.bodySize: int = int


# object: Initiator
class Initiator(TypingT):
    """
        Information about the request initiator.
    """
    def __init__(self):
        # Type of this initiator.
        self.type: str = str
        # OPTIONAL, Initiator JavaScript stack trace, set for Script only.
        self.stack: Runtime.StackTrace = Runtime.StackTrace
        # OPTIONAL, Initiator URL, set for Parser type or for Script type (when script is importing module) or for SignedExchange type.
        self.url: str = str
        # OPTIONAL, Initiator line number, set for Parser type or for Script type (when script is importingmodule) (0-based).
        self.lineNumber: int = int


# object: Cookie
class Cookie(TypingT):
    """
        Cookie object
    """
    def __init__(self):
        # Cookie name.
        self.name: str = str
        # Cookie value.
        self.value: str = str
        # Cookie domain.
        self.domain: str = str
        # Cookie path.
        self.path: str = str
        # Cookie expiration date as the number of seconds since the UNIX epoch.
        self.expires: int = int
        # Cookie size.
        self.size: int = int
        # True if cookie is http-only.
        self.httpOnly: bool = bool
        # True if cookie is secure.
        self.secure: bool = bool
        # True in case of session cookie.
        self.session: bool = bool
        # OPTIONAL, Cookie SameSite type.
        self.sameSite: CookieSameSite = CookieSameSite
        # Cookie Priority
        self.priority: CookiePriority = CookiePriority


# typing: Types of reasons why a cookie may not be stored from a response.
SetCookieBlockedReason = str
SetCookieBlockedReasonEnums = ['SecureOnly', 'SameSiteStrict', 'SameSiteLax', 'SameSiteUnspecifiedTreatedAsLax', 'SameSiteNoneInsecure', 'UserPreferences', 'SyntaxError', 'SchemeNotSupported', 'OverwriteSecure', 'InvalidDomain', 'InvalidPrefix', 'UnknownError']


# typing: Types of reasons why a cookie may not be sent with a request.
CookieBlockedReason = str
CookieBlockedReasonEnums = ['SecureOnly', 'NotOnPath', 'DomainMismatch', 'SameSiteStrict', 'SameSiteLax', 'SameSiteUnspecifiedTreatedAsLax', 'SameSiteNoneInsecure', 'UserPreferences', 'UnknownError']


# object: BlockedSetCookieWithReason
class BlockedSetCookieWithReason(TypingT):
    """
        A cookie which was not stored from a response with the corresponding reason.
    """
    def __init__(self):
        # The reason(s) this cookie was blocked.
        self.blockedReasons: List[SetCookieBlockedReason] = [SetCookieBlockedReason]
        # The string representing this individual cookie as it would appear in the header.This is not the entire "cookie" or "set-cookie" header which could have multiple cookies.
        self.cookieLine: str = str
        # OPTIONAL, The cookie object which represents the cookie which was not stored. It is optional becausesometimes complete cookie information is not available, such as in the case of parsingerrors.
        self.cookie: Cookie = Cookie


# object: BlockedCookieWithReason
class BlockedCookieWithReason(TypingT):
    """
        A cookie with was not sent with a request with the corresponding reason.
    """
    def __init__(self):
        # The reason(s) the cookie was blocked.
        self.blockedReasons: List[CookieBlockedReason] = [CookieBlockedReason]
        # The cookie object representing the cookie which was not sent.
        self.cookie: Cookie = Cookie


# object: CookieParam
class CookieParam(TypingT):
    """
        Cookie parameter object
    """
    def __init__(self):
        # Cookie name.
        self.name: str = str
        # Cookie value.
        self.value: str = str
        # OPTIONAL, The request-URI to associate with the setting of the cookie. This value can affect thedefault domain and path values of the created cookie.
        self.url: str = str
        # OPTIONAL, Cookie domain.
        self.domain: str = str
        # OPTIONAL, Cookie path.
        self.path: str = str
        # OPTIONAL, True if cookie is secure.
        self.secure: bool = bool
        # OPTIONAL, True if cookie is http-only.
        self.httpOnly: bool = bool
        # OPTIONAL, Cookie SameSite type.
        self.sameSite: CookieSameSite = CookieSameSite
        # OPTIONAL, Cookie expiration date, session cookie if not set
        self.expires: TimeSinceEpoch = TimeSinceEpoch
        # OPTIONAL, Cookie Priority.
        self.priority: CookiePriority = CookiePriority


# object: AuthChallenge
class AuthChallenge(TypingT):
    """
        Authorization challenge for HTTP status code 401 or 407.
    """
    def __init__(self):
        # OPTIONAL, Source of the authentication challenge.
        self.source: str = str
        # Origin of the challenger.
        self.origin: str = str
        # The authentication scheme used, such as basic or digest
        self.scheme: str = str
        # The realm of the challenge. May be empty.
        self.realm: str = str


# object: AuthChallengeResponse
class AuthChallengeResponse(TypingT):
    """
        Response to an AuthChallenge.
    """
    def __init__(self):
        # The decision on what to do in response to the authorization challenge.  Default meansdeferring to the default behavior of the net stack, which will likely either the Cancelauthentication or display a popup dialog box.
        self.response: str = str
        # OPTIONAL, The username to provide, possibly empty. Should only be set if response isProvideCredentials.
        self.username: str = str
        # OPTIONAL, The password to provide, possibly empty. Should only be set if response isProvideCredentials.
        self.password: str = str


# typing: Stages of the interception to begin intercepting. Request will intercept before the request issent. Response will intercept after the response is received.
InterceptionStage = str
InterceptionStageEnums = ['Request', 'HeadersReceived']


# object: RequestPattern
class RequestPattern(TypingT):
    """
        Request pattern for interception.
    """
    def __init__(self):
        # OPTIONAL, Wildcards ('*' -> zero or more, '?' -> exactly one) are allowed. Escape character isbackslash. Omitting is equivalent to "*".
        self.urlPattern: str = str
        # OPTIONAL, If set, only requests for matching resource types will be intercepted.
        self.resourceType: ResourceType = ResourceType
        # OPTIONAL, Stage at wich to begin intercepting requests. Default is Request.
        self.interceptionStage: InterceptionStage = InterceptionStage


# object: SignedExchangeSignature
class SignedExchangeSignature(TypingT):
    """
        Information about a signed exchange signature.
        https://wicg.github.io/webpackage/draft-yasskin-httpbis-origin-signed-exchanges-impl.html#rfc.section.3.1
    """
    def __init__(self):
        # Signed exchange signature label.
        self.label: str = str
        # The hex string of signed exchange signature.
        self.signature: str = str
        # Signed exchange signature integrity.
        self.integrity: str = str
        # OPTIONAL, Signed exchange signature cert Url.
        self.certUrl: str = str
        # OPTIONAL, The hex string of signed exchange signature cert sha256.
        self.certSha256: str = str
        # Signed exchange signature validity Url.
        self.validityUrl: str = str
        # Signed exchange signature date.
        self.date: int = int
        # Signed exchange signature expires.
        self.expires: int = int
        # OPTIONAL, The encoded certificates.
        self.certificates: List[str] = [str]


# object: SignedExchangeHeader
class SignedExchangeHeader(TypingT):
    """
        Information about a signed exchange header.
        https://wicg.github.io/webpackage/draft-yasskin-httpbis-origin-signed-exchanges-impl.html#cbor-representation
    """
    def __init__(self):
        # Signed exchange request URL.
        self.requestUrl: str = str
        # Signed exchange response code.
        self.responseCode: int = int
        # Signed exchange response headers.
        self.responseHeaders: Headers = Headers
        # Signed exchange response signature.
        self.signatures: List[SignedExchangeSignature] = [SignedExchangeSignature]
        # Signed exchange header integrity hash in the form of "sha256-<base64-hash-value>".
        self.headerIntegrity: str = str


# typing: Field type for a signed exchange related error.
SignedExchangeErrorField = str
SignedExchangeErrorFieldEnums = ['signatureSig', 'signatureIntegrity', 'signatureCertUrl', 'signatureCertSha256', 'signatureValidityUrl', 'signatureTimestamps']


# object: SignedExchangeError
class SignedExchangeError(TypingT):
    """
        Information about a signed exchange response.
    """
    def __init__(self):
        # Error message.
        self.message: str = str
        # OPTIONAL, The index of the signature which caused the error.
        self.signatureIndex: int = int
        # OPTIONAL, The field which caused the error.
        self.errorField: SignedExchangeErrorField = SignedExchangeErrorField


# object: SignedExchangeInfo
class SignedExchangeInfo(TypingT):
    """
        Information about a signed exchange response.
    """
    def __init__(self):
        # The outer response of signed HTTP exchange which was received from network.
        self.outerResponse: Response = Response
        # OPTIONAL, Information about the signed exchange header.
        self.header: SignedExchangeHeader = SignedExchangeHeader
        # OPTIONAL, Security details for the signed exchange header.
        self.securityDetails: SecurityDetails = SecurityDetails
        # OPTIONAL, Errors occurred while handling the signed exchagne.
        self.errors: List[SignedExchangeError] = [SignedExchangeError]


# typing: CrossOriginOpenerPolicyValue
CrossOriginOpenerPolicyValue = str
CrossOriginOpenerPolicyValueEnums = ['SameOrigin', 'SameOriginAllowPopups', 'UnsafeNone', 'SameOriginPlusCoep']


# object: CrossOriginOpenerPolicyStatus
class CrossOriginOpenerPolicyStatus(TypingT):
    """
        CrossOriginOpenerPolicyStatus
    """
    def __init__(self):
        # value
        self.value: CrossOriginOpenerPolicyValue = CrossOriginOpenerPolicyValue


# typing: CrossOriginEmbedderPolicyValue
CrossOriginEmbedderPolicyValue = str
CrossOriginEmbedderPolicyValueEnums = ['None', 'RequireCorp']


# object: CrossOriginEmbedderPolicyStatus
class CrossOriginEmbedderPolicyStatus(TypingT):
    """
        CrossOriginEmbedderPolicyStatus
    """
    def __init__(self):
        # value
        self.value: CrossOriginEmbedderPolicyValue = CrossOriginEmbedderPolicyValue


# object: SecurityIsolationStatus
class SecurityIsolationStatus(TypingT):
    """
        SecurityIsolationStatus
    """
    def __init__(self):
        # coop
        self.coop: CrossOriginOpenerPolicyStatus = CrossOriginOpenerPolicyStatus
        # coep
        self.coep: CrossOriginEmbedderPolicyStatus = CrossOriginEmbedderPolicyStatus


# --------------------------------------------------------------------------------
# Network Domain Event.
# --------------------------------------------------------------------------------
# event: dataReceived
class dataReceived(EventT):
    """
        Fired when data chunk was received over the network.
    """
    event="Network.dataReceived"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # Data chunk length.
        self.dataLength: int = int
        # Actual bytes received (might be less than dataLength for compressed encodings).
        self.encodedDataLength: int = int


# event: eventSourceMessageReceived
class eventSourceMessageReceived(EventT):
    """
        Fired when EventSource message is received.
    """
    event="Network.eventSourceMessageReceived"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # Message type.
        self.eventName: str = str
        # Message identifier.
        self.eventId: str = str
        # Message content.
        self.data: str = str


# event: loadingFailed
class loadingFailed(EventT):
    """
        Fired when HTTP request has failed to load.
    """
    event="Network.loadingFailed"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # Resource type.
        self.type: ResourceType = ResourceType
        # User friendly error message.
        self.errorText: str = str
        # OPTIONAL, True if loading was canceled.
        self.canceled: bool = bool
        # OPTIONAL, The reason why loading was blocked, if any.
        self.blockedReason: BlockedReason = BlockedReason


# event: loadingFinished
class loadingFinished(EventT):
    """
        Fired when HTTP request has finished loading.
    """
    event="Network.loadingFinished"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # Total number of bytes received for this request.
        self.encodedDataLength: int = int
        # OPTIONAL, Set when 1) response was blocked by Cross-Origin Read Blocking and also2) this needs to be reported to the DevTools console.
        self.shouldReportCorbBlocking: bool = bool


# event: requestIntercepted
class requestIntercepted(EventT):
    """
        Details of an intercepted HTTP request, which must be either allowed, blocked, modified or
        mocked.
        Deprecated, use Fetch.requestPaused instead.
    """
    event="Network.requestIntercepted"
    def __init__(self):
        # Each request the page makes will have a unique id, however if any redirects are encounteredwhile processing that fetch, they will be reported with the same id as the original fetch.Likewise if HTTP authentication is needed then the same fetch id will be used.
        self.interceptionId: InterceptionId = InterceptionId
        # request
        self.request: Request = Request
        # The id of the frame that initiated the request.
        self.frameId: Page.FrameId = Page.FrameId
        # How the requested resource will be used.
        self.resourceType: ResourceType = ResourceType
        # Whether this is a navigation request, which can abort the navigation completely.
        self.isNavigationRequest: bool = bool
        # OPTIONAL, Set if the request is a navigation that will result in a download.Only present after response is received from the server (i.e. HeadersReceived stage).
        self.isDownload: bool = bool
        # OPTIONAL, Redirect location, only sent if a redirect was intercepted.
        self.redirectUrl: str = str
        # OPTIONAL, Details of the Authorization Challenge encountered. If this is set thencontinueInterceptedRequest must contain an authChallengeResponse.
        self.authChallenge: AuthChallenge = AuthChallenge
        # OPTIONAL, Response error if intercepted at response stage or if redirect occurred while interceptingrequest.
        self.responseErrorReason: ErrorReason = ErrorReason
        # OPTIONAL, Response code if intercepted at response stage or if redirect occurred while interceptingrequest or auth retry occurred.
        self.responseStatusCode: int = int
        # OPTIONAL, Response headers if intercepted at the response stage or if redirect occurred whileintercepting request or auth retry occurred.
        self.responseHeaders: Headers = Headers
        # OPTIONAL, If the intercepted request had a corresponding requestWillBeSent event fired for it, thenthis requestId will be the same as the requestId present in the requestWillBeSent event.
        self.requestId: RequestId = RequestId


# event: requestServedFromCache
class requestServedFromCache(EventT):
    """
        Fired if request ended up loading from cache.
    """
    event="Network.requestServedFromCache"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId


# event: requestWillBeSent
class requestWillBeSent(EventT):
    """
        Fired when page is about to send HTTP request.
    """
    event="Network.requestWillBeSent"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Loader identifier. Empty string if the request is fetched from worker.
        self.loaderId: LoaderId = LoaderId
        # URL of the document this request is loaded for.
        self.documentURL: str = str
        # Request data.
        self.request: Request = Request
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # Timestamp.
        self.wallTime: TimeSinceEpoch = TimeSinceEpoch
        # Request initiator.
        self.initiator: Initiator = Initiator
        # OPTIONAL, Redirect response data.
        self.redirectResponse: Response = Response
        # OPTIONAL, Type of this resource.
        self.type: ResourceType = ResourceType
        # OPTIONAL, Frame identifier.
        self.frameId: Page.FrameId = Page.FrameId
        # OPTIONAL, Whether the request is initiated by a user gesture. Defaults to false.
        self.hasUserGesture: bool = bool


# event: resourceChangedPriority
class resourceChangedPriority(EventT):
    """
        Fired when resource loading priority is changed
    """
    event="Network.resourceChangedPriority"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # New priority
        self.newPriority: ResourcePriority = ResourcePriority
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime


# event: signedExchangeReceived
class signedExchangeReceived(EventT):
    """
        Fired when a signed exchange was received over the network
    """
    event="Network.signedExchangeReceived"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Information about the signed exchange response.
        self.info: SignedExchangeInfo = SignedExchangeInfo


# event: responseReceived
class responseReceived(EventT):
    """
        Fired when HTTP response is available.
    """
    event="Network.responseReceived"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Loader identifier. Empty string if the request is fetched from worker.
        self.loaderId: LoaderId = LoaderId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # Resource type.
        self.type: ResourceType = ResourceType
        # Response data.
        self.response: Response = Response
        # OPTIONAL, Frame identifier.
        self.frameId: Page.FrameId = Page.FrameId


# event: webSocketClosed
class webSocketClosed(EventT):
    """
        Fired when WebSocket is closed.
    """
    event="Network.webSocketClosed"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime


# event: webSocketCreated
class webSocketCreated(EventT):
    """
        Fired upon WebSocket creation.
    """
    event="Network.webSocketCreated"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # WebSocket request URL.
        self.url: str = str
        # OPTIONAL, Request initiator.
        self.initiator: Initiator = Initiator


# event: webSocketFrameError
class webSocketFrameError(EventT):
    """
        Fired when WebSocket message error occurs.
    """
    event="Network.webSocketFrameError"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # WebSocket error message.
        self.errorMessage: str = str


# event: webSocketFrameReceived
class webSocketFrameReceived(EventT):
    """
        Fired when WebSocket message is received.
    """
    event="Network.webSocketFrameReceived"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # WebSocket response data.
        self.response: WebSocketFrame = WebSocketFrame


# event: webSocketFrameSent
class webSocketFrameSent(EventT):
    """
        Fired when WebSocket message is sent.
    """
    event="Network.webSocketFrameSent"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # WebSocket response data.
        self.response: WebSocketFrame = WebSocketFrame


# event: webSocketHandshakeResponseReceived
class webSocketHandshakeResponseReceived(EventT):
    """
        Fired when WebSocket handshake response becomes available.
    """
    event="Network.webSocketHandshakeResponseReceived"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # WebSocket response data.
        self.response: WebSocketResponse = WebSocketResponse


# event: webSocketWillSendHandshakeRequest
class webSocketWillSendHandshakeRequest(EventT):
    """
        Fired when WebSocket is about to initiate handshake.
    """
    event="Network.webSocketWillSendHandshakeRequest"
    def __init__(self):
        # Request identifier.
        self.requestId: RequestId = RequestId
        # Timestamp.
        self.timestamp: MonotonicTime = MonotonicTime
        # UTC Timestamp.
        self.wallTime: TimeSinceEpoch = TimeSinceEpoch
        # WebSocket request data.
        self.request: WebSocketRequest = WebSocketRequest


# event: requestWillBeSentExtraInfo
class requestWillBeSentExtraInfo(EventT):
    """
        Fired when additional information about a requestWillBeSent event is available from the
        network stack. Not every requestWillBeSent event will have an additional
        requestWillBeSentExtraInfo fired for it, and there is no guarantee whether requestWillBeSent
        or requestWillBeSentExtraInfo will be fired first for the same request.
    """
    event="Network.requestWillBeSentExtraInfo"
    def __init__(self):
        # Request identifier. Used to match this information to an existing requestWillBeSent event.
        self.requestId: RequestId = RequestId
        # A list of cookies potentially associated to the requested URL. This includes both cookies sent withthe request and the ones not sent; the latter are distinguished by having blockedReason field set.
        self.associatedCookies: List[BlockedCookieWithReason] = [BlockedCookieWithReason]
        # Raw request headers as they will be sent over the wire.
        self.headers: Headers = Headers


# event: responseReceivedExtraInfo
class responseReceivedExtraInfo(EventT):
    """
        Fired when additional information about a responseReceived event is available from the network
        stack. Not every responseReceived event will have an additional responseReceivedExtraInfo for
        it, and responseReceivedExtraInfo may be fired before or after responseReceived.
    """
    event="Network.responseReceivedExtraInfo"
    def __init__(self):
        # Request identifier. Used to match this information to another responseReceived event.
        self.requestId: RequestId = RequestId
        # A list of cookies which were not stored from the response along with the correspondingreasons for blocking. The cookies here may not be valid due to syntax errors, whichare represented by the invalid cookie line string instead of a proper cookie.
        self.blockedCookies: List[BlockedSetCookieWithReason] = [BlockedSetCookieWithReason]
        # Raw response headers as they were received over the wire.
        self.headers: Headers = Headers
        # OPTIONAL, Raw response header text as it was received over the wire. The raw text may not always beavailable, such as in the case of HTTP/2 or QUIC.
        self.headersText: str = str


from cdp import Debugger
from cdp import Runtime
from cdp import Security
from cdp import Emulation
from cdp import Page
# ================================================================================
# Network Domain Class.
# ================================================================================
class Network(DomainT):
    """
        Network domain allows tracking network activities of the page. It exposes information about http,
        file, data and other requests and responses, their headers, bodies, timing, etc.
    """
    def __init__(self, drv):
        self.drv = drv


    # return: canClearBrowserCacheReturn
    class canClearBrowserCacheReturn(ReturnT):
        def __init__(self):
            # True if browser cache can be cleared.
            self.result: bool = bool


    # func: canClearBrowserCache
    def canClearBrowserCache(self,**kwargs) -> canClearBrowserCacheReturn:
        """
            Tells whether clearing browser cache is supported.
        Return: canClearBrowserCacheReturn
        """
        return self.drv.call(Network.canClearBrowserCacheReturn,'Network.canClearBrowserCache',**kwargs)


    # return: canClearBrowserCookiesReturn
    class canClearBrowserCookiesReturn(ReturnT):
        def __init__(self):
            # True if browser cookies can be cleared.
            self.result: bool = bool


    # func: canClearBrowserCookies
    def canClearBrowserCookies(self,**kwargs) -> canClearBrowserCookiesReturn:
        """
            Tells whether clearing browser cookies is supported.
        Return: canClearBrowserCookiesReturn
        """
        return self.drv.call(Network.canClearBrowserCookiesReturn,'Network.canClearBrowserCookies',**kwargs)


    # return: canEmulateNetworkConditionsReturn
    class canEmulateNetworkConditionsReturn(ReturnT):
        def __init__(self):
            # True if emulation of network conditions is supported.
            self.result: bool = bool


    # func: canEmulateNetworkConditions
    def canEmulateNetworkConditions(self,**kwargs) -> canEmulateNetworkConditionsReturn:
        """
            Tells whether emulation of network conditions is supported.
        Return: canEmulateNetworkConditionsReturn
        """
        return self.drv.call(Network.canEmulateNetworkConditionsReturn,'Network.canEmulateNetworkConditions',**kwargs)


    # func: clearBrowserCache
    def clearBrowserCache(self,**kwargs):
        """
            Clears browser cache.
        """
        return self.drv.call(None,'Network.clearBrowserCache',**kwargs)


    # func: clearBrowserCookies
    def clearBrowserCookies(self,**kwargs):
        """
            Clears browser cookies.
        """
        return self.drv.call(None,'Network.clearBrowserCookies',**kwargs)


    # func: continueInterceptedRequest
    def continueInterceptedRequest(self,interceptionId:InterceptionId, errorReason:ErrorReason=None, rawResponse:str=None, url:str=None, method:str=None, postData:str=None, headers:Headers=None, authChallengeResponse:AuthChallengeResponse=None, **kwargs):
        """
            Response to Network.requestIntercepted which either modifies the request to continue with any
            modifications, or blocks it, or completes it with the provided response bytes. If a network
            fetch occurs as a result which encounters a redirect an additional Network.requestIntercepted
            event will be sent with the same InterceptionId.
            Deprecated, use Fetch.continueRequest, Fetch.fulfillRequest and Fetch.failRequest instead.
        Params:
            1. interceptionId: InterceptionId
            2. errorReason: ErrorReason (OPTIONAL)
                If set this causes the request to fail with the given reason. Passing `Aborted` for requestsmarked with `isNavigationRequest` also cancels the navigation. Must not be set in responseto an authChallenge.
            3. rawResponse: str (OPTIONAL)
                If set the requests completes using with the provided base64 encoded raw response, includingHTTP status line and headers etc... Must not be set in response to an authChallenge.
            4. url: str (OPTIONAL)
                If set the request url will be modified in a way that's not observable by page. Must not beset in response to an authChallenge.
            5. method: str (OPTIONAL)
                If set this allows the request method to be overridden. Must not be set in response to anauthChallenge.
            6. postData: str (OPTIONAL)
                If set this allows postData to be set. Must not be set in response to an authChallenge.
            7. headers: Headers (OPTIONAL)
                If set this allows the request headers to be changed. Must not be set in response to anauthChallenge.
            8. authChallengeResponse: AuthChallengeResponse (OPTIONAL)
                Response to a requestIntercepted with an authChallenge. Must not be set otherwise.
        """
        return self.drv.call(None,'Network.continueInterceptedRequest',interceptionId=interceptionId, errorReason=errorReason, rawResponse=rawResponse, url=url, method=method, postData=postData, headers=headers, authChallengeResponse=authChallengeResponse, **kwargs)


    # func: deleteCookies
    def deleteCookies(self,name:str, url:str=None, domain:str=None, path:str=None, **kwargs):
        """
            Deletes browser cookies with matching name and url or domain/path pair.
        Params:
            1. name: str
                Name of the cookies to remove.
            2. url: str (OPTIONAL)
                If specified, deletes all the cookies with the given name where domain and path matchprovided URL.
            3. domain: str (OPTIONAL)
                If specified, deletes only cookies with the exact domain.
            4. path: str (OPTIONAL)
                If specified, deletes only cookies with the exact path.
        """
        return self.drv.call(None,'Network.deleteCookies',name=name, url=url, domain=domain, path=path, **kwargs)


    # func: disable
    def disable(self,**kwargs):
        """
            Disables network tracking, prevents network events from being sent to the client.
        """
        return self.drv.call(None,'Network.disable',**kwargs)


    # func: emulateNetworkConditions
    def emulateNetworkConditions(self,offline:bool, latency:int, downloadThroughput:int, uploadThroughput:int, connectionType:ConnectionType=None, **kwargs):
        """
            Activates emulation of network conditions.
        Params:
            1. offline: bool
                True to emulate internet disconnection.
            2. latency: int
                Minimum latency from request sent to response headers received (ms).
            3. downloadThroughput: int
                Maximal aggregated download throughput (bytes/sec). -1 disables download throttling.
            4. uploadThroughput: int
                Maximal aggregated upload throughput (bytes/sec).  -1 disables upload throttling.
            5. connectionType: ConnectionType (OPTIONAL)
                Connection type if known.
        """
        return self.drv.call(None,'Network.emulateNetworkConditions',offline=offline, latency=latency, downloadThroughput=downloadThroughput, uploadThroughput=uploadThroughput, connectionType=connectionType, **kwargs)


    # func: enable
    def enable(self,maxTotalBufferSize:int=None, maxResourceBufferSize:int=None, maxPostDataSize:int=None, **kwargs):
        """
            Enables network tracking, network events will now be delivered to the client.
        Params:
            1. maxTotalBufferSize: int (OPTIONAL)
                Buffer size in bytes to use when preserving network payloads (XHRs, etc).
            2. maxResourceBufferSize: int (OPTIONAL)
                Per-resource buffer size in bytes to use when preserving network payloads (XHRs, etc).
            3. maxPostDataSize: int (OPTIONAL)
                Longest post body size (in bytes) that would be included in requestWillBeSent notification
        """
        return self.drv.call(None,'Network.enable',maxTotalBufferSize=maxTotalBufferSize, maxResourceBufferSize=maxResourceBufferSize, maxPostDataSize=maxPostDataSize, **kwargs)


    # return: getAllCookiesReturn
    class getAllCookiesReturn(ReturnT):
        def __init__(self):
            # Array of cookie objects.
            self.cookies: List[Cookie] = [Cookie]


    # func: getAllCookies
    def getAllCookies(self,**kwargs) -> getAllCookiesReturn:
        """
            Returns all browser cookies. Depending on the backend support, will return detailed cookie
            information in the `cookies` field.
        Return: getAllCookiesReturn
        """
        return self.drv.call(Network.getAllCookiesReturn,'Network.getAllCookies',**kwargs)


    # return: getCertificateReturn
    class getCertificateReturn(ReturnT):
        def __init__(self):
            # tableNames
            self.tableNames: List[str] = [str]


    # func: getCertificate
    def getCertificate(self,origin:str, **kwargs) -> getCertificateReturn:
        """
            Returns the DER-encoded certificate.
        Params:
            1. origin: str
                Origin to get certificate for.
        Return: getCertificateReturn
        """
        return self.drv.call(Network.getCertificateReturn,'Network.getCertificate',origin=origin, **kwargs)


    # return: getCookiesReturn
    class getCookiesReturn(ReturnT):
        def __init__(self):
            # Array of cookie objects.
            self.cookies: List[Cookie] = [Cookie]


    # func: getCookies
    def getCookies(self,urls:List[str]=None, **kwargs) -> getCookiesReturn:
        """
            Returns all browser cookies for the current URL. Depending on the backend support, will return
            detailed cookie information in the `cookies` field.
        Params:
            1. urls: List[str] (OPTIONAL)
                The list of URLs for which applicable cookies will be fetched.If not specified, it's assumed to be set to the list containingthe URLs of the page and all of its subframes.
        Return: getCookiesReturn
        """
        return self.drv.call(Network.getCookiesReturn,'Network.getCookies',urls=urls, **kwargs)


    # return: getResponseBodyReturn
    class getResponseBodyReturn(ReturnT):
        def __init__(self):
            # Response body.
            self.body: str = str
            # True, if content was sent as base64.
            self.base64Encoded: bool = bool


    # func: getResponseBody
    def getResponseBody(self,requestId:RequestId, **kwargs) -> getResponseBodyReturn:
        """
            Returns content served for the given request.
        Params:
            1. requestId: RequestId
                Identifier of the network request to get content for.
        Return: getResponseBodyReturn
        """
        return self.drv.call(Network.getResponseBodyReturn,'Network.getResponseBody',requestId=requestId, **kwargs)


    # return: getRequestPostDataReturn
    class getRequestPostDataReturn(ReturnT):
        def __init__(self):
            # Request body string, omitting files from multipart requests
            self.postData: str = str


    # func: getRequestPostData
    def getRequestPostData(self,requestId:RequestId, **kwargs) -> getRequestPostDataReturn:
        """
            Returns post data sent with the request. Returns an error when no data was sent with the request.
        Params:
            1. requestId: RequestId
                Identifier of the network request to get content for.
        Return: getRequestPostDataReturn
        """
        return self.drv.call(Network.getRequestPostDataReturn,'Network.getRequestPostData',requestId=requestId, **kwargs)


    # return: getResponseBodyForInterceptionReturn
    class getResponseBodyForInterceptionReturn(ReturnT):
        def __init__(self):
            # Response body.
            self.body: str = str
            # True, if content was sent as base64.
            self.base64Encoded: bool = bool


    # func: getResponseBodyForInterception
    def getResponseBodyForInterception(self,interceptionId:InterceptionId, **kwargs) -> getResponseBodyForInterceptionReturn:
        """
            Returns content served for the given currently intercepted request.
        Params:
            1. interceptionId: InterceptionId
                Identifier for the intercepted request to get body for.
        Return: getResponseBodyForInterceptionReturn
        """
        return self.drv.call(Network.getResponseBodyForInterceptionReturn,'Network.getResponseBodyForInterception',interceptionId=interceptionId, **kwargs)


    # return: takeResponseBodyForInterceptionAsStreamReturn
    class takeResponseBodyForInterceptionAsStreamReturn(ReturnT):
        def __init__(self):
            # stream
            self.stream: IO.StreamHandle = IO.StreamHandle


    # func: takeResponseBodyForInterceptionAsStream
    def takeResponseBodyForInterceptionAsStream(self,interceptionId:InterceptionId, **kwargs) -> takeResponseBodyForInterceptionAsStreamReturn:
        """
            Returns a handle to the stream representing the response body. Note that after this command,
            the intercepted request can't be continued as is -- you either need to cancel it or to provide
            the response body. The stream only supports sequential read, IO.read will fail if the position
            is specified.
        Params:
            1. interceptionId: InterceptionId
        Return: takeResponseBodyForInterceptionAsStreamReturn
        """
        return self.drv.call(Network.takeResponseBodyForInterceptionAsStreamReturn,'Network.takeResponseBodyForInterceptionAsStream',interceptionId=interceptionId, **kwargs)


    # func: replayXHR
    def replayXHR(self,requestId:RequestId, **kwargs):
        """
            This method sends a new XMLHttpRequest which is identical to the original one. The following
            parameters should be identical: method, url, async, request body, extra headers, withCredentials
            attribute, user, password.
        Params:
            1. requestId: RequestId
                Identifier of XHR to replay.
        """
        return self.drv.call(None,'Network.replayXHR',requestId=requestId, **kwargs)


    # return: searchInResponseBodyReturn
    class searchInResponseBodyReturn(ReturnT):
        def __init__(self):
            # List of search matches.
            self.result: List[Debugger.SearchMatch] = [Debugger.SearchMatch]


    # func: searchInResponseBody
    def searchInResponseBody(self,requestId:RequestId, query:str, caseSensitive:bool=None, isRegex:bool=None, **kwargs) -> searchInResponseBodyReturn:
        """
            Searches for given string in response content.
        Params:
            1. requestId: RequestId
                Identifier of the network response to search.
            2. query: str
                String to search for.
            3. caseSensitive: bool (OPTIONAL)
                If true, search is case sensitive.
            4. isRegex: bool (OPTIONAL)
                If true, treats string parameter as regex.
        Return: searchInResponseBodyReturn
        """
        return self.drv.call(Network.searchInResponseBodyReturn,'Network.searchInResponseBody',requestId=requestId, query=query, caseSensitive=caseSensitive, isRegex=isRegex, **kwargs)


    # func: setBlockedURLs
    def setBlockedURLs(self,urls:List[str], **kwargs):
        """
            Blocks URLs from loading.
        Params:
            1. urls: List[str]
                URL patterns to block. Wildcards ('*') are allowed.
        """
        return self.drv.call(None,'Network.setBlockedURLs',urls=urls, **kwargs)


    # func: setBypassServiceWorker
    def setBypassServiceWorker(self,bypass:bool, **kwargs):
        """
            Toggles ignoring of service worker for each request.
        Params:
            1. bypass: bool
                Bypass service worker and load from network.
        """
        return self.drv.call(None,'Network.setBypassServiceWorker',bypass=bypass, **kwargs)


    # func: setCacheDisabled
    def setCacheDisabled(self,cacheDisabled:bool, **kwargs):
        """
            Toggles ignoring cache for each request. If `true`, cache will not be used.
        Params:
            1. cacheDisabled: bool
                Cache disabled state.
        """
        return self.drv.call(None,'Network.setCacheDisabled',cacheDisabled=cacheDisabled, **kwargs)


    # return: setCookieReturn
    class setCookieReturn(ReturnT):
        def __init__(self):
            # True if successfully set cookie.
            self.success: bool = bool


    # func: setCookie
    def setCookie(self,name:str, value:str, url:str=None, domain:str=None, path:str=None, secure:bool=None, httpOnly:bool=None, sameSite:CookieSameSite=None, expires:TimeSinceEpoch=None, priority:CookiePriority=None, **kwargs) -> setCookieReturn:
        """
            Sets a cookie with the given cookie data; may overwrite equivalent cookies if they exist.
        Params:
            1. name: str
                Cookie name.
            2. value: str
                Cookie value.
            3. url: str (OPTIONAL)
                The request-URI to associate with the setting of the cookie. This value can affect thedefault domain and path values of the created cookie.
            4. domain: str (OPTIONAL)
                Cookie domain.
            5. path: str (OPTIONAL)
                Cookie path.
            6. secure: bool (OPTIONAL)
                True if cookie is secure.
            7. httpOnly: bool (OPTIONAL)
                True if cookie is http-only.
            8. sameSite: CookieSameSite (OPTIONAL)
                Cookie SameSite type.
            9. expires: TimeSinceEpoch (OPTIONAL)
                Cookie expiration date, session cookie if not set
            10. priority: CookiePriority (OPTIONAL)
                Cookie Priority type.
        Return: setCookieReturn
        """
        return self.drv.call(Network.setCookieReturn,'Network.setCookie',name=name, value=value, url=url, domain=domain, path=path, secure=secure, httpOnly=httpOnly, sameSite=sameSite, expires=expires, priority=priority, **kwargs)


    # func: setCookies
    def setCookies(self,cookies:List[CookieParam], **kwargs):
        """
            Sets given cookies.
        Params:
            1. cookies: List[CookieParam]
                Cookies to be set.
        """
        return self.drv.call(None,'Network.setCookies',cookies=cookies, **kwargs)


    # func: setDataSizeLimitsForTest
    def setDataSizeLimitsForTest(self,maxTotalSize:int, maxResourceSize:int, **kwargs):
        """
            For testing.
        Params:
            1. maxTotalSize: int
                Maximum total buffer size.
            2. maxResourceSize: int
                Maximum per-resource size.
        """
        return self.drv.call(None,'Network.setDataSizeLimitsForTest',maxTotalSize=maxTotalSize, maxResourceSize=maxResourceSize, **kwargs)


    # func: setExtraHTTPHeaders
    def setExtraHTTPHeaders(self,headers:Headers, **kwargs):
        """
            Specifies whether to always send extra HTTP headers with the requests from this page.
        Params:
            1. headers: Headers
                Map with extra HTTP headers.
        """
        return self.drv.call(None,'Network.setExtraHTTPHeaders',headers=headers, **kwargs)


    # func: setRequestInterception
    def setRequestInterception(self,patterns:List[RequestPattern], **kwargs):
        """
            Sets the requests to intercept that match the provided patterns and optionally resource types.
            Deprecated, please use Fetch.enable instead.
        Params:
            1. patterns: List[RequestPattern]
                Requests matching any of these patterns will be forwarded and wait for the correspondingcontinueInterceptedRequest call.
        """
        return self.drv.call(None,'Network.setRequestInterception',patterns=patterns, **kwargs)


    # func: setUserAgentOverride
    def setUserAgentOverride(self,userAgent:str, acceptLanguage:str=None, platform:str=None, userAgentMetadata:Emulation.UserAgentMetadata=None, **kwargs):
        """
            Allows overriding user agent with the given string.
        Params:
            1. userAgent: str
                User agent to use.
            2. acceptLanguage: str (OPTIONAL)
                Browser langugage to emulate.
            3. platform: str (OPTIONAL)
                The platform navigator.platform should return.
            4. userAgentMetadata: Emulation.UserAgentMetadata (OPTIONAL)
                To be sent in Sec-CH-UA-* headers and returned in navigator.userAgentData
        """
        return self.drv.call(None,'Network.setUserAgentOverride',userAgent=userAgent, acceptLanguage=acceptLanguage, platform=platform, userAgentMetadata=userAgentMetadata, **kwargs)


    # return: getSecurityIsolationStatusReturn
    class getSecurityIsolationStatusReturn(ReturnT):
        def __init__(self):
            # status
            self.status: SecurityIsolationStatus = SecurityIsolationStatus


    # func: getSecurityIsolationStatus
    def getSecurityIsolationStatus(self,frameId:Page.FrameId=None, **kwargs) -> getSecurityIsolationStatusReturn:
        """
            Returns information about the COEP/COOP isolation status.
        Params:
            1. frameId: Page.FrameId (OPTIONAL)
                If no frameId is provided, the status of the target is provided.
        Return: getSecurityIsolationStatusReturn
        """
        return self.drv.call(Network.getSecurityIsolationStatusReturn,'Network.getSecurityIsolationStatus',frameId=frameId, **kwargs)



