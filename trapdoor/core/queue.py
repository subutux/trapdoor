"""
The queue manager for trapdoor.

If a trap is recieved, it's added to this
queue for processing. The queue is based on
Janus, a sync & async queue. This allows
us to execute queue items as sync, but add the tasks
in async.
"""

import janus
import asyncio
MAX_WORKERS = 0 #Infinite
loop = asyncio.get_event_loop()
Queue = janus.Queue(loop=loop,maxsize=MAX_WORKERS)

class Action(object):
    """
    An action is a worker in the Queue. Executing the Filter
    & handler.
    """
    
    def __init__(self,Filter,Q):
        self._Filter = Filter
        self.Q = Q
        self.Trap = Q.get()
    def Do(self):
        result = self._Filter.evaluate(self.Trap)
        
        