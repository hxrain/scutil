"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# --------------------------------------------------------------------------------
# Security Domain Typing.
# --------------------------------------------------------------------------------
# typing: An internal certificate ID value.
CertificateId = int


# typing: A description of mixed content (HTTP resources on HTTPS pages), as defined byhttps://www.w3.org/TR/mixed-content/#categories
MixedContentType = str
MixedContentTypeEnums = ['blockable', 'optionally-blockable', 'none']


# typing: The security level of a page or resource.
SecurityState = str
SecurityStateEnums = ['unknown', 'neutral', 'insecure', 'secure', 'info', 'insecure-broken']


# object: CertificateSecurityState
class CertificateSecurityState(TypingT):
    """
        Details about the security state of the page certificate.
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
        # Page certificate.
        self.certificate: List[str] = [str]
        # Certificate subject name.
        self.subjectName: str = str
        # Name of the issuing CA.
        self.issuer: str = str
        # Certificate valid from date.
        self.validFrom: Network.TimeSinceEpoch = Network.TimeSinceEpoch
        # Certificate valid to (expiration) date
        self.validTo: Network.TimeSinceEpoch = Network.TimeSinceEpoch
        # OPTIONAL, The highest priority network error code, if the certificate has an error.
        self.certificateNetworkError: str = str
        # True if the certificate uses a weak signature aglorithm.
        self.certificateHasWeakSignature: bool = bool
        # True if the certificate has a SHA1 signature in the chain.
        self.certificateHasSha1Signature: bool = bool
        # True if modern SSL
        self.modernSSL: bool = bool
        # True if the connection is using an obsolete SSL protocol.
        self.obsoleteSslProtocol: bool = bool
        # True if the connection is using an obsolete SSL key exchange.
        self.obsoleteSslKeyExchange: bool = bool
        # True if the connection is using an obsolete SSL cipher.
        self.obsoleteSslCipher: bool = bool
        # True if the connection is using an obsolete SSL signature.
        self.obsoleteSslSignature: bool = bool


# typing: SafetyTipStatus
SafetyTipStatus = str
SafetyTipStatusEnums = ['badReputation', 'lookalike']


# object: SafetyTipInfo
class SafetyTipInfo(TypingT):
    """
        SafetyTipInfo
    """
    def __init__(self):
        # Describes whether the page triggers any safety tips or reputation warnings. Default is unknown.
        self.safetyTipStatus: SafetyTipStatus = SafetyTipStatus
        # OPTIONAL, The URL the safety tip suggested ("Did you mean?"). Only filled in for lookalike matches.
        self.safeUrl: str = str


# object: VisibleSecurityState
class VisibleSecurityState(TypingT):
    """
        Security state information about the page.
    """
    def __init__(self):
        # The security level of the page.
        self.securityState: SecurityState = SecurityState
        # OPTIONAL, Security state details about the page certificate.
        self.certificateSecurityState: CertificateSecurityState = CertificateSecurityState
        # OPTIONAL, The type of Safety Tip triggered on the page. Note that this field will be set even if the Safety Tip UI was not actually shown.
        self.safetyTipInfo: SafetyTipInfo = SafetyTipInfo
        # Array of security state issues ids.
        self.securityStateIssueIds: List[str] = [str]


# object: SecurityStateExplanation
class SecurityStateExplanation(TypingT):
    """
        An explanation of an factor contributing to the security state.
    """
    def __init__(self):
        # Security state representing the severity of the factor being explained.
        self.securityState: SecurityState = SecurityState
        # Title describing the type of factor.
        self.title: str = str
        # Short phrase describing the type of factor.
        self.summary: str = str
        # Full text explanation of the factor.
        self.description: str = str
        # The type of mixed content described by the explanation.
        self.mixedContentType: MixedContentType = MixedContentType
        # Page certificate.
        self.certificate: List[str] = [str]
        # OPTIONAL, Recommendations to fix any issues.
        self.recommendations: List[str] = [str]


# object: InsecureContentStatus
class InsecureContentStatus(TypingT):
    """
        Information about insecure content on the page.
    """
    def __init__(self):
        # Always false.
        self.ranMixedContent: bool = bool
        # Always false.
        self.displayedMixedContent: bool = bool
        # Always false.
        self.containedMixedForm: bool = bool
        # Always false.
        self.ranContentWithCertErrors: bool = bool
        # Always false.
        self.displayedContentWithCertErrors: bool = bool
        # Always set to unknown.
        self.ranInsecureContentStyle: SecurityState = SecurityState
        # Always set to unknown.
        self.displayedInsecureContentStyle: SecurityState = SecurityState


# typing: The action to take when a certificate error occurs. continue will continue processing therequest and cancel will cancel the request.
CertificateErrorAction = str
CertificateErrorActionEnums = ['continue', 'cancel']


# --------------------------------------------------------------------------------
# Security Domain Event.
# --------------------------------------------------------------------------------
# event: certificateError
class certificateError(EventT):
    """
        There is a certificate error. If overriding certificate errors is enabled, then it should be
        handled with the `handleCertificateError` command. Note: this event does not fire if the
        certificate error has been allowed internally. Only one client per target should override
        certificate errors at the same time.
    """
    event="Security.certificateError"
    def __init__(self):
        # The ID of the event.
        self.eventId: int = int
        # The type of the error.
        self.errorType: str = str
        # The url that was requested.
        self.requestURL: str = str


# event: visibleSecurityStateChanged
class visibleSecurityStateChanged(EventT):
    """
        The security state of the page changed.
    """
    event="Security.visibleSecurityStateChanged"
    def __init__(self):
        # Security state information about the page.
        self.visibleSecurityState: VisibleSecurityState = VisibleSecurityState


# event: securityStateChanged
class securityStateChanged(EventT):
    """
        The security state of the page changed.
    """
    event="Security.securityStateChanged"
    def __init__(self):
        # Security state.
        self.securityState: SecurityState = SecurityState
        # True if the page was loaded over cryptographic transport such as HTTPS.
        self.schemeIsCryptographic: bool = bool
        # List of explanations for the security state. If the overall security state is `insecure` or`warning`, at least one corresponding explanation should be included.
        self.explanations: List[SecurityStateExplanation] = [SecurityStateExplanation]
        # Information about insecure content on the page.
        self.insecureContentStatus: InsecureContentStatus = InsecureContentStatus
        # OPTIONAL, Overrides user-visible description of the state.
        self.summary: str = str


# ================================================================================
# Security Domain Class.
# ================================================================================
class Security(DomainT):
    """
        Security
    """
    def __init__(self, drv):
        self.drv = drv


    # func: disable
    def disable(self,**kwargs):
        """
            Disables tracking security state changes.
        """
        return self.drv.call(None,'Security.disable',**kwargs)


    # func: enable
    def enable(self,**kwargs):
        """
            Enables tracking security state changes.
        """
        return self.drv.call(None,'Security.enable',**kwargs)


    # func: setIgnoreCertificateErrors
    def setIgnoreCertificateErrors(self,ignore:bool, **kwargs):
        """
            Enable/disable whether all certificate errors should be ignored.
        Params:
            1. ignore: bool
                If true, all certificate errors will be ignored.
        """
        return self.drv.call(None,'Security.setIgnoreCertificateErrors',ignore=ignore, **kwargs)


    # func: handleCertificateError
    def handleCertificateError(self,eventId:int, action:CertificateErrorAction, **kwargs):
        """
            Handles a certificate error that fired a certificateError event.
        Params:
            1. eventId: int
                The ID of the event.
            2. action: CertificateErrorAction
                The action to take on the certificate error.
        """
        return self.drv.call(None,'Security.handleCertificateError',eventId=eventId, action=action, **kwargs)


    # func: setOverrideCertificateErrors
    def setOverrideCertificateErrors(self,override:bool, **kwargs):
        """
            Enable/disable overriding certificate errors. If enabled, all certificate error events need to
            be handled by the DevTools client and should be answered with `handleCertificateError` commands.
        Params:
            1. override: bool
                If true, certificate errors will be overridden.
        """
        return self.drv.call(None,'Security.setOverrideCertificateErrors',override=override, **kwargs)



