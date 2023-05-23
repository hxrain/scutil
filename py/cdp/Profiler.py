"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# object: ProfileNode
class ProfileNode(TypingT):
    """
        Profile node. Holds callsite information, execution statistics and child nodes.
    """
    def __init__(self):
        # Unique id of the node.
        self.id: int = int
        # Function location.
        self.callFrame: Runtime.CallFrame = Runtime.CallFrame
        # OPTIONAL, Number of samples where this node was on top of the call stack.
        self.hitCount: int = int
        # OPTIONAL, Child node ids.
        self.children: List[int] = [int]
        # OPTIONAL, The reason of being not optimized. The function may be deoptimized or marked as don'toptimize.
        self.deoptReason: str = str
        # OPTIONAL, An array of source position ticks.
        self.positionTicks: List[PositionTickInfo] = [PositionTickInfo]


# object: Profile
class Profile(TypingT):
    """
        Profile.
    """
    def __init__(self):
        # The list of profile nodes. First item is the root node.
        self.nodes: List[ProfileNode] = [ProfileNode]
        # Profiling start timestamp in microseconds.
        self.startTime: int = int
        # Profiling end timestamp in microseconds.
        self.endTime: int = int
        # OPTIONAL, Ids of samples top nodes.
        self.samples: List[int] = [int]
        # OPTIONAL, Time intervals between adjacent samples in microseconds. The first delta is relative to theprofile startTime.
        self.timeDeltas: List[int] = [int]


# object: PositionTickInfo
class PositionTickInfo(TypingT):
    """
        Specifies a number of samples attributed to a certain source position.
    """
    def __init__(self):
        # Source line number (1-based).
        self.line: int = int
        # Number of samples attributed to the source line.
        self.ticks: int = int


# object: CoverageRange
class CoverageRange(TypingT):
    """
        Coverage data for a source range.
    """
    def __init__(self):
        # JavaScript script source offset for the range start.
        self.startOffset: int = int
        # JavaScript script source offset for the range end.
        self.endOffset: int = int
        # Collected execution count of the source range.
        self.count: int = int


# object: FunctionCoverage
class FunctionCoverage(TypingT):
    """
        Coverage data for a JavaScript function.
    """
    def __init__(self):
        # JavaScript function name.
        self.functionName: str = str
        # Source ranges inside the function with coverage data.
        self.ranges: List[CoverageRange] = [CoverageRange]
        # Whether coverage data for this function has block granularity.
        self.isBlockCoverage: bool = bool


# object: ScriptCoverage
class ScriptCoverage(TypingT):
    """
        Coverage data for a JavaScript script.
    """
    def __init__(self):
        # JavaScript script id.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # JavaScript script name or url.
        self.url: str = str
        # Functions contained in the script that has coverage data.
        self.functions: List[FunctionCoverage] = [FunctionCoverage]


# object: TypeObject
class TypeObject(TypingT):
    """
        Describes a type collected during runtime.
    """
    def __init__(self):
        # Name of a type collected with type profiling.
        self.name: str = str


# object: TypeProfileEntry
class TypeProfileEntry(TypingT):
    """
        Source offset and types for a parameter or return value.
    """
    def __init__(self):
        # Source offset of the parameter or end of function for return values.
        self.offset: int = int
        # The types for this parameter or return value.
        self.types: List[TypeObject] = [TypeObject]


# object: ScriptTypeProfile
class ScriptTypeProfile(TypingT):
    """
        Type profile data collected during runtime for a JavaScript script.
    """
    def __init__(self):
        # JavaScript script id.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # JavaScript script name or url.
        self.url: str = str
        # Type profile entries for parameters and return values of the functions in the script.
        self.entries: List[TypeProfileEntry] = [TypeProfileEntry]


# object: CounterInfo
class CounterInfo(TypingT):
    """
        Collected counter information.
    """
    def __init__(self):
        # Counter name.
        self.name: str = str
        # Counter value.
        self.value: int = int


# event: consoleProfileFinished
class consoleProfileFinished(EventT):
    """
        consoleProfileFinished
    """
    event="Profiler.consoleProfileFinished"
    def __init__(self):
        # id
        self.id: str = str
        # Location of console.profileEnd().
        self.location: Debugger.Location = Debugger.Location
        # profile
        self.profile: Profile = Profile
        # OPTIONAL, Profile title passed as an argument to console.profile().
        self.title: str = str


# event: consoleProfileStarted
class consoleProfileStarted(EventT):
    """
        Sent when new profile recording is started using console.profile() call.
    """
    event="Profiler.consoleProfileStarted"
    def __init__(self):
        # id
        self.id: str = str
        # Location of console.profile().
        self.location: Debugger.Location = Debugger.Location
        # OPTIONAL, Profile title passed as an argument to console.profile().
        self.title: str = str


import cdp.Runtime as Runtime
import cdp.Debugger as Debugger
# ================================================================================
# Profiler Domain.
# ================================================================================
class Profiler(DomainT):
    """
        Profiler
    """
    def __init__(self, drv):
        self.drv = drv


    # func: disable
    def disable(self):
        """
        """
        return self.drv.call(None,'Profiler.disable')


    # func: enable
    def enable(self):
        """
        """
        return self.drv.call(None,'Profiler.enable')


    # return: getBestEffortCoverageReturn
    class getBestEffortCoverageReturn(ReturnT):
        def __init__(self):
            # Coverage data for the current isolate.
            self.result: List[ScriptCoverage] = [ScriptCoverage]


    # func: getBestEffortCoverage
    def getBestEffortCoverage(self) -> getBestEffortCoverageReturn:
        """
            Collect coverage data for the current isolate. The coverage data may be incomplete due to
            garbage collection.
        Return: getBestEffortCoverageReturn
        """
        return self.drv.call(Profiler.getBestEffortCoverageReturn,'Profiler.getBestEffortCoverage')


    # func: setSamplingInterval
    def setSamplingInterval(self,interval:int):
        """
            Changes CPU profiler sampling interval. Must be called before CPU profiles recording started.
        Params:
            1. interval: int
                New sampling interval in microseconds.
        """
        return self.drv.call(None,'Profiler.setSamplingInterval',interval=interval)


    # func: start
    def start(self):
        """
        """
        return self.drv.call(None,'Profiler.start')


    # return: startPreciseCoverageReturn
    class startPreciseCoverageReturn(ReturnT):
        def __init__(self):
            # Monotonically increasing time (in seconds) when the coverage update was taken in the backend.
            self.timestamp: int = int


    # func: startPreciseCoverage
    def startPreciseCoverage(self,callCount:bool=None, detailed:bool=None, allowTriggeredUpdates:bool=None) -> startPreciseCoverageReturn:
        """
            Enable precise code coverage. Coverage data for JavaScript executed before enabling precise code
            coverage may be incomplete. Enabling prevents running optimized code and resets execution
            counters.
        Params:
            1. callCount: bool (OPTIONAL)
                Collect accurate call counts beyond simple 'covered' or 'not covered'.
            2. detailed: bool (OPTIONAL)
                Collect block-based coverage.
            3. allowTriggeredUpdates: bool (OPTIONAL)
                Allow the backend to send updates on its own initiative
        Return: startPreciseCoverageReturn
        """
        return self.drv.call(Profiler.startPreciseCoverageReturn,'Profiler.startPreciseCoverage',callCount=callCount, detailed=detailed, allowTriggeredUpdates=allowTriggeredUpdates)


    # func: startTypeProfile
    def startTypeProfile(self):
        """
            Enable type profile.
        """
        return self.drv.call(None,'Profiler.startTypeProfile')


    # return: stopReturn
    class stopReturn(ReturnT):
        def __init__(self):
            # Recorded profile.
            self.profile: Profile = Profile


    # func: stop
    def stop(self) -> stopReturn:
        """
        Return: stopReturn
        """
        return self.drv.call(Profiler.stopReturn,'Profiler.stop')


    # func: stopPreciseCoverage
    def stopPreciseCoverage(self):
        """
            Disable precise code coverage. Disabling releases unnecessary execution count records and allows
            executing optimized code.
        """
        return self.drv.call(None,'Profiler.stopPreciseCoverage')


    # func: stopTypeProfile
    def stopTypeProfile(self):
        """
            Disable type profile. Disabling releases type profile data collected so far.
        """
        return self.drv.call(None,'Profiler.stopTypeProfile')


    # return: takePreciseCoverageReturn
    class takePreciseCoverageReturn(ReturnT):
        def __init__(self):
            # Coverage data for the current isolate.
            self.result: List[ScriptCoverage] = [ScriptCoverage]
            # Monotonically increasing time (in seconds) when the coverage update was taken in the backend.
            self.timestamp: int = int


    # func: takePreciseCoverage
    def takePreciseCoverage(self) -> takePreciseCoverageReturn:
        """
            Collect coverage data for the current isolate, and resets execution counters. Precise code
            coverage needs to have started.
        Return: takePreciseCoverageReturn
        """
        return self.drv.call(Profiler.takePreciseCoverageReturn,'Profiler.takePreciseCoverage')


    # return: takeTypeProfileReturn
    class takeTypeProfileReturn(ReturnT):
        def __init__(self):
            # Type profile for all scripts since startTypeProfile() was turned on.
            self.result: List[ScriptTypeProfile] = [ScriptTypeProfile]


    # func: takeTypeProfile
    def takeTypeProfile(self) -> takeTypeProfileReturn:
        """
            Collect type profile.
        Return: takeTypeProfileReturn
        """
        return self.drv.call(Profiler.takeTypeProfileReturn,'Profiler.takeTypeProfile')


    # func: enableRuntimeCallStats
    def enableRuntimeCallStats(self):
        """
            Enable run time call stats collection.
        """
        return self.drv.call(None,'Profiler.enableRuntimeCallStats')


    # func: disableRuntimeCallStats
    def disableRuntimeCallStats(self):
        """
            Disable run time call stats collection.
        """
        return self.drv.call(None,'Profiler.disableRuntimeCallStats')


    # return: getRuntimeCallStatsReturn
    class getRuntimeCallStatsReturn(ReturnT):
        def __init__(self):
            # Collected counter information.
            self.result: List[CounterInfo] = [CounterInfo]


    # func: getRuntimeCallStats
    def getRuntimeCallStats(self) -> getRuntimeCallStatsReturn:
        """
            Retrieve run time call stats.
        Return: getRuntimeCallStatsReturn
        """
        return self.drv.call(Profiler.getRuntimeCallStatsReturn,'Profiler.getRuntimeCallStats')



