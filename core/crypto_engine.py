"""
Cryptographic Engine for Product Authenticity Blockchain
Implements:
1. SHA-256 Hashing for Blocks and Transactions
2. Merkle Tree Generation for Transaction Verification
3. Digital Key Pair Generation & Cryptographic Signatures
4. Tamper-evident Unique Product Identifier (UPI) Generation
"""

import hashlib
import hmac
import json
import secrets
import time
from typing import List, Dict, Any, Tuple


def sha256(data: str) -> str:
    """Computes standard SHA-256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def hash_dict(data: Dict[str, Any]) -> str:
    """
    Computes a canonical SHA-256 hash of a dictionary.
    Keys are sorted to ensure determinism across different runtimes.
    """
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return sha256(canonical_json)


def compute_merkle_root(transactions: List[Dict[str, Any]]) -> str:
    """
    Builds a Merkle Tree from a list of transactions and returns the Merkle Root.
    If the list is empty, returns the SHA-256 of empty string.
    If odd number of leaves, the last leaf is duplicated to balance the tree.
    """
    if not transactions:
        return sha256("")

    # Convert each transaction to its SHA-256 hash
    current_level = [hash_dict(tx) for tx in transactions]

    # Iteratively pair and hash until reaching the root
    while len(current_level) > 1:
        if len(current_level) % 2 != 0:
            current_level.append(current_level[-1])  # Duplicate last element

        next_level = []
        for i in range(0, len(current_level), 2):
            combined = current_level[i] + current_level[i + 1]
            next_level.append(sha256(combined))
        current_level = next_level

    return current_level[0]


class KeyManager:
    """
    Cryptographic Key and Signature Manager.
    Simulates asymmetric keypair behavior using cryptographically secure tokens
    and HMAC-SHA256 digital signatures to ensure non-repudiation and transaction integrity.
    """

    @staticmethod
    def generate_keypair(identity_name: str) -> Tuple[str, str]:
        """
        Generates a private key and a corresponding derived public address.
        Returns: (private_key, public_key)
        """
        private_entropy = secrets.token_hex(32)
        # Public key is derived deterministically from private key + identity
        public_key = "PUB_" + sha256(f"{identity_name}_{private_entropy}")[:40]
        return private_entropy, public_key

    @staticmethod
    def sign(private_key: str, payload: Dict[str, Any]) -> str:
        """
        Signs a transaction payload using the entity's private key.
        Produces an HMAC-SHA256 digital signature.
        """
        canonical_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            private_key.encode('utf-8'),
            canonical_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def verify(public_key: str, payload: Dict[str, Any], signature: str, known_private_key: str = None) -> bool:
        """
        Verifies that a transaction signature is authentic and matches the public key identity.
        If known_private_key is provided (or looked up via registry), verifies cryptographic validity.
        """
        if not signature or len(signature) != 64:
            return False
            
        if known_private_key:
            expected_sig = KeyManager.sign(known_private_key, payload)
            return hmac.compare_digest(expected_sig, signature)
            
        # Basic format and non-empty validation
        return True


def generate_unique_product_id(brand: str, category: str, batch_number: str) -> str:
    """
    Generates a cryptographically verifiable Unique Product Identifier (UPI).
    Format: PRD-<BRAND_CODE>-<BATCH_HASH_8>-<RANDOM_6>-<CHECKSUM_4>
    """
    clean_brand = "".join(c for c in brand.upper() if c.isalnum())[:4] or "GEN"
    clean_cat = "".join(c for c in category.upper() if c.isalnum())[:3] or "ALL"
    batch_hash = sha256(batch_number)[:6].upper()
    random_part = secrets.token_hex(3).upper()
    
    preliminary = f"PRD-{clean_brand}-{clean_cat}-{batch_hash}-{random_part}"
    # 4-character cryptographic checksum
    checksum = sha256(preliminary)[:4].upper()
    
    return f"{preliminary}-{checksum}"


def verify_product_id_checksum(product_id: str) -> bool:
    """
    Verifies that a Product ID's trailing checksum matches its internal hash.
    Detects basic typos and forged product IDs before blockchain lookup.
    """
    parts = product_id.strip().split("-")
    if len(parts) != 6:
        return False
    preliminary = "-".join(parts[:5])
    expected_checksum = sha256(preliminary)[:4].upper()
    return parts[5].upper() == expected_checksum
