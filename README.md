# trapdoor
A python application for recieving snmp traps

## Schema

```

.-----------------------------------------------------.
|                                          mainThread |
| .---------------------.  .------------------------. |
| |               async |  |                  async | |
| |  trapdoor.core.Web  |  |    trapdoor.core.Trap  | |
| |                     |  |                        | |
| ´---^-----------------´  `------------------|-----´ |
`-----|---------------------------------------|-------´
      |                                       v
      |                    .--------------------------.
      |                    |                    async |
      |                    |   trapdoor.core.Queue    <--.
      |                    |                   thread |  |
      |                    `------------------|-------´  |
      |                                       v          |
      |                    .--------------------------.  |
      |                    |         actionThread-XXX |  |
.-----|---.------------.   | .----------------------. |  |
|   async |            |   | |                      | |  |
`---------´            ----->| trapdoor.core.Filter  ----´
|                      |   | |                      | |
|                      |   | `----------------|-----´ |
|   trapdoor.core.db   |   |                  v       |
|                      |   | .----------------------. |
|                      |   | |                      | |
|                      |<----- trapdoor.handlers    | |
|                      |   | |                      | |
`----------------------´   | `----------------------´ |
                           `--------------------------´

```
### Description

Trapdoor tries to be async wherever it can.
Because we use handlers & filters that are written in js,
this can be a problem. That's why there's a threadpool for 
queue actions. (in schema actionThread-XXX). We use a Queue
named Janus, that has async & sync handlers for modifying the
queue.

Let's follow the trail of a incoming trap:
1. Trap is recieved at `trapdoor.core.Trap` [async]
2. It gets pushed to the Queue [async]
3. Where a waiting thread picks it up [sync/thread]
4. We lookup the filter in the database
5. Apply the JS filter
6. If the filter has explicitly returned `next: False`, go to
   the next step, else re-apply it to the queue with this filter
   marked as done. Note that the filter also allows to 'split' the
   trap into clones. A clone that goes to the handlers & one that
   goes back into the queue.
7. Handle the trap using the specified handler.
8. Save to the database.