import typing
import struct
import json
import functools
from base64 import b64encode, b64decode
import redis
from instance import config


# Storage
# - Node id
#       key: util:node_id
#       value: unsigned int
#       locking: no
# - Total nodes
#       key: util:total_node
#       value: unsigned int
#       locking: no
# - Registered nodes
#       key: util:registered_nodes
#       value: int
#       locking: no
# - Node URLs
#       key: util:node_urls
#       value: map [node_id: int] -> [json-encoded data]
#       locking: no


# Use these to have a compact and cacheable json representation
dumps = functools.partial(json.dumps, separators=(',', ':'), sort_keys=True)
loads = json.loads

UI = struct.Struct("!I")
D = struct.Struct("!d")

# TODO OPT: Place the configuration values (max_connections, path) in the config file
_connection_pool = redis.BlockingConnectionPool(max_connections=100,    # TODO OPT: 100? You sure?
                                                timeout=None,
                                                connection_class=redis.UnixDomainSocketConnection,
                                                path="/var/run/redis/redis.sock",
                                                db=config.DB)


def uitob(i: int) -> bytes:
    """Unsigned int to bytes"""
    return UI.pack(i)


def btoui(b: bytes) -> int:
    """Bytes to unsigned int"""
    return UI.unpack(b)[0]


def dtob(d: float) -> bytes:
    """Double to bytes"""
    return D.pack(d)


def btod(b: bytes) -> float:
    """Bytes to double"""
    return D.unpack(b)[0]


def stobin(s: str) -> bytes:
    """String to binary data"""
    return b64decode(s.encode())


def bintos(b: bytes) -> str:
    """Binary data to string"""
    return b64encode(b).decode()


def get_db():   # TODO OPT: annotate this (what's the return value of redis.Redis()?)
    return redis.Redis(connection_pool=_connection_pool)


def get_node_id() -> int:
    r = get_db()
    return btoui(r.get("util:node_id"))


def set_node_id(node_id: int) -> None:
    r = get_db()
    r.set("util:node_id", uitob(node_id))


def get_nodes() -> int:
    r = get_db()
    return btoui(r.get("util:nodes"))


def set_nodes(nodes: int) -> None:
    r = get_db()
    r.set("util:nodes", uitob(nodes))


def incr_registered_nodes(inc: int = 1) -> int:
    """Increment the registered node counter. When calling this for the first
    time, consider the counter as automatically initialized to 0."""
    r = get_db()
    return r.incr("util:registered_nodes", inc)


def get_registered_nodes() -> int:
    # incr_registered_nodes() conveniently returns the registered nodes
    return incr_registered_nodes(0)


def get_ip(node_id: int) -> typing.Mapping[str, str]:   # TODO OPT: This could support multiple IDs
    r = get_db()
    return loads(r.hget("util:node_urls", node_id).decode())


def set_ip(ips: typing.Mapping[int, typing.Mapping[str, str]]) -> None:
    r = get_db()
    r.hmset("util:node_urls", {node_id: dumps(url).encode() for node_id, url in ips.items()})

def get_peer_ids() -> typing.List[int]:
    """Return the ids of all nodes except ours"""
    peer_ids = list(range(get_nodes()))
    peer_ids.remove(get_node_id())
    return peer_ids
