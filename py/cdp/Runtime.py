"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: Unique script identifier.
ScriptId = str


# typing: Unique object identifier.
RemoteObjectId = str


# typing: Primitive value which cannot be JSON-stringified. Includes values `-0`, `NaN`, `Infinity`,`-Infinity`, and bigint literals.
UnserializableValue = str


# object: RemoteObject
class RemoteObject(TypingT):
    """
        Mirror object referencing original JavaScript object.
    """
    def __init__(self):
        # Object type.
        self.type: str = str
        # OPTIONAL, Object subtype hint. Specified for `object` or `wasm` type values only.
        self.subtype: str = str
        # OPTIONAL, Object class (constructor) name. Specified for `object` type values only.
        self.className: str = str
        # OPTIONAL, Remote object value in case of primitive values or JSON values (if it was requested).
        self.value: str = str
        # OPTIONAL, Primitive value which can not be JSON-stringified does not have `value`, but gets thisproperty.
        self.unserializableValue: UnserializableValue = UnserializableValue
        # OPTIONAL, String representation of the object.
        self.description: str = str
        # OPTIONAL, Unique object identifier (for non-primitive values).
        self.objectId: RemoteObjectId = RemoteObjectId
        # OPTIONAL, Preview containing abbreviated property values. Specified for `object` type values only.
        self.preview: ObjectPreview = ObjectPreview
        # OPTIONAL, customPreview
        self.customPreview: CustomPreview = CustomPreview


# object: CustomPreview
class CustomPreview(TypingT):
    """
        CustomPreview
    """
    def __init__(self):
        # The JSON-stringified result of formatter.header(object, config) call.It contains json ML array that represents RemoteObject.
        self.header: str = str
        # OPTIONAL, If formatter returns true as a result of formatter.hasBody call then bodyGetterId willcontain RemoteObjectId for the function that returns result of formatter.body(object, config) call.The result value is json ML array.
        self.bodyGetterId: RemoteObjectId = RemoteObjectId


# object: ObjectPreview
class ObjectPreview(TypingT):
    """
        Object containing abbreviated remote object value.
    """
    def __init__(self):
        # Object type.
        self.type: str = str
        # OPTIONAL, Object subtype hint. Specified for `object` type values only.
        self.subtype: str = str
        # OPTIONAL, String representation of the object.
        self.description: str = str
        # True iff some of the properties or entries of the original object did not fit.
        self.overflow: bool = bool
        # List of the properties.
        self.properties: List[PropertyPreview] = [PropertyPreview]
        # OPTIONAL, List of the entries. Specified for `map` and `set` subtype values only.
        self.entries: List[EntryPreview] = [EntryPreview]


# object: PropertyPreview
class PropertyPreview(TypingT):
    """
        PropertyPreview
    """
    def __init__(self):
        # Property name.
        self.name: str = str
        # Object type. Accessor means that the property itself is an accessor property.
        self.type: str = str
        # OPTIONAL, User-friendly property value string.
        self.value: str = str
        # OPTIONAL, Nested value preview.
        self.valuePreview: ObjectPreview = ObjectPreview
        # OPTIONAL, Object subtype hint. Specified for `object` type values only.
        self.subtype: str = str


# object: EntryPreview
class EntryPreview(TypingT):
    """
        EntryPreview
    """
    def __init__(self):
        # OPTIONAL, Preview of the key. Specified for map-like collection entries.
        self.key: ObjectPreview = ObjectPreview
        # Preview of the value.
        self.value: ObjectPreview = ObjectPreview


# object: PropertyDescriptor
class PropertyDescriptor(TypingT):
    """
        Object property descriptor.
    """
    def __init__(self):
        # Property name or symbol description.
        self.name: str = str
        # OPTIONAL, The value associated with the property.
        self.value: RemoteObject = RemoteObject
        # OPTIONAL, True if the value associated with the property may be changed (data descriptors only).
        self.writable: bool = bool
        # OPTIONAL, A function which serves as a getter for the property, or `undefined` if there is no getter(accessor descriptors only).
        self.get: RemoteObject = RemoteObject
        # OPTIONAL, A function which serves as a setter for the property, or `undefined` if there is no setter(accessor descriptors only).
        self.set: RemoteObject = RemoteObject
        # True if the type of this property descriptor may be changed and if the property may bedeleted from the corresponding object.
        self.configurable: bool = bool
        # True if this property shows up during enumeration of the properties on the correspondingobject.
        self.enumerable: bool = bool
        # OPTIONAL, True if the result was thrown during the evaluation.
        self.wasThrown: bool = bool
        # OPTIONAL, True if the property is owned for the object.
        self.isOwn: bool = bool
        # OPTIONAL, Property symbol object, if the property is of the `symbol` type.
        self.symbol: RemoteObject = RemoteObject


# object: InternalPropertyDescriptor
class InternalPropertyDescriptor(TypingT):
    """
        Object internal property descriptor. This property isn't normally visible in JavaScript code.
    """
    def __init__(self):
        # Conventional property name.
        self.name: str = str
        # OPTIONAL, The value associated with the property.
        self.value: RemoteObject = RemoteObject


# object: PrivatePropertyDescriptor
class PrivatePropertyDescriptor(TypingT):
    """
        Object private field descriptor.
    """
    def __init__(self):
        # Private property name.
        self.name: str = str
        # OPTIONAL, The value associated with the private property.
        self.value: RemoteObject = RemoteObject
        # OPTIONAL, A function which serves as a getter for the private property,or `undefined` if there is no getter (accessor descriptors only).
        self.get: RemoteObject = RemoteObject
        # OPTIONAL, A function which serves as a setter for the private property,or `undefined` if there is no setter (accessor descriptors only).
        self.set: RemoteObject = RemoteObject


# object: CallArgument
class CallArgument(TypingT):
    """
        Represents function call argument. Either remote object id `objectId`, primitive `value`,
        unserializable primitive value or neither of (for undefined) them should be specified.
    """
    def __init__(self):
        # OPTIONAL, Primitive value or serializable javascript object.
        self.value: str = str
        # OPTIONAL, Primitive value which can not be JSON-stringified.
        self.unserializableValue: UnserializableValue = UnserializableValue
        # OPTIONAL, Remote object handle.
        self.objectId: RemoteObjectId = RemoteObjectId


# typing: Id of an execution context.
ExecutionContextId = int


# object: ExecutionContextDescription
class ExecutionContextDescription(TypingT):
    """
        Description of an isolated world.
    """
    def __init__(self):
        # Unique id of the execution context. It can be used to specify in which execution contextscript evaluation should be performed.
        self.id: ExecutionContextId = ExecutionContextId
        # Execution context origin.
        self.origin: str = str
        # Human readable name describing given context.
        self.name: str = str
        # OPTIONAL, Embedder-specific auxiliary data.
        self.auxData: str = str


# object: ExceptionDetails
class ExceptionDetails(TypingT):
    """
        Detailed information about exception (or error) that was thrown during script compilation or
        execution.
    """
    def __init__(self):
        # Exception id.
        self.exceptionId: int = int
        # Exception text, which should be used together with exception object when available.
        self.text: str = str
        # Line number of the exception location (0-based).
        self.lineNumber: int = int
        # Column number of the exception location (0-based).
        self.columnNumber: int = int
        # OPTIONAL, Script ID of the exception location.
        self.scriptId: ScriptId = ScriptId
        # OPTIONAL, URL of the exception location, to be used when the script was not reported.
        self.url: str = str
        # OPTIONAL, JavaScript stack trace if available.
        self.stackTrace: StackTrace = StackTrace
        # OPTIONAL, Exception object if available.
        self.exception: RemoteObject = RemoteObject
        # OPTIONAL, Identifier of the context where exception happened.
        self.executionContextId: ExecutionContextId = ExecutionContextId


# typing: Number of milliseconds since epoch.
Timestamp = int


# typing: Number of milliseconds.
TimeDelta = int


# object: CallFrame
class CallFrame(TypingT):
    """
        Stack entry for runtime errors and assertions.
    """
    def __init__(self):
        # JavaScript function name.
        self.functionName: str = str
        # JavaScript script id.
        self.scriptId: ScriptId = ScriptId
        # JavaScript script name or url.
        self.url: str = str
        # JavaScript script line number (0-based).
        self.lineNumber: int = int
        # JavaScript script column number (0-based).
        self.columnNumber: int = int


# object: StackTrace
class StackTrace(TypingT):
    """
        Call frames for assertions or error messages.
    """
    def __init__(self):
        # OPTIONAL, String label of this stack trace. For async traces this may be a name of the function thatinitiated the async call.
        self.description: str = str
        # JavaScript function name.
        self.callFrames: List[CallFrame] = [CallFrame]
        # OPTIONAL, Asynchronous JavaScript stack trace that preceded this stack, if available.
        self.parent: StackTrace = StackTrace
        # OPTIONAL, Asynchronous JavaScript stack trace that preceded this stack, if available.
        self.parentId: StackTraceId = StackTraceId


# typing: Unique identifier of current debugger.
UniqueDebuggerId = str


# object: StackTraceId
class StackTraceId(TypingT):
    """
        If `debuggerId` is set stack trace comes from another debugger and can be resolved there. This
        allows to track cross-debugger calls. See `Runtime.StackTrace` and `Debugger.paused` for usages.
    """
    def __init__(self):
        # id
        self.id: str = str
        # OPTIONAL, debuggerId
        self.debuggerId: UniqueDebuggerId = UniqueDebuggerId


# event: consoleAPICalled
class consoleAPICalled(EventT):
    """
        Issued when console API was called.
    """
    event="Runtime.consoleAPICalled"
    def __init__(self):
        typeEnums = ['log', 'debug', 'info', 'error', 'warning', 'dir', 'dirxml', 'table', 'trace', 'clear', 'startGroup', 'startGroupCollapsed', 'endGroup', 'assert', 'profile', 'profileEnd', 'count', 'timeEnd']
        # Type of the call.
        self.type: str = str
        # Call arguments.
        self.args: List[RemoteObject] = [RemoteObject]
        # Identifier of the context where the call was made.
        self.executionContextId: ExecutionContextId = ExecutionContextId
        # Call timestamp.
        self.timestamp: Timestamp = Timestamp
        # OPTIONAL, Stack trace captured when the call was made. The async stack chain is automatically reported forthe following call types: `assert`, `error`, `trace`, `warning`. For other types the async callchain can be retrieved using `Debugger.getStackTrace` and `stackTrace.parentId` field.
        self.stackTrace: StackTrace = StackTrace
        # OPTIONAL, Console context descriptor for calls on non-default console context (not console.*):'anonymous#unique-logger-id' for call on unnamed context, 'name#unique-logger-id' for callon named context.
        self.context: str = str


# event: exceptionRevoked
class exceptionRevoked(EventT):
    """
        Issued when unhandled exception was revoked.
    """
    event="Runtime.exceptionRevoked"
    def __init__(self):
        # Reason describing why exception was revoked.
        self.reason: str = str
        # The id of revoked exception, as reported in `exceptionThrown`.
        self.exceptionId: int = int


# event: exceptionThrown
class exceptionThrown(EventT):
    """
        Issued when exception was thrown and unhandled.
    """
    event="Runtime.exceptionThrown"
    def __init__(self):
        # Timestamp of the exception.
        self.timestamp: Timestamp = Timestamp
        # exceptionDetails
        self.exceptionDetails: ExceptionDetails = ExceptionDetails


# event: executionContextCreated
class executionContextCreated(EventT):
    """
        Issued when new execution context is created.
    """
    event="Runtime.executionContextCreated"
    def __init__(self):
        # A newly created execution context.
        self.context: ExecutionContextDescription = ExecutionContextDescription


# event: executionContextDestroyed
class executionContextDestroyed(EventT):
    """
        Issued when execution context is destroyed.
    """
    event="Runtime.executionContextDestroyed"
    def __init__(self):
        # Id of the destroyed context
        self.executionContextId: ExecutionContextId = ExecutionContextId


# event: executionContextsCleared
class executionContextsCleared(EventT):
    """
        Issued when all executionContexts were cleared in browser
    """
    event="Runtime.executionContextsCleared"
    def __init__(self):
        pass


# event: inspectRequested
class inspectRequested(EventT):
    """
        Issued when object should be inspected (for example, as a result of inspect() command line API
        call).
    """
    event="Runtime.inspectRequested"
    def __init__(self):
        # object
        self.object: RemoteObject = RemoteObject
        # hints
        self.hints: str = str


# ================================================================================
# Runtime Domain.
# ================================================================================
class Runtime(DomainT):
    """
        Runtime domain exposes JavaScript runtime by means of remote evaluation and mirror objects.
        Evaluation results are returned as mirror object that expose object type, string representation
        and unique identifier that can be used for further object reference. Original objects are
        maintained in memory unless they are either explicitly released or are released along with the
        other objects in their object group.
    """
    def __init__(self, drv):
        self.drv = drv


    # return: awaitPromiseReturn
    class awaitPromiseReturn(ReturnT):
        def __init__(self):
            # Promise result. Will contain rejected value if promise was rejected.
            self.result: RemoteObject = RemoteObject
            # OPTIONAL, Exception details if stack strace is available.
            self.exceptionDetails: ExceptionDetails = ExceptionDetails


    # func: awaitPromise
    def awaitPromise(self,promiseObjectId:RemoteObjectId, returnByValue:bool=None, generatePreview:bool=None, **kwargs) -> awaitPromiseReturn:
        """
            Add handler to promise with given promise object id.
        Params:
            1. promiseObjectId: RemoteObjectId
                Identifier of the promise.
            2. returnByValue: bool (OPTIONAL)
                Whether the result is expected to be a JSON object that should be sent by value.
            3. generatePreview: bool (OPTIONAL)
                Whether preview should be generated for the result.
        Return: awaitPromiseReturn
        """
        return self.drv.call(Runtime.awaitPromiseReturn,'Runtime.awaitPromise',promiseObjectId=promiseObjectId, returnByValue=returnByValue, generatePreview=generatePreview, **kwargs)


    # return: callFunctionOnReturn
    class callFunctionOnReturn(ReturnT):
        def __init__(self):
            # Call result.
            self.result: RemoteObject = RemoteObject
            # OPTIONAL, Exception details.
            self.exceptionDetails: ExceptionDetails = ExceptionDetails


    # func: callFunctionOn
    def callFunctionOn(self,functionDeclaration:str, objectId:RemoteObjectId=None, arguments:List[CallArgument]=None, silent:bool=None, returnByValue:bool=None, generatePreview:bool=None, userGesture:bool=None, awaitPromise:bool=None, executionContextId:ExecutionContextId=None, objectGroup:str=None, **kwargs) -> callFunctionOnReturn:
        """
            Calls function with given declaration on the given object. Object group of the result is
            inherited from the target object.
        Params:
            1. functionDeclaration: str
                Declaration of the function to call.
            2. objectId: RemoteObjectId (OPTIONAL)
                Identifier of the object to call function on. Either objectId or executionContextId shouldbe specified.
            3. arguments: List[CallArgument] (OPTIONAL)
                Call arguments. All call arguments must belong to the same JavaScript world as the targetobject.
            4. silent: bool (OPTIONAL)
                In silent mode exceptions thrown during evaluation are not reported and do not pauseexecution. Overrides `setPauseOnException` state.
            5. returnByValue: bool (OPTIONAL)
                Whether the result is expected to be a JSON object which should be sent by value.
            6. generatePreview: bool (OPTIONAL)
                Whether preview should be generated for the result.
            7. userGesture: bool (OPTIONAL)
                Whether execution should be treated as initiated by user in the UI.
            8. awaitPromise: bool (OPTIONAL)
                Whether execution should `await` for resulting value and return once awaited promise isresolved.
            9. executionContextId: ExecutionContextId (OPTIONAL)
                Specifies execution context which global object will be used to call function on. EitherexecutionContextId or objectId should be specified.
            10. objectGroup: str (OPTIONAL)
                Symbolic group name that can be used to release multiple objects. If objectGroup is notspecified and objectId is, objectGroup will be inherited from object.
        Return: callFunctionOnReturn
        """
        return self.drv.call(Runtime.callFunctionOnReturn,'Runtime.callFunctionOn',functionDeclaration=functionDeclaration, objectId=objectId, arguments=arguments, silent=silent, returnByValue=returnByValue, generatePreview=generatePreview, userGesture=userGesture, awaitPromise=awaitPromise, executionContextId=executionContextId, objectGroup=objectGroup, **kwargs)


    # return: compileScriptReturn
    class compileScriptReturn(ReturnT):
        def __init__(self):
            # OPTIONAL, Id of the script.
            self.scriptId: ScriptId = ScriptId
            # OPTIONAL, Exception details.
            self.exceptionDetails: ExceptionDetails = ExceptionDetails


    # func: compileScript
    def compileScript(self,expression:str, sourceURL:str, persistScript:bool, executionContextId:ExecutionContextId=None, **kwargs) -> compileScriptReturn:
        """
            Compiles expression.
        Params:
            1. expression: str
                Expression to compile.
            2. sourceURL: str
                Source url to be set for the script.
            3. persistScript: bool
                Specifies whether the compiled script should be persisted.
            4. executionContextId: ExecutionContextId (OPTIONAL)
                Specifies in which execution context to perform script run. If the parameter is omitted theevaluation will be performed in the context of the inspected page.
        Return: compileScriptReturn
        """
        return self.drv.call(Runtime.compileScriptReturn,'Runtime.compileScript',expression=expression, sourceURL=sourceURL, persistScript=persistScript, executionContextId=executionContextId, **kwargs)


    # func: disable
    def disable(self,**kwargs):
        """
            Disables reporting of execution contexts creation.
        """
        return self.drv.call(None,'Runtime.disable',**kwargs)


    # func: discardConsoleEntries
    def discardConsoleEntries(self,**kwargs):
        """
            Discards collected exceptions and console API calls.
        """
        return self.drv.call(None,'Runtime.discardConsoleEntries',**kwargs)


    # func: enable
    def enable(self,**kwargs):
        """
            Enables reporting of execution contexts creation by means of `executionContextCreated` event.
            When the reporting gets enabled the event will be sent immediately for each existing execution
            context.
        """
        return self.drv.call(None,'Runtime.enable',**kwargs)


    # return: evaluateReturn
    class evaluateReturn(ReturnT):
        def __init__(self):
            # Evaluation result.
            self.result: RemoteObject = RemoteObject
            # OPTIONAL, Exception details.
            self.exceptionDetails: ExceptionDetails = ExceptionDetails


    # func: evaluate
    def evaluate(self,expression:str, objectGroup:str=None, includeCommandLineAPI:bool=None, silent:bool=None, contextId:ExecutionContextId=None, returnByValue:bool=None, generatePreview:bool=None, userGesture:bool=None, awaitPromise:bool=None, throwOnSideEffect:bool=None, timeout:TimeDelta=None, disableBreaks:bool=None, replMode:bool=None, allowUnsafeEvalBlockedByCSP:bool=None, **kwargs) -> evaluateReturn:
        """
            Evaluates expression on global object.
        Params:
            1. expression: str
                Expression to evaluate.
            2. objectGroup: str (OPTIONAL)
                Symbolic group name that can be used to release multiple objects.
            3. includeCommandLineAPI: bool (OPTIONAL)
                Determines whether Command Line API should be available during the evaluation.
            4. silent: bool (OPTIONAL)
                In silent mode exceptions thrown during evaluation are not reported and do not pauseexecution. Overrides `setPauseOnException` state.
            5. contextId: ExecutionContextId (OPTIONAL)
                Specifies in which execution context to perform evaluation. If the parameter is omitted theevaluation will be performed in the context of the inspected page.
            6. returnByValue: bool (OPTIONAL)
                Whether the result is expected to be a JSON object that should be sent by value.
            7. generatePreview: bool (OPTIONAL)
                Whether preview should be generated for the result.
            8. userGesture: bool (OPTIONAL)
                Whether execution should be treated as initiated by user in the UI.
            9. awaitPromise: bool (OPTIONAL)
                Whether execution should `await` for resulting value and return once awaited promise isresolved.
            10. throwOnSideEffect: bool (OPTIONAL)
                Whether to throw an exception if side effect cannot be ruled out during evaluation.This implies `disableBreaks` below.
            11. timeout: TimeDelta (OPTIONAL)
                Terminate execution after timing out (number of milliseconds).
            12. disableBreaks: bool (OPTIONAL)
                Disable breakpoints during execution.
            13. replMode: bool (OPTIONAL)
                Setting this flag to true enables `let` re-declaration and top-level `await`.Note that `let` variables can only be re-declared if they originate from`replMode` themselves.
            14. allowUnsafeEvalBlockedByCSP: bool (OPTIONAL)
                The Content Security Policy (CSP) for the target might block 'unsafe-eval'which includes eval(), Function(), setTimeout() and setInterval()when called with non-callable arguments. This flag bypasses CSP for thisevaluation and allows unsafe-eval. Defaults to true.
        Return: evaluateReturn
        """
        return self.drv.call(Runtime.evaluateReturn,'Runtime.evaluate',expression=expression, objectGroup=objectGroup, includeCommandLineAPI=includeCommandLineAPI, silent=silent, contextId=contextId, returnByValue=returnByValue, generatePreview=generatePreview, userGesture=userGesture, awaitPromise=awaitPromise, throwOnSideEffect=throwOnSideEffect, timeout=timeout, disableBreaks=disableBreaks, replMode=replMode, allowUnsafeEvalBlockedByCSP=allowUnsafeEvalBlockedByCSP, **kwargs)


    # return: getIsolateIdReturn
    class getIsolateIdReturn(ReturnT):
        def __init__(self):
            # The isolate id.
            self.id: str = str


    # func: getIsolateId
    def getIsolateId(self,**kwargs) -> getIsolateIdReturn:
        """
            Returns the isolate id.
        Return: getIsolateIdReturn
        """
        return self.drv.call(Runtime.getIsolateIdReturn,'Runtime.getIsolateId',**kwargs)


    # return: getHeapUsageReturn
    class getHeapUsageReturn(ReturnT):
        def __init__(self):
            # Used heap size in bytes.
            self.usedSize: int = int
            # Allocated heap size in bytes.
            self.totalSize: int = int


    # func: getHeapUsage
    def getHeapUsage(self,**kwargs) -> getHeapUsageReturn:
        """
            Returns the JavaScript heap usage.
            It is the total usage of the corresponding isolate not scoped to a particular Runtime.
        Return: getHeapUsageReturn
        """
        return self.drv.call(Runtime.getHeapUsageReturn,'Runtime.getHeapUsage',**kwargs)


    # return: getPropertiesReturn
    class getPropertiesReturn(ReturnT):
        def __init__(self):
            # Object properties.
            self.result: List[PropertyDescriptor] = [PropertyDescriptor]
            # OPTIONAL, Internal object properties (only of the element itself).
            self.internalProperties: List[InternalPropertyDescriptor] = [InternalPropertyDescriptor]
            # OPTIONAL, Object private properties.
            self.privateProperties: List[PrivatePropertyDescriptor] = [PrivatePropertyDescriptor]
            # OPTIONAL, Exception details.
            self.exceptionDetails: ExceptionDetails = ExceptionDetails


    # func: getProperties
    def getProperties(self,objectId:RemoteObjectId, ownProperties:bool=None, accessorPropertiesOnly:bool=None, generatePreview:bool=None, **kwargs) -> getPropertiesReturn:
        """
            Returns properties of a given object. Object group of the result is inherited from the target
            object.
        Params:
            1. objectId: RemoteObjectId
                Identifier of the object to return properties for.
            2. ownProperties: bool (OPTIONAL)
                If true, returns properties belonging only to the element itself, not to its prototypechain.
            3. accessorPropertiesOnly: bool (OPTIONAL)
                If true, returns accessor properties (with getter/setter) only; internal properties are notreturned either.
            4. generatePreview: bool (OPTIONAL)
                Whether preview should be generated for the results.
        Return: getPropertiesReturn
        """
        return self.drv.call(Runtime.getPropertiesReturn,'Runtime.getProperties',objectId=objectId, ownProperties=ownProperties, accessorPropertiesOnly=accessorPropertiesOnly, generatePreview=generatePreview, **kwargs)


    # return: globalLexicalScopeNamesReturn
    class globalLexicalScopeNamesReturn(ReturnT):
        def __init__(self):
            # names
            self.names: List[str] = [str]


    # func: globalLexicalScopeNames
    def globalLexicalScopeNames(self,executionContextId:ExecutionContextId=None, **kwargs) -> globalLexicalScopeNamesReturn:
        """
            Returns all let, const and class variables from global scope.
        Params:
            1. executionContextId: ExecutionContextId (OPTIONAL)
                Specifies in which execution context to lookup global scope variables.
        Return: globalLexicalScopeNamesReturn
        """
        return self.drv.call(Runtime.globalLexicalScopeNamesReturn,'Runtime.globalLexicalScopeNames',executionContextId=executionContextId, **kwargs)


    # return: queryObjectsReturn
    class queryObjectsReturn(ReturnT):
        def __init__(self):
            # Array with objects.
            self.objects: RemoteObject = RemoteObject


    # func: queryObjects
    def queryObjects(self,prototypeObjectId:RemoteObjectId, objectGroup:str=None, **kwargs) -> queryObjectsReturn:
        """
        Params:
            1. prototypeObjectId: RemoteObjectId
                Identifier of the prototype to return objects for.
            2. objectGroup: str (OPTIONAL)
                Symbolic group name that can be used to release the results.
        Return: queryObjectsReturn
        """
        return self.drv.call(Runtime.queryObjectsReturn,'Runtime.queryObjects',prototypeObjectId=prototypeObjectId, objectGroup=objectGroup, **kwargs)


    # func: releaseObject
    def releaseObject(self,objectId:RemoteObjectId, **kwargs):
        """
            Releases remote object with given id.
        Params:
            1. objectId: RemoteObjectId
                Identifier of the object to release.
        """
        return self.drv.call(None,'Runtime.releaseObject',objectId=objectId, **kwargs)


    # func: releaseObjectGroup
    def releaseObjectGroup(self,objectGroup:str, **kwargs):
        """
            Releases all remote objects that belong to a given group.
        Params:
            1. objectGroup: str
                Symbolic object group name.
        """
        return self.drv.call(None,'Runtime.releaseObjectGroup',objectGroup=objectGroup, **kwargs)


    # func: runIfWaitingForDebugger
    def runIfWaitingForDebugger(self,**kwargs):
        """
            Tells inspected instance to run if it was waiting for debugger to attach.
        """
        return self.drv.call(None,'Runtime.runIfWaitingForDebugger',**kwargs)


    # return: runScriptReturn
    class runScriptReturn(ReturnT):
        def __init__(self):
            # Run result.
            self.result: RemoteObject = RemoteObject
            # OPTIONAL, Exception details.
            self.exceptionDetails: ExceptionDetails = ExceptionDetails


    # func: runScript
    def runScript(self,scriptId:ScriptId, executionContextId:ExecutionContextId=None, objectGroup:str=None, silent:bool=None, includeCommandLineAPI:bool=None, returnByValue:bool=None, generatePreview:bool=None, awaitPromise:bool=None, **kwargs) -> runScriptReturn:
        """
            Runs script with given id in a given context.
        Params:
            1. scriptId: ScriptId
                Id of the script to run.
            2. executionContextId: ExecutionContextId (OPTIONAL)
                Specifies in which execution context to perform script run. If the parameter is omitted theevaluation will be performed in the context of the inspected page.
            3. objectGroup: str (OPTIONAL)
                Symbolic group name that can be used to release multiple objects.
            4. silent: bool (OPTIONAL)
                In silent mode exceptions thrown during evaluation are not reported and do not pauseexecution. Overrides `setPauseOnException` state.
            5. includeCommandLineAPI: bool (OPTIONAL)
                Determines whether Command Line API should be available during the evaluation.
            6. returnByValue: bool (OPTIONAL)
                Whether the result is expected to be a JSON object which should be sent by value.
            7. generatePreview: bool (OPTIONAL)
                Whether preview should be generated for the result.
            8. awaitPromise: bool (OPTIONAL)
                Whether execution should `await` for resulting value and return once awaited promise isresolved.
        Return: runScriptReturn
        """
        return self.drv.call(Runtime.runScriptReturn,'Runtime.runScript',scriptId=scriptId, executionContextId=executionContextId, objectGroup=objectGroup, silent=silent, includeCommandLineAPI=includeCommandLineAPI, returnByValue=returnByValue, generatePreview=generatePreview, awaitPromise=awaitPromise, **kwargs)


    # func: setAsyncCallStackDepth
    def setAsyncCallStackDepth(self,maxDepth:int, **kwargs):
        """
            Enables or disables async call stacks tracking.
        Params:
            1. maxDepth: int
                Maximum depth of async call stacks. Setting to `0` will effectively disable collecting asynccall stacks (default).
        """
        return self.drv.call(None,'Runtime.setAsyncCallStackDepth',maxDepth=maxDepth, **kwargs)


    # func: setCustomObjectFormatterEnabled
    def setCustomObjectFormatterEnabled(self,enabled:bool, **kwargs):
        """
        Params:
            1. enabled: bool
        """
        return self.drv.call(None,'Runtime.setCustomObjectFormatterEnabled',enabled=enabled, **kwargs)


    # func: setMaxCallStackSizeToCapture
    def setMaxCallStackSizeToCapture(self,size:int, **kwargs):
        """
        Params:
            1. size: int
        """
        return self.drv.call(None,'Runtime.setMaxCallStackSizeToCapture',size=size, **kwargs)


    # func: terminateExecution
    def terminateExecution(self,**kwargs):
        """
            Terminate current or next JavaScript execution.
            Will cancel the termination when the outer-most script execution ends.
        """
        return self.drv.call(None,'Runtime.terminateExecution',**kwargs)


    # func: addBinding
    def addBinding(self,name:str, executionContextId:ExecutionContextId=None, **kwargs):
        """
            If executionContextId is empty, adds binding with the given name on the
            global objects of all inspected contexts, including those created later,
            bindings survive reloads.
            If executionContextId is specified, adds binding only on global object of
            given execution context.
            Binding function takes exactly one argument, this argument should be string,
            in case of any other input, function throws an exception.
            Each binding function call produces Runtime.bindingCalled notification.
        Params:
            1. name: str
            2. executionContextId: ExecutionContextId (OPTIONAL)
        """
        return self.drv.call(None,'Runtime.addBinding',name=name, executionContextId=executionContextId, **kwargs)


    # func: removeBinding
    def removeBinding(self,name:str, **kwargs):
        """
            This method does not remove binding function from global object but
            unsubscribes current runtime agent from Runtime.bindingCalled notifications.
        Params:
            1. name: str
        """
        return self.drv.call(None,'Runtime.removeBinding',name=name, **kwargs)



