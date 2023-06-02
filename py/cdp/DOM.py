"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: Unique DOM node identifier.
NodeId = int


# typing: Unique DOM node identifier used to reference a node that may not have been pushed to thefront-end.
BackendNodeId = int


# object: BackendNode
class BackendNode(TypingT):
    """
        Backend node with a friendly name.
    """
    def __init__(self):
        # `Node`'s nodeType.
        self.nodeType: int = int
        # `Node`'s nodeName.
        self.nodeName: str = str
        # backendNodeId
        self.backendNodeId: BackendNodeId = BackendNodeId


# typing: Pseudo element type.
PseudoType = str
PseudoTypeEnums = ['first-line', 'first-letter', 'before', 'after', 'marker', 'backdrop', 'selection', 'first-line-inherited', 'scrollbar', 'scrollbar-thumb', 'scrollbar-button', 'scrollbar-track', 'scrollbar-track-piece', 'scrollbar-corner', 'resizer', 'input-list-button']


# typing: Shadow root type.
ShadowRootType = str
ShadowRootTypeEnums = ['user-agent', 'open', 'closed']


# object: Node
class Node(TypingT):
    """
        DOM interaction is implemented in terms of mirror objects that represent the actual DOM nodes.
        DOMNode is a base node mirror type.
    """
    def __init__(self):
        # Node identifier that is passed into the rest of the DOM messages as the `nodeId`. Backendwill only push node with given `id` once. It is aware of all requested nodes and will onlyfire DOM events for nodes known to the client.
        self.nodeId: NodeId = NodeId
        # OPTIONAL, The id of the parent node if any.
        self.parentId: NodeId = NodeId
        # The BackendNodeId for this node.
        self.backendNodeId: BackendNodeId = BackendNodeId
        # `Node`'s nodeType.
        self.nodeType: int = int
        # `Node`'s nodeName.
        self.nodeName: str = str
        # `Node`'s localName.
        self.localName: str = str
        # `Node`'s nodeValue.
        self.nodeValue: str = str
        # OPTIONAL, Child count for `Container` nodes.
        self.childNodeCount: int = int
        # OPTIONAL, Child nodes of this node when requested with children.
        self.children: List[Node] = [Node]
        # OPTIONAL, Attributes of the `Element` node in the form of flat array `[name1, value1, name2, value2]`.
        self.attributes: List[str] = [str]
        # OPTIONAL, Document URL that `Document` or `FrameOwner` node points to.
        self.documentURL: str = str
        # OPTIONAL, Base URL that `Document` or `FrameOwner` node uses for URL completion.
        self.baseURL: str = str
        # OPTIONAL, `DocumentType`'s publicId.
        self.publicId: str = str
        # OPTIONAL, `DocumentType`'s systemId.
        self.systemId: str = str
        # OPTIONAL, `DocumentType`'s internalSubset.
        self.internalSubset: str = str
        # OPTIONAL, `Document`'s XML version in case of XML documents.
        self.xmlVersion: str = str
        # OPTIONAL, `Attr`'s name.
        self.name: str = str
        # OPTIONAL, `Attr`'s value.
        self.value: str = str
        # OPTIONAL, Pseudo element type for this node.
        self.pseudoType: PseudoType = PseudoType
        # OPTIONAL, Shadow root type.
        self.shadowRootType: ShadowRootType = ShadowRootType
        # OPTIONAL, Frame ID for frame owner elements.
        self.frameId: Page.FrameId = Page.FrameId
        # OPTIONAL, Content document for frame owner elements.
        self.contentDocument: Node = Node
        # OPTIONAL, Shadow root list for given element host.
        self.shadowRoots: List[Node] = [Node]
        # OPTIONAL, Content document fragment for template elements.
        self.templateContent: Node = Node
        # OPTIONAL, Pseudo elements associated with this node.
        self.pseudoElements: List[Node] = [Node]
        # OPTIONAL, Import document for the HTMLImport links.
        self.importedDocument: Node = Node
        # OPTIONAL, Distributed nodes for given insertion point.
        self.distributedNodes: List[BackendNode] = [BackendNode]
        # OPTIONAL, Whether the node is SVG.
        self.isSVG: bool = bool


# object: RGBA
class RGBA(TypingT):
    """
        A structure holding an RGBA color.
    """
    def __init__(self):
        # The red component, in the [0-255] range.
        self.r: int = int
        # The green component, in the [0-255] range.
        self.g: int = int
        # The blue component, in the [0-255] range.
        self.b: int = int
        # OPTIONAL, The alpha component, in the [0-1] range (default: 1).
        self.a: int = int


# typing: An array of quad vertices, x immediately followed by y for each point, points clock-wise.
Quad = List[int]


# object: BoxModel
class BoxModel(TypingT):
    """
        Box model.
    """
    def __init__(self):
        # Content box
        self.content: Quad = Quad
        # Padding box
        self.padding: Quad = Quad
        # Border box
        self.border: Quad = Quad
        # Margin box
        self.margin: Quad = Quad
        # Node width
        self.width: int = int
        # Node height
        self.height: int = int
        # OPTIONAL, Shape outside coordinates
        self.shapeOutside: ShapeOutsideInfo = ShapeOutsideInfo


# object: ShapeOutsideInfo
class ShapeOutsideInfo(TypingT):
    """
        CSS Shape Outside details.
    """
    def __init__(self):
        # Shape bounds
        self.bounds: Quad = Quad
        # Shape coordinate details
        self.shape: List[str] = [str]
        # Margin shape bounds
        self.marginShape: List[str] = [str]


# object: Rect
class Rect(TypingT):
    """
        Rectangle.
    """
    def __init__(self):
        # X coordinate
        self.x: int = int
        # Y coordinate
        self.y: int = int
        # Rectangle width
        self.width: int = int
        # Rectangle height
        self.height: int = int


# object: CSSComputedStyleProperty
class CSSComputedStyleProperty(TypingT):
    """
        CSSComputedStyleProperty
    """
    def __init__(self):
        # Computed style property name.
        self.name: str = str
        # Computed style property value.
        self.value: str = str


# event: attributeModified
class attributeModified(EventT):
    """
        Fired when `Element`'s attribute is modified.
    """
    event="DOM.attributeModified"
    def __init__(self):
        # Id of the node that has changed.
        self.nodeId: NodeId = NodeId
        # Attribute name.
        self.name: str = str
        # Attribute value.
        self.value: str = str


# event: attributeRemoved
class attributeRemoved(EventT):
    """
        Fired when `Element`'s attribute is removed.
    """
    event="DOM.attributeRemoved"
    def __init__(self):
        # Id of the node that has changed.
        self.nodeId: NodeId = NodeId
        # A ttribute name.
        self.name: str = str


# event: characterDataModified
class characterDataModified(EventT):
    """
        Mirrors `DOMCharacterDataModified` event.
    """
    event="DOM.characterDataModified"
    def __init__(self):
        # Id of the node that has changed.
        self.nodeId: NodeId = NodeId
        # New text value.
        self.characterData: str = str


# event: childNodeCountUpdated
class childNodeCountUpdated(EventT):
    """
        Fired when `Container`'s child node count has changed.
    """
    event="DOM.childNodeCountUpdated"
    def __init__(self):
        # Id of the node that has changed.
        self.nodeId: NodeId = NodeId
        # New node count.
        self.childNodeCount: int = int


# event: childNodeInserted
class childNodeInserted(EventT):
    """
        Mirrors `DOMNodeInserted` event.
    """
    event="DOM.childNodeInserted"
    def __init__(self):
        # Id of the node that has changed.
        self.parentNodeId: NodeId = NodeId
        # If of the previous siblint.
        self.previousNodeId: NodeId = NodeId
        # Inserted node data.
        self.node: Node = Node


# event: childNodeRemoved
class childNodeRemoved(EventT):
    """
        Mirrors `DOMNodeRemoved` event.
    """
    event="DOM.childNodeRemoved"
    def __init__(self):
        # Parent id.
        self.parentNodeId: NodeId = NodeId
        # Id of the node that has been removed.
        self.nodeId: NodeId = NodeId


# event: distributedNodesUpdated
class distributedNodesUpdated(EventT):
    """
        Called when distrubution is changed.
    """
    event="DOM.distributedNodesUpdated"
    def __init__(self):
        # Insertion point where distrubuted nodes were updated.
        self.insertionPointId: NodeId = NodeId
        # Distributed nodes for given insertion point.
        self.distributedNodes: List[BackendNode] = [BackendNode]


# event: documentUpdated
class documentUpdated(EventT):
    """
        Fired when `Document` has been totally updated. Node ids are no longer valid.
    """
    event="DOM.documentUpdated"
    def __init__(self):
        pass


# event: inlineStyleInvalidated
class inlineStyleInvalidated(EventT):
    """
        Fired when `Element`'s inline style is modified via a CSS property modification.
    """
    event="DOM.inlineStyleInvalidated"
    def __init__(self):
        # Ids of the nodes for which the inline styles have been invalidated.
        self.nodeIds: List[NodeId] = [NodeId]


# event: pseudoElementAdded
class pseudoElementAdded(EventT):
    """
        Called when a pseudo element is added to an element.
    """
    event="DOM.pseudoElementAdded"
    def __init__(self):
        # Pseudo element's parent element id.
        self.parentId: NodeId = NodeId
        # The added pseudo element.
        self.pseudoElement: Node = Node


# event: pseudoElementRemoved
class pseudoElementRemoved(EventT):
    """
        Called when a pseudo element is removed from an element.
    """
    event="DOM.pseudoElementRemoved"
    def __init__(self):
        # Pseudo element's parent element id.
        self.parentId: NodeId = NodeId
        # The removed pseudo element id.
        self.pseudoElementId: NodeId = NodeId


# event: setChildNodes
class setChildNodes(EventT):
    """
        Fired when backend wants to provide client with the missing DOM structure. This happens upon
        most of the calls requesting node ids.
    """
    event="DOM.setChildNodes"
    def __init__(self):
        # Parent node id to populate with children.
        self.parentId: NodeId = NodeId
        # Child nodes array.
        self.nodes: List[Node] = [Node]


# event: shadowRootPopped
class shadowRootPopped(EventT):
    """
        Called when shadow root is popped from the element.
    """
    event="DOM.shadowRootPopped"
    def __init__(self):
        # Host element id.
        self.hostId: NodeId = NodeId
        # Shadow root id.
        self.rootId: NodeId = NodeId


# event: shadowRootPushed
class shadowRootPushed(EventT):
    """
        Called when shadow root is pushed into the element.
    """
    event="DOM.shadowRootPushed"
    def __init__(self):
        # Host element id.
        self.hostId: NodeId = NodeId
        # Shadow root.
        self.root: Node = Node


import cdp.Runtime as Runtime
import cdp.Page as Page
# ================================================================================
# DOM Domain.
# ================================================================================
class DOM(DomainT):
    """
        This domain exposes DOM read/write operations. Each DOM Node is represented with its mirror object
        that has an `id`. This `id` can be used to get additional information on the Node, resolve it into
        the JavaScript object wrapper, etc. It is important that client receives DOM events only for the
        nodes that are known to the client. Backend keeps track of the nodes that were sent to the client
        and never sends the same node twice. It is client's responsibility to collect information about
        the nodes that were sent to the client.<p>Note that `iframe` owner elements will return
        corresponding document elements as their child nodes.</p>
    """
    def __init__(self, drv):
        self.drv = drv


    # return: collectClassNamesFromSubtreeReturn
    class collectClassNamesFromSubtreeReturn(ReturnT):
        def __init__(self):
            # Class name list.
            self.classNames: List[str] = [str]


    # func: collectClassNamesFromSubtree
    def collectClassNamesFromSubtree(self,nodeId:NodeId, **kwargs) -> collectClassNamesFromSubtreeReturn:
        """
            Collects class names for the node with given id and all of it's child nodes.
        Params:
            1. nodeId: NodeId
                Id of the node to collect class names.
        Return: collectClassNamesFromSubtreeReturn
        """
        return self.drv.call(DOM.collectClassNamesFromSubtreeReturn,'DOM.collectClassNamesFromSubtree',nodeId=nodeId, **kwargs)


    # return: copyToReturn
    class copyToReturn(ReturnT):
        def __init__(self):
            # Id of the node clone.
            self.nodeId: NodeId = NodeId


    # func: copyTo
    def copyTo(self,nodeId:NodeId, targetNodeId:NodeId, insertBeforeNodeId:NodeId=None, **kwargs) -> copyToReturn:
        """
            Creates a deep copy of the specified node and places it into the target container before the
            given anchor.
        Params:
            1. nodeId: NodeId
                Id of the node to copy.
            2. targetNodeId: NodeId
                Id of the element to drop the copy into.
            3. insertBeforeNodeId: NodeId (OPTIONAL)
                Drop the copy before this node (if absent, the copy becomes the last child of`targetNodeId`).
        Return: copyToReturn
        """
        return self.drv.call(DOM.copyToReturn,'DOM.copyTo',nodeId=nodeId, targetNodeId=targetNodeId, insertBeforeNodeId=insertBeforeNodeId, **kwargs)


    # return: describeNodeReturn
    class describeNodeReturn(ReturnT):
        def __init__(self):
            # Node description.
            self.node: Node = Node


    # func: describeNode
    def describeNode(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, depth:int=None, pierce:bool=None, **kwargs) -> describeNodeReturn:
        """
            Describes node given its id, does not require domain to be enabled. Does not start tracking any
            objects, can be used for automation.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            3. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
            4. depth: int (OPTIONAL)
                The maximum depth at which children should be retrieved, defaults to 1. Use -1 for theentire subtree or provide an integer larger than 0.
            5. pierce: bool (OPTIONAL)
                Whether or not iframes and shadow roots should be traversed when returning the subtree(default is false).
        Return: describeNodeReturn
        """
        return self.drv.call(DOM.describeNodeReturn,'DOM.describeNode',nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, depth=depth, pierce=pierce, **kwargs)


    # func: scrollIntoViewIfNeeded
    def scrollIntoViewIfNeeded(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, rect:Rect=None, **kwargs):
        """
            Scrolls the specified rect of the given node into view if not already visible.
            Note: exactly one between nodeId, backendNodeId and objectId should be passed
            to identify the node.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            3. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
            4. rect: Rect (OPTIONAL)
                The rect to be scrolled into view, relative to the node's border box, in CSS pixels.When omitted, center of the node will be used, similar to Element.scrollIntoView.
        """
        return self.drv.call(None,'DOM.scrollIntoViewIfNeeded',nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, rect=rect, **kwargs)


    # func: disable
    def disable(self,**kwargs):
        """
            Disables DOM agent for the given page.
        """
        return self.drv.call(None,'DOM.disable',**kwargs)


    # func: discardSearchResults
    def discardSearchResults(self,searchId:str, **kwargs):
        """
            Discards search results from the session with the given id. `getSearchResults` should no longer
            be called for that search.
        Params:
            1. searchId: str
                Unique search session identifier.
        """
        return self.drv.call(None,'DOM.discardSearchResults',searchId=searchId, **kwargs)


    # func: enable
    def enable(self,**kwargs):
        """
            Enables DOM agent for the given page.
        """
        return self.drv.call(None,'DOM.enable',**kwargs)


    # func: focus
    def focus(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, **kwargs):
        """
            Focuses the given element.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            3. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
        """
        return self.drv.call(None,'DOM.focus',nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, **kwargs)


    # return: getAttributesReturn
    class getAttributesReturn(ReturnT):
        def __init__(self):
            # An interleaved array of node attribute names and values.
            self.attributes: List[str] = [str]


    # func: getAttributes
    def getAttributes(self,nodeId:NodeId, **kwargs) -> getAttributesReturn:
        """
            Returns attributes for the specified node.
        Params:
            1. nodeId: NodeId
                Id of the node to retrieve attibutes for.
        Return: getAttributesReturn
        """
        return self.drv.call(DOM.getAttributesReturn,'DOM.getAttributes',nodeId=nodeId, **kwargs)


    # return: getBoxModelReturn
    class getBoxModelReturn(ReturnT):
        def __init__(self):
            # Box model for the node.
            self.model: BoxModel = BoxModel


    # func: getBoxModel
    def getBoxModel(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, **kwargs) -> getBoxModelReturn:
        """
            Returns boxes for the given node.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            3. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
        Return: getBoxModelReturn
        """
        return self.drv.call(DOM.getBoxModelReturn,'DOM.getBoxModel',nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, **kwargs)


    # return: getContentQuadsReturn
    class getContentQuadsReturn(ReturnT):
        def __init__(self):
            # Quads that describe node layout relative to viewport.
            self.quads: List[Quad] = [Quad]


    # func: getContentQuads
    def getContentQuads(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, **kwargs) -> getContentQuadsReturn:
        """
            Returns quads that describe node position on the page. This method
            might return multiple quads for inline nodes.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            3. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
        Return: getContentQuadsReturn
        """
        return self.drv.call(DOM.getContentQuadsReturn,'DOM.getContentQuads',nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, **kwargs)


    # return: getDocumentReturn
    class getDocumentReturn(ReturnT):
        def __init__(self):
            # Resulting node.
            self.root: Node = Node


    # func: getDocument
    def getDocument(self,depth:int=None, pierce:bool=None, **kwargs) -> getDocumentReturn:
        """
            Returns the root DOM node (and optionally the subtree) to the caller.
        Params:
            1. depth: int (OPTIONAL)
                The maximum depth at which children should be retrieved, defaults to 1. Use -1 for theentire subtree or provide an integer larger than 0.
            2. pierce: bool (OPTIONAL)
                Whether or not iframes and shadow roots should be traversed when returning the subtree(default is false).
        Return: getDocumentReturn
        """
        return self.drv.call(DOM.getDocumentReturn,'DOM.getDocument',depth=depth, pierce=pierce, **kwargs)


    # return: getFlattenedDocumentReturn
    class getFlattenedDocumentReturn(ReturnT):
        def __init__(self):
            # Resulting node.
            self.nodes: List[Node] = [Node]


    # func: getFlattenedDocument
    def getFlattenedDocument(self,depth:int=None, pierce:bool=None, **kwargs) -> getFlattenedDocumentReturn:
        """
            Returns the root DOM node (and optionally the subtree) to the caller.
            Deprecated, as it is not designed to work well with the rest of the DOM agent.
            Use DOMSnapshot.captureSnapshot instead.
        Params:
            1. depth: int (OPTIONAL)
                The maximum depth at which children should be retrieved, defaults to 1. Use -1 for theentire subtree or provide an integer larger than 0.
            2. pierce: bool (OPTIONAL)
                Whether or not iframes and shadow roots should be traversed when returning the subtree(default is false).
        Return: getFlattenedDocumentReturn
        """
        return self.drv.call(DOM.getFlattenedDocumentReturn,'DOM.getFlattenedDocument',depth=depth, pierce=pierce, **kwargs)


    # return: getNodesForSubtreeByStyleReturn
    class getNodesForSubtreeByStyleReturn(ReturnT):
        def __init__(self):
            # Resulting nodes.
            self.nodeIds: List[NodeId] = [NodeId]


    # func: getNodesForSubtreeByStyle
    def getNodesForSubtreeByStyle(self,nodeId:NodeId, computedStyles:List[CSSComputedStyleProperty], pierce:bool=None, **kwargs) -> getNodesForSubtreeByStyleReturn:
        """
            Finds nodes with a given computed style in a subtree.
        Params:
            1. nodeId: NodeId
                Node ID pointing to the root of a subtree.
            2. computedStyles: List[CSSComputedStyleProperty]
                The style to filter nodes by (includes nodes if any of properties matches).
            3. pierce: bool (OPTIONAL)
                Whether or not iframes and shadow roots in the same target should be traversed when returning theresults (default is false).
        Return: getNodesForSubtreeByStyleReturn
        """
        return self.drv.call(DOM.getNodesForSubtreeByStyleReturn,'DOM.getNodesForSubtreeByStyle',nodeId=nodeId, computedStyles=computedStyles, pierce=pierce, **kwargs)


    # return: getNodeForLocationReturn
    class getNodeForLocationReturn(ReturnT):
        def __init__(self):
            # Resulting node.
            self.backendNodeId: BackendNodeId = BackendNodeId
            # Frame this node belongs to.
            self.frameId: Page.FrameId = Page.FrameId
            # OPTIONAL, Id of the node at given coordinates, only when enabled and requested document.
            self.nodeId: NodeId = NodeId


    # func: getNodeForLocation
    def getNodeForLocation(self,x:int, y:int, includeUserAgentShadowDOM:bool=None, ignorePointerEventsNone:bool=None, **kwargs) -> getNodeForLocationReturn:
        """
            Returns node id at given location. Depending on whether DOM domain is enabled, nodeId is
            either returned or not.
        Params:
            1. x: int
                X coordinate.
            2. y: int
                Y coordinate.
            3. includeUserAgentShadowDOM: bool (OPTIONAL)
                False to skip to the nearest non-UA shadow root ancestor (default: false).
            4. ignorePointerEventsNone: bool (OPTIONAL)
                Whether to ignore pointer-events: none on elements and hit test them.
        Return: getNodeForLocationReturn
        """
        return self.drv.call(DOM.getNodeForLocationReturn,'DOM.getNodeForLocation',x=x, y=y, includeUserAgentShadowDOM=includeUserAgentShadowDOM, ignorePointerEventsNone=ignorePointerEventsNone, **kwargs)


    # return: getOuterHTMLReturn
    class getOuterHTMLReturn(ReturnT):
        def __init__(self):
            # Outer HTML markup.
            self.outerHTML: str = str


    # func: getOuterHTML
    def getOuterHTML(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, **kwargs) -> getOuterHTMLReturn:
        """
            Returns node's HTML markup.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            3. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
        Return: getOuterHTMLReturn
        """
        return self.drv.call(DOM.getOuterHTMLReturn,'DOM.getOuterHTML',nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, **kwargs)


    # return: getRelayoutBoundaryReturn
    class getRelayoutBoundaryReturn(ReturnT):
        def __init__(self):
            # Relayout boundary node id for the given node.
            self.nodeId: NodeId = NodeId


    # func: getRelayoutBoundary
    def getRelayoutBoundary(self,nodeId:NodeId, **kwargs) -> getRelayoutBoundaryReturn:
        """
            Returns the id of the nearest ancestor that is a relayout boundary.
        Params:
            1. nodeId: NodeId
                Id of the node.
        Return: getRelayoutBoundaryReturn
        """
        return self.drv.call(DOM.getRelayoutBoundaryReturn,'DOM.getRelayoutBoundary',nodeId=nodeId, **kwargs)


    # return: getSearchResultsReturn
    class getSearchResultsReturn(ReturnT):
        def __init__(self):
            # Ids of the search result nodes.
            self.nodeIds: List[NodeId] = [NodeId]


    # func: getSearchResults
    def getSearchResults(self,searchId:str, fromIndex:int, toIndex:int, **kwargs) -> getSearchResultsReturn:
        """
            Returns search results from given `fromIndex` to given `toIndex` from the search with the given
            identifier.
        Params:
            1. searchId: str
                Unique search session identifier.
            2. fromIndex: int
                Start index of the search result to be returned.
            3. toIndex: int
                End index of the search result to be returned.
        Return: getSearchResultsReturn
        """
        return self.drv.call(DOM.getSearchResultsReturn,'DOM.getSearchResults',searchId=searchId, fromIndex=fromIndex, toIndex=toIndex, **kwargs)


    # func: hideHighlight
    def hideHighlight(self,**kwargs):
        """
            Hides any highlight.
        """
        return self.drv.call(None,'DOM.hideHighlight',**kwargs)


    # func: highlightNode
    def highlightNode(self,**kwargs):
        """
            Highlights DOM node.
        """
        return self.drv.call(None,'DOM.highlightNode',**kwargs)


    # func: highlightRect
    def highlightRect(self,**kwargs):
        """
            Highlights given rectangle.
        """
        return self.drv.call(None,'DOM.highlightRect',**kwargs)


    # func: markUndoableState
    def markUndoableState(self,**kwargs):
        """
            Marks last undoable state.
        """
        return self.drv.call(None,'DOM.markUndoableState',**kwargs)


    # return: moveToReturn
    class moveToReturn(ReturnT):
        def __init__(self):
            # New id of the moved node.
            self.nodeId: NodeId = NodeId


    # func: moveTo
    def moveTo(self,nodeId:NodeId, targetNodeId:NodeId, insertBeforeNodeId:NodeId=None, **kwargs) -> moveToReturn:
        """
            Moves node into the new container, places it before the given anchor.
        Params:
            1. nodeId: NodeId
                Id of the node to move.
            2. targetNodeId: NodeId
                Id of the element to drop the moved node into.
            3. insertBeforeNodeId: NodeId (OPTIONAL)
                Drop node before this one (if absent, the moved node becomes the last child of`targetNodeId`).
        Return: moveToReturn
        """
        return self.drv.call(DOM.moveToReturn,'DOM.moveTo',nodeId=nodeId, targetNodeId=targetNodeId, insertBeforeNodeId=insertBeforeNodeId, **kwargs)


    # return: performSearchReturn
    class performSearchReturn(ReturnT):
        def __init__(self):
            # Unique search session identifier.
            self.searchId: str = str
            # Number of search results.
            self.resultCount: int = int


    # func: performSearch
    def performSearch(self,query:str, includeUserAgentShadowDOM:bool=None, **kwargs) -> performSearchReturn:
        """
            Searches for a given string in the DOM tree. Use `getSearchResults` to access search results or
            `cancelSearch` to end this search session.
        Params:
            1. query: str
                Plain text or query selector or XPath search query.
            2. includeUserAgentShadowDOM: bool (OPTIONAL)
                True to search in user agent shadow DOM.
        Return: performSearchReturn
        """
        return self.drv.call(DOM.performSearchReturn,'DOM.performSearch',query=query, includeUserAgentShadowDOM=includeUserAgentShadowDOM, **kwargs)


    # return: pushNodeByPathToFrontendReturn
    class pushNodeByPathToFrontendReturn(ReturnT):
        def __init__(self):
            # Id of the node for given path.
            self.nodeId: NodeId = NodeId


    # func: pushNodeByPathToFrontend
    def pushNodeByPathToFrontend(self,path:str, **kwargs) -> pushNodeByPathToFrontendReturn:
        """
            Requests that the node is sent to the caller given its path. // FIXME, use XPath
        Params:
            1. path: str
                Path to node in the proprietary format.
        Return: pushNodeByPathToFrontendReturn
        """
        return self.drv.call(DOM.pushNodeByPathToFrontendReturn,'DOM.pushNodeByPathToFrontend',path=path, **kwargs)


    # return: pushNodesByBackendIdsToFrontendReturn
    class pushNodesByBackendIdsToFrontendReturn(ReturnT):
        def __init__(self):
            # The array of ids of pushed nodes that correspond to the backend ids specified inbackendNodeIds.
            self.nodeIds: List[NodeId] = [NodeId]


    # func: pushNodesByBackendIdsToFrontend
    def pushNodesByBackendIdsToFrontend(self,backendNodeIds:List[BackendNodeId], **kwargs) -> pushNodesByBackendIdsToFrontendReturn:
        """
            Requests that a batch of nodes is sent to the caller given their backend node ids.
        Params:
            1. backendNodeIds: List[BackendNodeId]
                The array of backend node ids.
        Return: pushNodesByBackendIdsToFrontendReturn
        """
        return self.drv.call(DOM.pushNodesByBackendIdsToFrontendReturn,'DOM.pushNodesByBackendIdsToFrontend',backendNodeIds=backendNodeIds, **kwargs)


    # return: querySelectorReturn
    class querySelectorReturn(ReturnT):
        def __init__(self):
            # Query selector result.
            self.nodeId: NodeId = NodeId


    # func: querySelector
    def querySelector(self,nodeId:NodeId, selector:str, **kwargs) -> querySelectorReturn:
        """
            Executes `querySelector` on a given node.
        Params:
            1. nodeId: NodeId
                Id of the node to query upon.
            2. selector: str
                Selector string.
        Return: querySelectorReturn
        """
        return self.drv.call(DOM.querySelectorReturn,'DOM.querySelector',nodeId=nodeId, selector=selector, **kwargs)


    # return: querySelectorAllReturn
    class querySelectorAllReturn(ReturnT):
        def __init__(self):
            # Query selector result.
            self.nodeIds: List[NodeId] = [NodeId]


    # func: querySelectorAll
    def querySelectorAll(self,nodeId:NodeId, selector:str, **kwargs) -> querySelectorAllReturn:
        """
            Executes `querySelectorAll` on a given node.
        Params:
            1. nodeId: NodeId
                Id of the node to query upon.
            2. selector: str
                Selector string.
        Return: querySelectorAllReturn
        """
        return self.drv.call(DOM.querySelectorAllReturn,'DOM.querySelectorAll',nodeId=nodeId, selector=selector, **kwargs)


    # func: redo
    def redo(self,**kwargs):
        """
            Re-does the last undone action.
        """
        return self.drv.call(None,'DOM.redo',**kwargs)


    # func: removeAttribute
    def removeAttribute(self,nodeId:NodeId, name:str, **kwargs):
        """
            Removes attribute with given name from an element with given id.
        Params:
            1. nodeId: NodeId
                Id of the element to remove attribute from.
            2. name: str
                Name of the attribute to remove.
        """
        return self.drv.call(None,'DOM.removeAttribute',nodeId=nodeId, name=name, **kwargs)


    # func: removeNode
    def removeNode(self,nodeId:NodeId, **kwargs):
        """
            Removes node with given id.
        Params:
            1. nodeId: NodeId
                Id of the node to remove.
        """
        return self.drv.call(None,'DOM.removeNode',nodeId=nodeId, **kwargs)


    # func: requestChildNodes
    def requestChildNodes(self,nodeId:NodeId, depth:int=None, pierce:bool=None, **kwargs):
        """
            Requests that children of the node with given id are returned to the caller in form of
            `setChildNodes` events where not only immediate children are retrieved, but all children down to
            the specified depth.
        Params:
            1. nodeId: NodeId
                Id of the node to get children for.
            2. depth: int (OPTIONAL)
                The maximum depth at which children should be retrieved, defaults to 1. Use -1 for theentire subtree or provide an integer larger than 0.
            3. pierce: bool (OPTIONAL)
                Whether or not iframes and shadow roots should be traversed when returning the sub-tree(default is false).
        """
        return self.drv.call(None,'DOM.requestChildNodes',nodeId=nodeId, depth=depth, pierce=pierce, **kwargs)


    # return: requestNodeReturn
    class requestNodeReturn(ReturnT):
        def __init__(self):
            # Node id for given object.
            self.nodeId: NodeId = NodeId


    # func: requestNode
    def requestNode(self,objectId:Runtime.RemoteObjectId, **kwargs) -> requestNodeReturn:
        """
            Requests that the node is sent to the caller given the JavaScript node object reference. All
            nodes that form the path from the node to the root are also sent to the client as a series of
            `setChildNodes` notifications.
        Params:
            1. objectId: Runtime.RemoteObjectId
                JavaScript object id to convert into node.
        Return: requestNodeReturn
        """
        return self.drv.call(DOM.requestNodeReturn,'DOM.requestNode',objectId=objectId, **kwargs)


    # return: resolveNodeReturn
    class resolveNodeReturn(ReturnT):
        def __init__(self):
            # JavaScript object wrapper for given node.
            self.object: Runtime.RemoteObject = Runtime.RemoteObject


    # func: resolveNode
    def resolveNode(self,nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectGroup:str=None, executionContextId:Runtime.ExecutionContextId=None, **kwargs) -> resolveNodeReturn:
        """
            Resolves the JavaScript node object for a given NodeId or BackendNodeId.
        Params:
            1. nodeId: NodeId (OPTIONAL)
                Id of the node to resolve.
            2. backendNodeId: BackendNodeId (OPTIONAL)
                Backend identifier of the node to resolve.
            3. objectGroup: str (OPTIONAL)
                Symbolic group name that can be used to release multiple objects.
            4. executionContextId: Runtime.ExecutionContextId (OPTIONAL)
                Execution context in which to resolve the node.
        Return: resolveNodeReturn
        """
        return self.drv.call(DOM.resolveNodeReturn,'DOM.resolveNode',nodeId=nodeId, backendNodeId=backendNodeId, objectGroup=objectGroup, executionContextId=executionContextId, **kwargs)


    # func: setAttributeValue
    def setAttributeValue(self,nodeId:NodeId, name:str, value:str, **kwargs):
        """
            Sets attribute for an element with given id.
        Params:
            1. nodeId: NodeId
                Id of the element to set attribute for.
            2. name: str
                Attribute name.
            3. value: str
                Attribute value.
        """
        return self.drv.call(None,'DOM.setAttributeValue',nodeId=nodeId, name=name, value=value, **kwargs)


    # func: setAttributesAsText
    def setAttributesAsText(self,nodeId:NodeId, text:str, name:str=None, **kwargs):
        """
            Sets attributes on element with given id. This method is useful when user edits some existing
            attribute value and types in several attribute name/value pairs.
        Params:
            1. nodeId: NodeId
                Id of the element to set attributes for.
            2. text: str
                Text with a number of attributes. Will parse this text using HTML parser.
            3. name: str (OPTIONAL)
                Attribute name to replace with new attributes derived from text in case text parsedsuccessfully.
        """
        return self.drv.call(None,'DOM.setAttributesAsText',nodeId=nodeId, text=text, name=name, **kwargs)


    # func: setFileInputFiles
    def setFileInputFiles(self,files:List[str], nodeId:NodeId=None, backendNodeId:BackendNodeId=None, objectId:Runtime.RemoteObjectId=None, **kwargs):
        """
            Sets files for the given file input element.
        Params:
            1. files: List[str]
                Array of file paths to set.
            2. nodeId: NodeId (OPTIONAL)
                Identifier of the node.
            3. backendNodeId: BackendNodeId (OPTIONAL)
                Identifier of the backend node.
            4. objectId: Runtime.RemoteObjectId (OPTIONAL)
                JavaScript object id of the node wrapper.
        """
        return self.drv.call(None,'DOM.setFileInputFiles',files=files, nodeId=nodeId, backendNodeId=backendNodeId, objectId=objectId, **kwargs)


    # func: setNodeStackTracesEnabled
    def setNodeStackTracesEnabled(self,enable:bool, **kwargs):
        """
            Sets if stack traces should be captured for Nodes. See `Node.getNodeStackTraces`. Default is disabled.
        Params:
            1. enable: bool
                Enable or disable.
        """
        return self.drv.call(None,'DOM.setNodeStackTracesEnabled',enable=enable, **kwargs)


    # return: getNodeStackTracesReturn
    class getNodeStackTracesReturn(ReturnT):
        def __init__(self):
            # OPTIONAL, Creation stack trace, if available.
            self.creation: Runtime.StackTrace = Runtime.StackTrace


    # func: getNodeStackTraces
    def getNodeStackTraces(self,nodeId:NodeId, **kwargs) -> getNodeStackTracesReturn:
        """
            Gets stack traces associated with a Node. As of now, only provides stack trace for Node creation.
        Params:
            1. nodeId: NodeId
                Id of the node to get stack traces for.
        Return: getNodeStackTracesReturn
        """
        return self.drv.call(DOM.getNodeStackTracesReturn,'DOM.getNodeStackTraces',nodeId=nodeId, **kwargs)


    # return: getFileInfoReturn
    class getFileInfoReturn(ReturnT):
        def __init__(self):
            # path
            self.path: str = str


    # func: getFileInfo
    def getFileInfo(self,objectId:Runtime.RemoteObjectId, **kwargs) -> getFileInfoReturn:
        """
            Returns file information for the given
            File wrapper.
        Params:
            1. objectId: Runtime.RemoteObjectId
                JavaScript object id of the node wrapper.
        Return: getFileInfoReturn
        """
        return self.drv.call(DOM.getFileInfoReturn,'DOM.getFileInfo',objectId=objectId, **kwargs)


    # func: setInspectedNode
    def setInspectedNode(self,nodeId:NodeId, **kwargs):
        """
            Enables console to refer to the node with given id via $x (see Command Line API for more details
            $x functions).
        Params:
            1. nodeId: NodeId
                DOM node id to be accessible by means of $x command line API.
        """
        return self.drv.call(None,'DOM.setInspectedNode',nodeId=nodeId, **kwargs)


    # return: setNodeNameReturn
    class setNodeNameReturn(ReturnT):
        def __init__(self):
            # New node's id.
            self.nodeId: NodeId = NodeId


    # func: setNodeName
    def setNodeName(self,nodeId:NodeId, name:str, **kwargs) -> setNodeNameReturn:
        """
            Sets node name for a node with given id.
        Params:
            1. nodeId: NodeId
                Id of the node to set name for.
            2. name: str
                New node's name.
        Return: setNodeNameReturn
        """
        return self.drv.call(DOM.setNodeNameReturn,'DOM.setNodeName',nodeId=nodeId, name=name, **kwargs)


    # func: setNodeValue
    def setNodeValue(self,nodeId:NodeId, value:str, **kwargs):
        """
            Sets node value for a node with given id.
        Params:
            1. nodeId: NodeId
                Id of the node to set value for.
            2. value: str
                New node's value.
        """
        return self.drv.call(None,'DOM.setNodeValue',nodeId=nodeId, value=value, **kwargs)


    # func: setOuterHTML
    def setOuterHTML(self,nodeId:NodeId, outerHTML:str, **kwargs):
        """
            Sets node HTML markup, returns new node id.
        Params:
            1. nodeId: NodeId
                Id of the node to set markup for.
            2. outerHTML: str
                Outer HTML markup to set.
        """
        return self.drv.call(None,'DOM.setOuterHTML',nodeId=nodeId, outerHTML=outerHTML, **kwargs)


    # func: undo
    def undo(self,**kwargs):
        """
            Undoes the last performed action.
        """
        return self.drv.call(None,'DOM.undo',**kwargs)


    # return: getFrameOwnerReturn
    class getFrameOwnerReturn(ReturnT):
        def __init__(self):
            # Resulting node.
            self.backendNodeId: BackendNodeId = BackendNodeId
            # OPTIONAL, Id of the node at given coordinates, only when enabled and requested document.
            self.nodeId: NodeId = NodeId


    # func: getFrameOwner
    def getFrameOwner(self,frameId:Page.FrameId, **kwargs) -> getFrameOwnerReturn:
        """
            Returns iframe node that owns iframe with the given domain.
        Params:
            1. frameId: Page.FrameId
        Return: getFrameOwnerReturn
        """
        return self.drv.call(DOM.getFrameOwnerReturn,'DOM.getFrameOwner',frameId=frameId, **kwargs)



