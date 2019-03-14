import struct
import json
import functools
import redis


# Storage
# - Node id             util:node_id            unsigned int
# - Total nodes         util:total_node         unsigned int
# - Registered nodes    util:registered_nodes   int


# Use these to have a compact and cacheable json representation
dumps = functools.partial(json.dumps, separators=(',', ':'), sort_keys=True)
loads = json.loads

UI = struct.Struct("!I")
D = struct.Struct("!d")


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


def stob(s: str) -> bytes:
    """String to bytes. ONLY WORKS FOR STRINGS RETURNED BY btos"""
    return bytes.fromhex(s)


def btos(b: bytes) -> str:
    """Bytes to string"""
    return b.hex()


def get_db(db=0):   # TODO OPT: annotate this (what's the return value of redis.Redis()?)
    return redis.Redis(db=db)


def get_ip():   # TODO: Argument(s) and return value(s)
    # TODO
    raise NotImplementedError


def set_ip():   # TODO: Argument(s) and return value(s)
    # TODO
    raise NotImplementedError


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
    r = get_db()
    return r.incr("util:registered_nodes", inc)


get_registered_nodes = functools.partial(incr_registered_nodes, inc=0)
