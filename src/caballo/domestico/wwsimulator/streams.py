from pdsteele.des import rngs

DEFAULT = 0
"""
Default stream.
"""
EXTERNAL_ARRIVALS = 1
"""
Stream for generating external inter-arrival times
"""
SERVICES = 2
"""
Stream for generating service times
"""

# register more streams here ...

MAX = rngs.STREAMS - 1