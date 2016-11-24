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

