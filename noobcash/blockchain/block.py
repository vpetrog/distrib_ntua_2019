import typing
import hashlib
import sys
import subprocess
from noobcash.blockchain.transaction import Transaction
from noobcash.blockchain import util
from noobcash.blockchain.util import uitob, btoui, stobin, bintos


# Storage
# - CAPACITY
#       key: block:capacity
#       value: unsigned int
#       locking: no
# - DIFFICULTY
#       key: block:difficulty
#       value: unsigned int
#       locking: no


class Block:

    def __init__(self,
                 index: int,
                 previous_hash: bytes,
                 transactions: typing.List[Transaction],
                 timestamp: typing.Optional[int] = None,
                 nonce: typing.Optional[int] = None,
                 current_hash: typing.Optional[bytes] = None) -> None:
        if not (isinstance(previous_hash, bytes) and \
                isinstance(transactions, list) and \
                all(isinstance(t, Transaction) for t in transactions)):
            raise TypeError
        self.index = int(index)
        self.previous_hash = previous_hash
        self.transactions = transactions

        if timestamp is None and nonce is None and current_hash is None:
            # NOTE: It's good practice to initialize all attributes in the constructor
            self.timestamp = None   # set when mining instead
            self.nonce = None
            self.current_hash = None
        else:
            if not isinstance(current_hash, bytes):
                raise TypeError
            self.timestamp = int(timestamp) # type: ignore
            self.nonce = int(nonce) # type: ignore
            self.current_hash = current_hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Block):
            return False
        if self.current_hash is None:
            return False
        return self.current_hash == other.current_hash

    def __hash__(self) -> int:
        # NOTE: This will raise an exception if the block hasn't been finalized (mined)
        return int.from_bytes(self.current_hash, byteorder="big")   # type: ignore

    def __repr__(self) -> str:
        return self.dumps()

    @staticmethod
    def genesis() -> 'Block':
        g = Block(index=0,
                  previous_hash=(1).to_bytes(256 // 8, byteorder="big"),
                  transactions=[Transaction.genesis()])
        g.timestamp = 0
        g.nonce = 0
        g.current_hash = g.hash()
        return g

    def finalize(self) -> int:
        """
        Mine the block

        Spawns a miner process responsible for mining the block and broadcasting
        it upon success. The difficulty is passed as the first command line
        argument and the (partial) block is fed to the standard input,
        JSON-serialized with dumps().
        NOTE: to be clear: this object is NOT changed in any way. Its nonce and
        current_hash are NOT updated, even upon successful mining

        :returns: the pid of the spawned process
        """
        def wait_miner(p, b):
            import logging
            outs, errs = p.communicate(input=b.dumps())
            logging.debug("Miner %d stdout: %s", p.pid, outs)
            logging.debug("Miner %d stderr: %s", p.pid, errs)

        import threading
        python = sys.executable if sys.executable else 'python3'
        p = subprocess.Popen(args=[python,
                                   '-m',
                                   'noobcash.blockchain.miner',
                                   str(get_difficulty())],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             universal_newlines=True)
        threading.Thread(target=wait_miner, args=(p, self)).start()
        return p.pid

    def _partial_hash(self):   # TODO OPT: Annotate this (what's the type of hashlib.sha256()?)
        """Return a hash object updated with the fixed part of the block"""
        h = hashlib.sha256()
        h.update(uitob(self.index))
        h.update(self.previous_hash)
        h.update(uitob(self.timestamp))
        for t in self.transactions:
            h.update(t.id)
        return h

    def hash(self) -> bytes:
        h = self._partial_hash()
        # NOTE: This will raise an exception if the block hasn't been finalized (mined)
        h.update(uitob(self.nonce)) # type: ignore
        # TODO OPT: self.current_hash = digest?
        return h.digest()

    def _check_difficulty(self) -> bool:
        target = (1 << (256 - get_difficulty())) - 1    # assume DIFFICULTY # of bits (not bytes)
        # NOTE: This will raise an exception if the block hasn't been finalized (mined)
        return self.current_hash <= target.to_bytes(256 // 8, byteorder="big")  # type: ignore

    def is_genesis(self) -> bool:
        if self.index != 0:
            return False
        if self.previous_hash != (1).to_bytes(256 // 8, byteorder="big"):
            return False
        if self.timestamp != 0:
            return False
        if len(self.transactions) != 1:
            return False
        if not self.transactions[0].is_genesis():
            return False
        if self.nonce != 0:
            return False
        if self.current_hash != self.hash():
            return False

        return True

    def verify(self) -> bool:
        # TODO OPT: Is there anything else to verify?
        if self.is_genesis():
            return True
        # CAPACITY > 0
        capacity = get_capacity()
        if capacity <= 0:
            return False
        # # of transactions == CAPACITY
        if len(self.transactions) != capacity:
            return False
        # all transactions are verified
        if not all(t.verify() for t in self.transactions):
            return False
        # hash check
        if self.current_hash != self.hash():
            return False
        # difficulty check
        if not self._check_difficulty():
            return False

        return True

    def dumpb(self) -> bytes:
        """Dump to bytes"""
        # NOTE: We can't easily have a proper binary encoding because
        # transactions don't have a fixed size bytes representation
        return self.dumps().encode()

    def dumpo(self) -> typing.Mapping[str, typing.Any]:
        """Dump to JSON-serializable object"""
        return {
            "index": self.index,
            "previous_hash": bintos(self.previous_hash),
            "timestamp": self.timestamp,
            "transactions": [t.dumpo() for t in self.transactions],
            "nonce": self.nonce,
            "current_hash": bintos(self.current_hash) if self.current_hash is not None else None
        }

    def dumps(self) -> str:
        """Dump to string"""
        return util.dumps(self.dumpo())

    @classmethod
    def loadb(cls, b: bytes) -> 'Block':
        """Load from bytes"""
        return cls.loads(b.decode())

    @classmethod
    def loado(cls, o: typing.Mapping[str, typing.Any]) -> 'Block':
        """Load from JSON-serializable object"""
        current_hash = o["current_hash"]
        return cls(index=o["index"],
                   previous_hash=stobin(o["previous_hash"]),
                   timestamp=o["timestamp"],
                   transactions=[Transaction.loado(t) for t in o["transactions"]],
                   nonce=o["nonce"],
                   current_hash=stobin(current_hash) if current_hash is not None else None)

    @classmethod
    def loads(cls, s: str) -> 'Block':
        """Load from string"""
        return cls.loado(util.loads(s))


def get_capacity() -> int:
    r = util.get_db()
    return btoui(r.get("block:capacity"))


def set_capacity(c: int) -> None:
    r = util.get_db()
    r.set("block:capacity", uitob(c))


def get_difficulty() -> int:
    r = util.get_db()
    return btoui(r.get("block:difficulty"))


def set_difficulty(d: int) -> None:
    r = util.get_db()
    r.set("block:difficulty", uitob(d))
