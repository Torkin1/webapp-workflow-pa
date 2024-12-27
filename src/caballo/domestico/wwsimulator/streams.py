from pdsteele.des import rngs

SERVICES_NUM = 64


DEFAULT = 0
"""
Default stream.
"""
EXTERNAL_ARRIVALS = 1
"""
Stream for generating external inter-arrival times
"""
SERVICES_BASE = 2
"""
Stream for generating service times. Streams from SERVICES_BASE up to SERVICES_BASE + SERVICES_NUM - 1
are reserved for indipendent service times.
"""


# register more streams here ...

NUM_STREAMS = rngs.STREAMS