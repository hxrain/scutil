"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: Breakpoint identifier.
BreakpointId = str


# typing: Call frame identifier.
CallFrameId = str


# object: Location
class Location(TypingT):
    """
        Location in the source code.
    """
    def __init__(self):
        # Script identifier as reported in the `Debugger.scriptParsed`.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # Line number in the script (0-based).
        self.lineNumber: int = int
        # OPTIONAL, Column number in the script (0-based).
        self.columnNumber: int = int


# object: ScriptPosition
class ScriptPosition(TypingT):
    """
        Location in the source code.
    """
    def __init__(self):
        # lineNumber
        self.lineNumber: int = int
        # columnNumber
        self.columnNumber: int = int


# object: LocationRange
class LocationRange(TypingT):
    """
        Location range within one script.
    """
    def __init__(self):
        # scriptId
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # start
        self.start: ScriptPosition = ScriptPosition
        # end
        self.end: ScriptPosition = ScriptPosition


# object: CallFrame
class CallFrame(TypingT):
    """
        JavaScript call frame. Array of call frames form the call stack.
    """
    def __init__(self):
        # Call frame identifier. This identifier is only valid while the virtual machine is paused.
        self.callFrameId: CallFrameId = CallFrameId
        # Name of the JavaScript function called on this call frame.
        self.functionName: str = str
        # OPTIONAL, Location in the source code.
        self.functionLocation: Location = Location
        # Location in the source code.
        self.location: Location = Location
        # JavaScript script name or url.
        self.url: str = str
        # Scope chain for this call frame.
        self.scopeChain: List[Scope] = [Scope]
        # `this` object for this call frame.
        self.this: Runtime.RemoteObject = Runtime.RemoteObject
        # OPTIONAL, The value being returned, if the function is at return point.
        self.returnValue: Runtime.RemoteObject = Runtime.RemoteObject


# object: Scope
class Scope(TypingT):
    """
        Scope description.
    """
    def __init__(self):
        # Scope type.
        self.type: str = str
        # Object representing the scope. For `global` and `with` scopes it represents the actualobject; for the rest of the scopes, it is artificial transient object enumerating scopevariables as its properties.
        self.object: Runtime.RemoteObject = Runtime.RemoteObject
        # OPTIONAL, name
        self.name: str = str
        # OPTIONAL, Location in the source code where scope starts
        self.startLocation: Location = Location
        # OPTIONAL, Location in the source code where scope ends
        self.endLocation: Location = Location


# object: SearchMatch
class SearchMatch(TypingT):
    """
        Search match for resource.
    """
    def __init__(self):
        # Line number in resource content.
        self.lineNumber: int = int
        # Line with match content.
        self.lineContent: str = str


# object: BreakLocation
class BreakLocation(TypingT):
    """
        BreakLocation
    """
    def __init__(self):
        # Script identifier as reported in the `Debugger.scriptParsed`.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # Line number in the script (0-based).
        self.lineNumber: int = int
        # OPTIONAL, Column number in the script (0-based).
        self.columnNumber: int = int
        # OPTIONAL, type
        self.type: str = str


# typing: Enum of possible script languages.
ScriptLanguage = str
ScriptLanguageEnums = ['JavaScript', 'WebAssembly']


# object: DebugSymbols
class DebugSymbols(TypingT):
    """
        Debug symbols available for a wasm script.
    """
    def __init__(self):
        # Type of the debug symbols.
        self.type: str = str
        # OPTIONAL, URL of the external symbol source.
        self.externalURL: str = str


# event: breakpointResolved
class breakpointResolved(EventT):
    """
        Fired when breakpoint is resolved to an actual script and location.
    """
    event="Debugger.breakpointResolved"
    def __init__(self):
        # Breakpoint unique identifier.
        self.breakpointId: BreakpointId = BreakpointId
        # Actual breakpoint location.
        self.location: Location = Location


# event: paused
class paused(EventT):
    """
        Fired when the virtual machine stopped on breakpoint or exception or any other stop criteria.
    """
    event="Debugger.paused"
    def __init__(self):
        # Call stack the virtual machine stopped on.
        self.callFrames: List[CallFrame] = [CallFrame]
        reasonEnums = ['ambiguous', 'assert', 'debugCommand', 'DOM', 'EventListener', 'exception', 'instrumentation', 'OOM', 'other', 'promiseRejection', 'XHR']
        # Pause reason.
        self.reason: str = str
        # OPTIONAL, Object containing break-specific auxiliary properties.
        self.data: any = any
        # OPTIONAL, Hit breakpoints IDs
        self.hitBreakpoints: List[str] = [str]
        # OPTIONAL, Async stack trace, if any.
        self.asyncStackTrace: Runtime.StackTrace = Runtime.StackTrace
        # OPTIONAL, Async stack trace, if any.
        self.asyncStackTraceId: Runtime.StackTraceId = Runtime.StackTraceId
        # OPTIONAL, Never present, will be removed.
        self.asyncCallStackTraceId: Runtime.StackTraceId = Runtime.StackTraceId


# event: resumed
class resumed(EventT):
    """
        Fired when the virtual machine resumed execution.
    """
    event="Debugger.resumed"
    def __init__(self):
        pass


# event: scriptFailedToParse
class scriptFailedToParse(EventT):
    """
        Fired when virtual machine fails to parse the script.
    """
    event="Debugger.scriptFailedToParse"
    def __init__(self):
        # Identifier of the script parsed.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # URL or name of the script parsed (if any).
        self.url: str = str
        # Line offset of the script within the resource with given URL (for script tags).
        self.startLine: int = int
        # Column offset of the script within the resource with given URL.
        self.startColumn: int = int
        # Last line of the script.
        self.endLine: int = int
        # Length of the last line of the script.
        self.endColumn: int = int
        # Specifies script creation context.
        self.executionContextId: Runtime.ExecutionContextId = Runtime.ExecutionContextId
        # Content hash of the script.
        self.hash: str = str
        # OPTIONAL, Embedder-specific auxiliary data.
        self.executionContextAuxData: any = any
        # OPTIONAL, URL of source map associated with script (if any).
        self.sourceMapURL: str = str
        # OPTIONAL, True, if this script has sourceURL.
        self.hasSourceURL: bool = bool
        # OPTIONAL, True, if this script is ES6 module.
        self.isModule: bool = bool
        # OPTIONAL, This script length.
        self.length: int = int
        # OPTIONAL, JavaScript top stack frame of where the script parsed event was triggered if available.
        self.stackTrace: Runtime.StackTrace = Runtime.StackTrace
        # OPTIONAL, If the scriptLanguage is WebAssembly, the code section offset in the module.
        self.codeOffset: int = int
        # OPTIONAL, The language of the script.
        self.scriptLanguage: Debugger.ScriptLanguage = Debugger.ScriptLanguage
        # OPTIONAL, The name the embedder supplied for this script.
        self.embedderName: str = str


# event: scriptParsed
class scriptParsed(EventT):
    """
        Fired when virtual machine parses script. This event is also fired for all known and uncollected
        scripts upon enabling debugger.
    """
    event="Debugger.scriptParsed"
    def __init__(self):
        # Identifier of the script parsed.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # URL or name of the script parsed (if any).
        self.url: str = str
        # Line offset of the script within the resource with given URL (for script tags).
        self.startLine: int = int
        # Column offset of the script within the resource with given URL.
        self.startColumn: int = int
        # Last line of the script.
        self.endLine: int = int
        # Length of the last line of the script.
        self.endColumn: int = int
        # Specifies script creation context.
        self.executionContextId: Runtime.ExecutionContextId = Runtime.ExecutionContextId
        # Content hash of the script.
        self.hash: str = str
        # OPTIONAL, Embedder-specific auxiliary data.
        self.executionContextAuxData: any = any
        # OPTIONAL, True, if this script is generated as a result of the live edit operation.
        self.isLiveEdit: bool = bool
        # OPTIONAL, URL of source map associated with script (if any).
        self.sourceMapURL: str = str
        # OPTIONAL, True, if this script has sourceURL.
        self.hasSourceURL: bool = bool
        # OPTIONAL, True, if this script is ES6 module.
        self.isModule: bool = bool
        # OPTIONAL, This script length.
        self.length: int = int
        # OPTIONAL, JavaScript top stack frame of where the script parsed event was triggered if available.
        self.stackTrace: Runtime.StackTrace = Runtime.StackTrace
        # OPTIONAL, If the scriptLanguage is WebAssembly, the code section offset in the module.
        self.codeOffset: int = int
        # OPTIONAL, The language of the script.
        self.scriptLanguage: Debugger.ScriptLanguage = Debugger.ScriptLanguage
        # OPTIONAL, If the scriptLanguage is WebASsembly, the source of debug symbols for the module.
        self.debugSymbols: Debugger.DebugSymbols = Debugger.DebugSymbols
        # OPTIONAL, The name the embedder supplied for this script.
        self.embedderName: str = str


import cdp.Runtime as Runtime
# ================================================================================
# Debugger Domain.
# ================================================================================
class Debugger(DomainT):
    """
        Debugger domain exposes JavaScript debugging capabilities. It allows setting and removing
        breakpoints, stepping through execution, exploring stack traces, etc.
    """
    def __init__(self, drv):
        self.drv = drv


    # func: continueToLocation
    def continueToLocation(self,location:Location, targetCallFrames:str=None):
        """
            Continues execution until specific location is reached.
        Params:
            1. location: Location
                Location to continue to.
            targetCallFramesEnums = ['any', 'current']
            2. targetCallFrames: str (OPTIONAL)
        """
        return self.drv.call(None,'Debugger.continueToLocation',location=location, targetCallFrames=targetCallFrames)


    # func: disable
    def disable(self):
        """
            Disables debugger for given page.
        """
        return self.drv.call(None,'Debugger.disable')


    # return: enableReturn
    class enableReturn(ReturnT):
        def __init__(self):
            # Unique identifier of the debugger.
            self.debuggerId: Runtime.UniqueDebuggerId = Runtime.UniqueDebuggerId


    # func: enable
    def enable(self,maxScriptsCacheSize:int=None) -> enableReturn:
        """
            Enables debugger for the given page. Clients should not assume that the debugging has been
            enabled until the result for this command is received.
        Params:
            1. maxScriptsCacheSize: int (OPTIONAL)
                The maximum size in bytes of collected scripts (not referenced by other heap objects)the debugger can hold. Puts no limit if paramter is omitted.
        Return: enableReturn
        """
        return self.drv.call(Debugger.enableReturn,'Debugger.enable',maxScriptsCacheSize=maxScriptsCacheSize)


    # return: evaluateOnCallFrameReturn
    class evaluateOnCallFrameReturn(ReturnT):
        def __init__(self):
            # Object wrapper for the evaluation result.
            self.result: Runtime.RemoteObject = Runtime.RemoteObject
            # OPTIONAL, Exception details.
            self.exceptionDetails: Runtime.ExceptionDetails = Runtime.ExceptionDetails


    # func: evaluateOnCallFrame
    def evaluateOnCallFrame(self,callFrameId:CallFrameId, expression:str, objectGroup:str=None, includeCommandLineAPI:bool=None, silent:bool=None, returnByValue:bool=None, generatePreview:bool=None, throwOnSideEffect:bool=None, timeout:Runtime.TimeDelta=None) -> evaluateOnCallFrameReturn:
        """
            Evaluates expression on a given call frame.
        Params:
            1. callFrameId: CallFrameId
                Call frame identifier to evaluate on.
            2. expression: str
                Expression to evaluate.
            3. objectGroup: str (OPTIONAL)
                String object group name to put result into (allows rapid releasing resulting object handlesusing `releaseObjectGroup`).
            4. includeCommandLineAPI: bool (OPTIONAL)
                Specifies whether command line API should be available to the evaluated expression, defaultsto false.
            5. silent: bool (OPTIONAL)
                In silent mode exceptions thrown during evaluation are not reported and do not pauseexecution. Overrides `setPauseOnException` state.
            6. returnByValue: bool (OPTIONAL)
                Whether the result is expected to be a JSON object that should be sent by value.
            7. generatePreview: bool (OPTIONAL)
                Whether preview should be generated for the result.
            8. throwOnSideEffect: bool (OPTIONAL)
                Whether to throw an exception if side effect cannot be ruled out during evaluation.
            9. timeout: Runtime.TimeDelta (OPTIONAL)
                Terminate execution after timing out (number of milliseconds).
        Return: evaluateOnCallFrameReturn
        """
        return self.drv.call(Debugger.evaluateOnCallFrameReturn,'Debugger.evaluateOnCallFrame',callFrameId=callFrameId, expression=expression, objectGroup=objectGroup, includeCommandLineAPI=includeCommandLineAPI, silent=silent, returnByValue=returnByValue, generatePreview=generatePreview, throwOnSideEffect=throwOnSideEffect, timeout=timeout)


    # return: executeWasmEvaluatorReturn
    class executeWasmEvaluatorReturn(ReturnT):
        def __init__(self):
            # Object wrapper for the evaluation result.
            self.result: Runtime.RemoteObject = Runtime.RemoteObject
            # OPTIONAL, Exception details.
            self.exceptionDetails: Runtime.ExceptionDetails = Runtime.ExceptionDetails


    # func: executeWasmEvaluator
    def executeWasmEvaluator(self,callFrameId:CallFrameId, evaluator:str, timeout:Runtime.TimeDelta=None) -> executeWasmEvaluatorReturn:
        """
            Execute a Wasm Evaluator module on a given call frame.
        Params:
            1. callFrameId: CallFrameId
                WebAssembly call frame identifier to evaluate on.
            2. evaluator: str
                Code of the evaluator module.
            3. timeout: Runtime.TimeDelta (OPTIONAL)
                Terminate execution after timing out (number of milliseconds).
        Return: executeWasmEvaluatorReturn
        """
        return self.drv.call(Debugger.executeWasmEvaluatorReturn,'Debugger.executeWasmEvaluator',callFrameId=callFrameId, evaluator=evaluator, timeout=timeout)


    # return: getPossibleBreakpointsReturn
    class getPossibleBreakpointsReturn(ReturnT):
        def __init__(self):
            # List of the possible breakpoint locations.
            self.locations: List[BreakLocation] = [BreakLocation]


    # func: getPossibleBreakpoints
    def getPossibleBreakpoints(self,start:Location, end:Location=None, restrictToFunction:bool=None) -> getPossibleBreakpointsReturn:
        """
            Returns possible locations for breakpoint. scriptId in start and end range locations should be
            the same.
        Params:
            1. start: Location
                Start of range to search possible breakpoint locations in.
            2. end: Location (OPTIONAL)
                End of range to search possible breakpoint locations in (excluding). When not specified, endof scripts is used as end of range.
            3. restrictToFunction: bool (OPTIONAL)
                Only consider locations which are in the same (non-nested) function as start.
        Return: getPossibleBreakpointsReturn
        """
        return self.drv.call(Debugger.getPossibleBreakpointsReturn,'Debugger.getPossibleBreakpoints',start=start, end=end, restrictToFunction=restrictToFunction)


    # return: getScriptSourceReturn
    class getScriptSourceReturn(ReturnT):
        def __init__(self):
            # Script source (empty in case of Wasm bytecode).
            self.scriptSource: str = str
            # OPTIONAL, Wasm bytecode.
            self.bytecode: str = str


    # func: getScriptSource
    def getScriptSource(self,scriptId:Runtime.ScriptId) -> getScriptSourceReturn:
        """
            Returns source for the script with given id.
        Params:
            1. scriptId: Runtime.ScriptId
                Id of the script to get source for.
        Return: getScriptSourceReturn
        """
        return self.drv.call(Debugger.getScriptSourceReturn,'Debugger.getScriptSource',scriptId=scriptId)


    # return: getWasmBytecodeReturn
    class getWasmBytecodeReturn(ReturnT):
        def __init__(self):
            # Script source.
            self.bytecode: str = str


    # func: getWasmBytecode
    def getWasmBytecode(self,scriptId:Runtime.ScriptId) -> getWasmBytecodeReturn:
        """
            This command is deprecated. Use getScriptSource instead.
        Params:
            1. scriptId: Runtime.ScriptId
                Id of the Wasm script to get source for.
        Return: getWasmBytecodeReturn
        """
        return self.drv.call(Debugger.getWasmBytecodeReturn,'Debugger.getWasmBytecode',scriptId=scriptId)


    # return: getStackTraceReturn
    class getStackTraceReturn(ReturnT):
        def __init__(self):
            # stackTrace
            self.stackTrace: Runtime.StackTrace = Runtime.StackTrace


    # func: getStackTrace
    def getStackTrace(self,stackTraceId:Runtime.StackTraceId) -> getStackTraceReturn:
        """
            Returns stack trace with given `stackTraceId`.
        Params:
            1. stackTraceId: Runtime.StackTraceId
        Return: getStackTraceReturn
        """
        return self.drv.call(Debugger.getStackTraceReturn,'Debugger.getStackTrace',stackTraceId=stackTraceId)


    # func: pause
    def pause(self):
        """
            Stops on the next JavaScript statement.
        """
        return self.drv.call(None,'Debugger.pause')


    # func: pauseOnAsyncCall
    def pauseOnAsyncCall(self,parentStackTraceId:Runtime.StackTraceId):
        """
        Params:
            1. parentStackTraceId: Runtime.StackTraceId
                Debugger will pause when async call with given stack trace is started.
        """
        return self.drv.call(None,'Debugger.pauseOnAsyncCall',parentStackTraceId=parentStackTraceId)


    # func: removeBreakpoint
    def removeBreakpoint(self,breakpointId:BreakpointId):
        """
            Removes JavaScript breakpoint.
        Params:
            1. breakpointId: BreakpointId
        """
        return self.drv.call(None,'Debugger.removeBreakpoint',breakpointId=breakpointId)


    # return: restartFrameReturn
    class restartFrameReturn(ReturnT):
        def __init__(self):
            # New stack trace.
            self.callFrames: List[CallFrame] = [CallFrame]
            # OPTIONAL, Async stack trace, if any.
            self.asyncStackTrace: Runtime.StackTrace = Runtime.StackTrace
            # OPTIONAL, Async stack trace, if any.
            self.asyncStackTraceId: Runtime.StackTraceId = Runtime.StackTraceId


    # func: restartFrame
    def restartFrame(self,callFrameId:CallFrameId) -> restartFrameReturn:
        """
            Restarts particular call frame from the beginning.
        Params:
            1. callFrameId: CallFrameId
                Call frame identifier to evaluate on.
        Return: restartFrameReturn
        """
        return self.drv.call(Debugger.restartFrameReturn,'Debugger.restartFrame',callFrameId=callFrameId)


    # func: resume
    def resume(self,terminateOnResume:bool=None):
        """
            Resumes JavaScript execution.
        Params:
            1. terminateOnResume: bool (OPTIONAL)
                Set to true to terminate execution upon resuming execution. In contrastto Runtime.terminateExecution, this will allows to execute furtherJavaScript (i.e. via evaluation) until execution of the paused codeis actually resumed, at which point termination is triggered.If execution is currently not paused, this parameter has no effect.
        """
        return self.drv.call(None,'Debugger.resume',terminateOnResume=terminateOnResume)


    # return: searchInContentReturn
    class searchInContentReturn(ReturnT):
        def __init__(self):
            # List of search matches.
            self.result: List[SearchMatch] = [SearchMatch]


    # func: searchInContent
    def searchInContent(self,scriptId:Runtime.ScriptId, query:str, caseSensitive:bool=None, isRegex:bool=None) -> searchInContentReturn:
        """
            Searches for given string in script content.
        Params:
            1. scriptId: Runtime.ScriptId
                Id of the script to search in.
            2. query: str
                String to search for.
            3. caseSensitive: bool (OPTIONAL)
                If true, search is case sensitive.
            4. isRegex: bool (OPTIONAL)
                If true, treats string parameter as regex.
        Return: searchInContentReturn
        """
        return self.drv.call(Debugger.searchInContentReturn,'Debugger.searchInContent',scriptId=scriptId, query=query, caseSensitive=caseSensitive, isRegex=isRegex)


    # func: setAsyncCallStackDepth
    def setAsyncCallStackDepth(self,maxDepth:int):
        """
            Enables or disables async call stacks tracking.
        Params:
            1. maxDepth: int
                Maximum depth of async call stacks. Setting to `0` will effectively disable collecting asynccall stacks (default).
        """
        return self.drv.call(None,'Debugger.setAsyncCallStackDepth',maxDepth=maxDepth)


    # func: setBlackboxPatterns
    def setBlackboxPatterns(self,patterns:List[str]):
        """
            Replace previous blackbox patterns with passed ones. Forces backend to skip stepping/pausing in
            scripts with url matching one of the patterns. VM will try to leave blackboxed script by
            performing 'step in' several times, finally resorting to 'step out' if unsuccessful.
        Params:
            1. patterns: List[str]
                Array of regexps that will be used to check script url for blackbox state.
        """
        return self.drv.call(None,'Debugger.setBlackboxPatterns',patterns=patterns)


    # func: setBlackboxedRanges
    def setBlackboxedRanges(self,scriptId:Runtime.ScriptId, positions:List[ScriptPosition]):
        """
            Makes backend skip steps in the script in blackboxed ranges. VM will try leave blacklisted
            scripts by performing 'step in' several times, finally resorting to 'step out' if unsuccessful.
            Positions array contains positions where blackbox state is changed. First interval isn't
            blackboxed. Array should be sorted.
        Params:
            1. scriptId: Runtime.ScriptId
                Id of the script.
            2. positions: List[ScriptPosition]
        """
        return self.drv.call(None,'Debugger.setBlackboxedRanges',scriptId=scriptId, positions=positions)


    # return: setBreakpointReturn
    class setBreakpointReturn(ReturnT):
        def __init__(self):
            # Id of the created breakpoint for further reference.
            self.breakpointId: BreakpointId = BreakpointId
            # Location this breakpoint resolved into.
            self.actualLocation: Location = Location


    # func: setBreakpoint
    def setBreakpoint(self,location:Location, condition:str=None) -> setBreakpointReturn:
        """
            Sets JavaScript breakpoint at a given location.
        Params:
            1. location: Location
                Location to set breakpoint in.
            2. condition: str (OPTIONAL)
                Expression to use as a breakpoint condition. When specified, debugger will only stop on thebreakpoint if this expression evaluates to true.
        Return: setBreakpointReturn
        """
        return self.drv.call(Debugger.setBreakpointReturn,'Debugger.setBreakpoint',location=location, condition=condition)


    # return: setInstrumentationBreakpointReturn
    class setInstrumentationBreakpointReturn(ReturnT):
        def __init__(self):
            # Id of the created breakpoint for further reference.
            self.breakpointId: BreakpointId = BreakpointId


    # func: setInstrumentationBreakpoint
    def setInstrumentationBreakpoint(self,instrumentation:str) -> setInstrumentationBreakpointReturn:
        """
            Sets instrumentation breakpoint.
        Params:
            instrumentationEnums = ['beforeScriptExecution', 'beforeScriptWithSourceMapExecution']
            1. instrumentation: str
                Instrumentation name.
        Return: setInstrumentationBreakpointReturn
        """
        return self.drv.call(Debugger.setInstrumentationBreakpointReturn,'Debugger.setInstrumentationBreakpoint',instrumentation=instrumentation)


    # return: setBreakpointByUrlReturn
    class setBreakpointByUrlReturn(ReturnT):
        def __init__(self):
            # Id of the created breakpoint for further reference.
            self.breakpointId: BreakpointId = BreakpointId
            # List of the locations this breakpoint resolved into upon addition.
            self.locations: List[Location] = [Location]


    # func: setBreakpointByUrl
    def setBreakpointByUrl(self,lineNumber:int, url:str=None, urlRegex:str=None, scriptHash:str=None, columnNumber:int=None, condition:str=None) -> setBreakpointByUrlReturn:
        """
            Sets JavaScript breakpoint at given location specified either by URL or URL regex. Once this
            command is issued, all existing parsed scripts will have breakpoints resolved and returned in
            `locations` property. Further matching script parsing will result in subsequent
            `breakpointResolved` events issued. This logical breakpoint will survive page reloads.
        Params:
            1. lineNumber: int
                Line number to set breakpoint at.
            2. url: str (OPTIONAL)
                URL of the resources to set breakpoint on.
            3. urlRegex: str (OPTIONAL)
                Regex pattern for the URLs of the resources to set breakpoints on. Either `url` or`urlRegex` must be specified.
            4. scriptHash: str (OPTIONAL)
                Script hash of the resources to set breakpoint on.
            5. columnNumber: int (OPTIONAL)
                Offset in the line to set breakpoint at.
            6. condition: str (OPTIONAL)
                Expression to use as a breakpoint condition. When specified, debugger will only stop on thebreakpoint if this expression evaluates to true.
        Return: setBreakpointByUrlReturn
        """
        return self.drv.call(Debugger.setBreakpointByUrlReturn,'Debugger.setBreakpointByUrl',lineNumber=lineNumber, url=url, urlRegex=urlRegex, scriptHash=scriptHash, columnNumber=columnNumber, condition=condition)


    # return: setBreakpointOnFunctionCallReturn
    class setBreakpointOnFunctionCallReturn(ReturnT):
        def __init__(self):
            # Id of the created breakpoint for further reference.
            self.breakpointId: BreakpointId = BreakpointId


    # func: setBreakpointOnFunctionCall
    def setBreakpointOnFunctionCall(self,objectId:Runtime.RemoteObjectId, condition:str=None) -> setBreakpointOnFunctionCallReturn:
        """
            Sets JavaScript breakpoint before each call to the given function.
            If another function was created from the same source as a given one,
            calling it will also trigger the breakpoint.
        Params:
            1. objectId: Runtime.RemoteObjectId
                Function object id.
            2. condition: str (OPTIONAL)
                Expression to use as a breakpoint condition. When specified, debugger willstop on the breakpoint if this expression evaluates to true.
        Return: setBreakpointOnFunctionCallReturn
        """
        return self.drv.call(Debugger.setBreakpointOnFunctionCallReturn,'Debugger.setBreakpointOnFunctionCall',objectId=objectId, condition=condition)


    # func: setBreakpointsActive
    def setBreakpointsActive(self,active:bool):
        """
            Activates / deactivates all breakpoints on the page.
        Params:
            1. active: bool
                New value for breakpoints active state.
        """
        return self.drv.call(None,'Debugger.setBreakpointsActive',active=active)


    # func: setPauseOnExceptions
    def setPauseOnExceptions(self,state:str):
        """
            Defines pause on exceptions state. Can be set to stop on all exceptions, uncaught exceptions or
            no exceptions. Initial pause on exceptions state is `none`.
        Params:
            stateEnums = ['none', 'uncaught', 'all']
            1. state: str
                Pause on exceptions mode.
        """
        return self.drv.call(None,'Debugger.setPauseOnExceptions',state=state)


    # func: setReturnValue
    def setReturnValue(self,newValue:Runtime.CallArgument):
        """
            Changes return value in top frame. Available only at return break position.
        Params:
            1. newValue: Runtime.CallArgument
                New return value.
        """
        return self.drv.call(None,'Debugger.setReturnValue',newValue=newValue)


    # return: setScriptSourceReturn
    class setScriptSourceReturn(ReturnT):
        def __init__(self):
            # OPTIONAL, New stack trace in case editing has happened while VM was stopped.
            self.callFrames: List[CallFrame] = [CallFrame]
            # OPTIONAL, Whether current call stack  was modified after applying the changes.
            self.stackChanged: bool = bool
            # OPTIONAL, Async stack trace, if any.
            self.asyncStackTrace: Runtime.StackTrace = Runtime.StackTrace
            # OPTIONAL, Async stack trace, if any.
            self.asyncStackTraceId: Runtime.StackTraceId = Runtime.StackTraceId
            # OPTIONAL, Exception details if any.
            self.exceptionDetails: Runtime.ExceptionDetails = Runtime.ExceptionDetails


    # func: setScriptSource
    def setScriptSource(self,scriptId:Runtime.ScriptId, scriptSource:str, dryRun:bool=None) -> setScriptSourceReturn:
        """
            Edits JavaScript source live.
        Params:
            1. scriptId: Runtime.ScriptId
                Id of the script to edit.
            2. scriptSource: str
                New content of the script.
            3. dryRun: bool (OPTIONAL)
                If true the change will not actually be applied. Dry run may be used to get resultdescription without actually modifying the code.
        Return: setScriptSourceReturn
        """
        return self.drv.call(Debugger.setScriptSourceReturn,'Debugger.setScriptSource',scriptId=scriptId, scriptSource=scriptSource, dryRun=dryRun)


    # func: setSkipAllPauses
    def setSkipAllPauses(self,skip:bool):
        """
            Makes page not interrupt on any pauses (breakpoint, exception, dom exception etc).
        Params:
            1. skip: bool
                New value for skip pauses state.
        """
        return self.drv.call(None,'Debugger.setSkipAllPauses',skip=skip)


    # func: setVariableValue
    def setVariableValue(self,scopeNumber:int, variableName:str, newValue:Runtime.CallArgument, callFrameId:CallFrameId):
        """
            Changes value of variable in a callframe. Object-based scopes are not supported and must be
            mutated manually.
        Params:
            1. scopeNumber: int
                0-based number of scope as was listed in scope chain. Only 'local', 'closure' and 'catch'scope types are allowed. Other scopes could be manipulated manually.
            2. variableName: str
                Variable name.
            3. newValue: Runtime.CallArgument
                New variable value.
            4. callFrameId: CallFrameId
                Id of callframe that holds variable.
        """
        return self.drv.call(None,'Debugger.setVariableValue',scopeNumber=scopeNumber, variableName=variableName, newValue=newValue, callFrameId=callFrameId)


    # func: stepInto
    def stepInto(self,breakOnAsyncCall:bool=None, skipList:List[LocationRange]=None):
        """
            Steps into the function call.
        Params:
            1. breakOnAsyncCall: bool (OPTIONAL)
                Debugger will pause on the execution of the first async task which was scheduledbefore next pause.
            2. skipList: List[LocationRange] (OPTIONAL)
                The skipList specifies location ranges that should be skipped on step into.
        """
        return self.drv.call(None,'Debugger.stepInto',breakOnAsyncCall=breakOnAsyncCall, skipList=skipList)


    # func: stepOut
    def stepOut(self):
        """
            Steps out of the function call.
        """
        return self.drv.call(None,'Debugger.stepOut')


    # func: stepOver
    def stepOver(self,skipList:List[LocationRange]=None):
        """
            Steps over the statement.
        Params:
            1. skipList: List[LocationRange] (OPTIONAL)
                The skipList specifies location ranges that should be skipped on step over.
        """
        return self.drv.call(None,'Debugger.stepOver',skipList=skipList)



