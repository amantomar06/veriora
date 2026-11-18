"""
Block Data Structure & Proof-of-Work Mining for E-Commerce Blockchain
"""

import time
from typing import List, Dict, Any
from core.crypto_engine import sha256, compute_merkle_root


class Block:
    """
    Represents a single block in the Product Authenticity Blockchain.
    Contains block header data, list of transactions, and cryptographic proofs.
    """

    def __init__(
        self,
        index: int,
        transactions: List[Dict[str, Any]],
        previous_hash: str,
        timestamp: float = None,
        nonce: int = 0,
        difficulty: int = 2,
        merkle_root: str = None,
        block_hash: str = None
    ):
        self.index = index
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = nonce
        self.merkle_root = merkle_root if merkle_root is not None else compute_merkle_root(transactions)
        self.hash = block_hash if block_hash is not None else self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculates SHA-256 hash of the block header attributes:
        Index + Timestamp + PreviousHash + MerkleRoot + Nonce + Difficulty
        """
        header_string = (
            f"{self.index}"
            f"{self.timestamp:.6f}"
            f"{self.previous_hash}"
            f"{self.merkle_root}"
            f"{self.nonce}"
            f"{self.difficulty}"
        )
        return sha256(header_string)

    def mine_block(self, difficulty: int = None) -> Dict[str, Any]:
        """
        Executes Proof-of-Work (PoW) consensus.
        Increments nonce until hash satisfies target difficulty (number of leading zeros).
        """
        if difficulty is not None:
            self.difficulty = difficulty

        target_prefix = "0" * self.difficulty
        start_time = time.time()
        initial_nonce = self.nonce

        while not self.calculate_hash().startswith(target_prefix):
            self.nonce += 1

        self.hash = self.calculate_hash()
        duration = time.time() - start_time
        hashes_calculated = self.nonce - initial_nonce + 1

        return {
            "index": self.index,
            "nonce": self.nonce,
            "hash": self.hash,
            "duration_seconds": round(duration, 4),
            "hashes_calculated": hashes_calculated
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializes block to a dictionary for network transport and storage."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """Constructs a Block object from a dictionary."""
        return cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            nonce=data["nonce"],
            difficulty=data.get("difficulty", 2),
            merkle_root=data.get("merkle_root"),
            block_hash=data.get("hash")
        )
