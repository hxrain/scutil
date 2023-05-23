"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: DOM breakpoint type.
DOMBreakpointType = str
DOMBreakpointTypeEnums = ['subtree-modified', 'attribute-modified', 'node-removed']


# object: EventListener
class EventListener(TypingT):
    """
        Object event listener.
    """
    def __init__(self):
        # `EventListener`'s type.
        self.type: str = str
        # `EventListener`'s useCapture.
        self.useCapture: bool = bool
        # `EventListener`'s passive flag.
        self.passive: bool = bool
        # `EventListener`'s once flag.
        self.once: bool = bool
        # Script id of the handler code.
        self.scriptId: Runtime.ScriptId = Runtime.ScriptId
        # Line number in the script (0-based).
        self.lineNumber: int = int
        # Column number in the script (0-based).
        self.columnNumber: int = int
        # OPTIONAL, Event handler function value.
        self.handler: Runtime.RemoteObject = Runtime.RemoteObject
        # OPTIONAL, Event original handler function value.
        self.originalHandler: Runtime.RemoteObject = Runtime.RemoteObject
        # OPTIONAL, Node the listener is added to (if any).
        self.backendNodeId: DOM.BackendNodeId = DOM.BackendNodeId


import cdp.DOM as DOM
import cdp.Debugger as Debugger
import cdp.Runtime as Runtime
# ================================================================================
# DOMDebugger Domain.
# ================================================================================
class DOMDebugger(DomainT):
    """
        DOM debugging allows setting breakpoints on particular DOM operations and events. JavaScript
        execution will stop on these operations as if there was a regular breakpoint set.
    """
    def __init__(self, drv):
        self.drv = drv


    # return: getEventListenersReturn
    class getEventListenersReturn(ReturnT):
        def __init__(self):
            # Array of relevant listeners.
            self.listeners: List[EventListener] = [EventListener]


    # func: getEventListeners
    def getEventListeners(self,objectId:Runtime.RemoteObjectId, depth:int=None, pierce:bool=None) -> getEventListenersReturn:
        """
            Returns event listeners of the given object.
        Params:
            1. objectId: Runtime.RemoteObjectId
                Identifier of the object to return listeners for.
            2. depth: int (OPTIONAL)
                The maximum depth at which Node children should be retrieved, defaults to 1. Use -1 for theentire subtree or provide an integer larger than 0.
            3. pierce: bool (OPTIONAL)
                Whether or not iframes and shadow roots should be traversed when returning the subtree(default is false). Reports listeners for all contexts if pierce is enabled.
        Return: getEventListenersReturn
        """
        return self.drv.call(DOMDebugger.getEventListenersReturn,'DOMDebugger.getEventListeners',objectId=objectId, depth=depth, pierce=pierce)


    # func: removeDOMBreakpoint
    def removeDOMBreakpoint(self,nodeId:DOM.NodeId, type:DOMBreakpointType):
        """
            Removes DOM breakpoint that was set using `setDOMBreakpoint`.
        Params:
            1. nodeId: DOM.NodeId
                Identifier of the node to remove breakpoint from.
            2. type: DOMBreakpointType
                Type of the breakpoint to remove.
        """
        return self.drv.call(None,'DOMDebugger.removeDOMBreakpoint',nodeId=nodeId, type=type)


    # func: removeEventListenerBreakpoint
    def removeEventListenerBreakpoint(self,eventName:str, targetName:str=None):
        """
            Removes breakpoint on particular DOM event.
        Params:
            1. eventName: str
                Event name.
            2. targetName: str (OPTIONAL)
                EventTarget interface name.
        """
        return self.drv.call(None,'DOMDebugger.removeEventListenerBreakpoint',eventName=eventName, targetName=targetName)


    # func: removeInstrumentationBreakpoint
    def removeInstrumentationBreakpoint(self,eventName:str):
        """
            Removes breakpoint on particular native event.
        Params:
            1. eventName: str
                Instrumentation name to stop on.
        """
        return self.drv.call(None,'DOMDebugger.removeInstrumentationBreakpoint',eventName=eventName)


    # func: removeXHRBreakpoint
    def removeXHRBreakpoint(self,url:str):
        """
            Removes breakpoint from XMLHttpRequest.
        Params:
            1. url: str
                Resource URL substring.
        """
        return self.drv.call(None,'DOMDebugger.removeXHRBreakpoint',url=url)


    # func: setDOMBreakpoint
    def setDOMBreakpoint(self,nodeId:DOM.NodeId, type:DOMBreakpointType):
        """
            Sets breakpoint on particular operation with DOM.
        Params:
            1. nodeId: DOM.NodeId
                Identifier of the node to set breakpoint on.
            2. type: DOMBreakpointType
                Type of the operation to stop upon.
        """
        return self.drv.call(None,'DOMDebugger.setDOMBreakpoint',nodeId=nodeId, type=type)


    # func: setEventListenerBreakpoint
    def setEventListenerBreakpoint(self,eventName:str, targetName:str=None):
        """
            Sets breakpoint on particular DOM event.
        Params:
            1. eventName: str
                DOM Event name to stop on (any DOM event will do).
            2. targetName: str (OPTIONAL)
                EventTarget interface name to stop on. If equal to `"*"` or not provided, will stop on anyEventTarget.
        """
        return self.drv.call(None,'DOMDebugger.setEventListenerBreakpoint',eventName=eventName, targetName=targetName)


    # func: setInstrumentationBreakpoint
    def setInstrumentationBreakpoint(self,eventName:str):
        """
            Sets breakpoint on particular native event.
        Params:
            1. eventName: str
                Instrumentation name to stop on.
        """
        return self.drv.call(None,'DOMDebugger.setInstrumentationBreakpoint',eventName=eventName)


    # func: setXHRBreakpoint
    def setXHRBreakpoint(self,url:str):
        """
            Sets breakpoint on XMLHttpRequest.
        Params:
            1. url: str
                Resource URL substring. All XHRs having this substring in the URL will get stopped upon.
        """
        return self.drv.call(None,'DOMDebugger.setXHRBreakpoint',url=url)



