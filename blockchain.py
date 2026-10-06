import hashlib
import json
import random
import time


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Block:
    def __init__(self, index, transactions, prev_hash, timestamp=None):
        self.index = index
        self.transactions = transactions  # lista de dicts
        self.prev_hash = prev_hash
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        payload = json.dumps(
            {
                "index": self.index,
                "tx": self.transactions,
                "prev": self.prev_hash,
                "ts": self.timestamp,
                "nonce": self.nonce,
            },
            sort_keys=True,
        )
        return sha256(payload)

    def mine(self, difficulty):
        """Proof of Work: busca un hash que empiece con `difficulty` ceros."""
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty
        self.chain = []
        genesis = Block(0, [], "0" * 64, timestamp=0)
        genesis.mine(difficulty)
        self.chain.append(genesis)

    def add_block(self, transactions):
        prev = self.chain[-1]
        block = Block(len(self.chain), transactions, prev.hash)
        block.mine(self.difficulty)
        self.chain.append(block)
        return block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            cur, prev = self.chain[i], self.chain[i - 1]
            if cur.hash != cur.compute_hash() or cur.prev_hash != prev.hash:
                return False
        return True


def make_transaction(rng: random.Random, n_accounts=50):
    """Transacción aleatoria; con `rng` con semilla es reproducible."""
    sender = f"acc{rng.randrange(n_accounts):03d}"
    receiver = f"acc{rng.randrange(n_accounts):03d}"
    amount = rng.randrange(1, 1000)
    nonce = rng.getrandbits(64)
    tx_id = sha256(f"{sender}{receiver}{amount}{nonce}")
    return {"id": tx_id, "from": sender, "to": receiver, "amount": amount}


def build_chain(n_blocks=100, tx_per_block=10, difficulty=2, seed=42):
    rng = random.Random(seed)
    bc = Blockchain(difficulty)
    for _ in range(n_blocks):
        bc.add_block([make_transaction(rng) for _ in range(tx_per_block)])
    return bc
