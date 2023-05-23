"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# typing: This is either obtained from another method or specifed as `blob:&lt;uuid&gt;` where`&lt;uuid&gt` is an UUID of a Blob.
StreamHandle = str


import cdp.Runtime as Runtime
# ================================================================================
# IO Domain.
# ================================================================================
class IO(DomainT):
    """
        Input/Output operations for streams produced by DevTools.
    """
    def __init__(self, drv):
        self.drv = drv


    # func: close
    def close(self,handle:StreamHandle):
        """
            Close the stream, discard any temporary backing storage.
        Params:
            1. handle: StreamHandle
                Handle of the stream to close.
        """
        return self.drv.call(None,'IO.close',handle=handle)


    # return: readReturn
    class readReturn(ReturnT):
        def __init__(self):
            # OPTIONAL, Set if the data is base64-encoded
            self.base64Encoded: bool = bool
            # Data that were read.
            self.data: str = str
            # Set if the end-of-file condition occured while reading.
            self.eof: bool = bool


    # func: read
    def read(self,handle:StreamHandle, offset:int=None, size:int=None) -> readReturn:
        """
            Read a chunk of the stream
        Params:
            1. handle: StreamHandle
                Handle of the stream to read.
            2. offset: int (OPTIONAL)
                Seek to the specified offset before reading (if not specificed, proceed with offsetfollowing the last read). Some types of streams may only support sequential reads.
            3. size: int (OPTIONAL)
                Maximum number of bytes to read (left upon the agent discretion if not specified).
        Return: readReturn
        """
        return self.drv.call(IO.readReturn,'IO.read',handle=handle, offset=offset, size=size)


    # return: resolveBlobReturn
    class resolveBlobReturn(ReturnT):
        def __init__(self):
            # UUID of the specified Blob.
            self.uuid: str = str


    # func: resolveBlob
    def resolveBlob(self,objectId:Runtime.RemoteObjectId) -> resolveBlobReturn:
        """
            Return UUID of Blob object specified by a remote object id.
        Params:
            1. objectId: Runtime.RemoteObjectId
                Object id of a Blob object wrapper.
        Return: resolveBlobReturn
        """
        return self.drv.call(IO.resolveBlobReturn,'IO.resolveBlob',objectId=objectId)



