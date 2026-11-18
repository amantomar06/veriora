"""
Educational Blockchain Ledger Implementation
Features:
- Immutable Block Linking (SHA-256)
- Proof-of-Work (PoW) Consensus
- Merkle Root Verification
- Smart Contract Integration
- Tamper Detection & Chain Validation
"""

import copy
import time
from typing import List, Dict, Any, Tuple, Optional
from core.block import Block
from core.crypto_engine import sha256, compute_merkle_root
from core.smart_contract import ProductAuthenticityContract, SmartContractError


class Blockchain:
    """
    Core distributed ledger managing blocks, transactions, and consensus.
    """

    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.difficulty: int = difficulty
        self.smart_contract = ProductAuthenticityContract()
        self._tampered_backup: Optional[Dict[int, Block]] = None

        # Mine the Genesis Block
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Initializes Block #0, the root of trust."""
        genesis_tx = [{
            "type": "GENESIS_INITIALIZATION",
            "sender": "SYSTEM_ROOT",
            "recipient": "NETWORK",
            "product_id": "PRD-GENESIS-ROOT",
            "payload": {
                "message": "E-Commerce Product Authenticity Blockchain Root of Trust",
                "consensus": f"Proof-of-Work (Difficulty={self.difficulty})",
                "version": "1.0.0-PROD-AUTH"
            },
            "timestamp": time.time(),
            "signature": sha256("GENESIS_SIGNATURE_IMMUTABLE_ROOT")
        }]

        genesis_block = Block(
            index=0,
            transactions=genesis_tx,
            previous_hash="0" * 64,
            timestamp=1700000000.0,  # Fixed canonical genesis timestamp
            difficulty=self.difficulty
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

    def get_latest_block(self) -> Block:
        """Returns the most recently added block on the chain."""
        return self.chain[-1]

    def add_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates transaction against smart contract programmable rules.
        If valid, adds to pending transaction pool.
        """
        if "timestamp" not in tx:
            tx["timestamp"] = time.time()
        if "tx_id" not in tx:
            tx["tx_id"] = "TX-" + sha256(f"{tx.get('product_id')}-{tx['timestamp']}")[:16].upper()

        # Execute smart contract validation
        execution_result = self.smart_contract.validate_and_execute(tx)
        
        self.pending_transactions.append(tx)
        return {
            "status": "ACCEPTED",
            "tx_id": tx["tx_id"],
            "execution_result": execution_result
        }

    def mine_pending_transactions(self, miner_address: str = "NODE_SYSTEM_MINER") -> Dict[str, Any]:
        """
        Packages pending transactions into a new block, computes Merkle Root,
        solves Proof-of-Work puzzle, and commits block to ledger.
        """
        if not self.pending_transactions:
            return {"status": "NO_TRANSACTIONS", "message": "Pending pool is empty. Nothing to mine."}

        latest_block = self.get_latest_block()
        new_index = latest_block.index + 1
        txs_to_mine = list(self.pending_transactions)

        new_block = Block(
            index=new_index,
            transactions=txs_to_mine,
            previous_hash=latest_block.hash,
            difficulty=self.difficulty
        )

        mining_stats = new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = []

        return {
            "status": "MINED_SUCCESSFULLY",
            "block_index": new_block.index,
            "block_hash": new_block.hash,
            "transactions_count": len(txs_to_mine),
            "mining_stats": mining_stats
        }

    def validate_chain(self) -> Tuple[bool, str, Optional[int]]:
        """
        Validates the entire blockchain cryptographic integrity:
        1. Correct sequential block indexing.
        2. Block header SHA-256 hash recalculation check.
        3. Linking check: block[i].previous_hash == block[i-1].hash.
        4. Proof-of-Work difficulty target satisfied.
        5. Merkle Root integrity of transaction list.

        Returns: (is_valid, error_description, faulty_block_index)
        """
        target_prefix = "0" * self.difficulty

        for i in range(len(self.chain)):
            current = self.chain[i]

            # 1. Check index
            if current.index != i:
                return False, f"Block #{i} index mismatch (found {current.index})", i

            # 2. Check recalculated hash
            recalculated_hash = current.calculate_hash()
            if current.hash != recalculated_hash:
                return (
                    False,
                    f"Block #{i} has been tampered! Stored hash '{current.hash}' != Recalculated '{recalculated_hash}'",
                    i
                )

            # 3. Check Proof-of-Work
            if not current.hash.startswith(target_prefix):
                return False, f"Block #{i} failed Proof-of-Work condition (difficulty {self.difficulty})", i

            # 4. Check Merkle Root
            recalculated_merkle = compute_merkle_root(current.transactions)
            if current.merkle_root != recalculated_merkle:
                return (
                    False,
                    f"Block #{i} Merkle Root corrupted! Stored '{current.merkle_root}' != Computed '{recalculated_merkle}'",
                    i
                )

            # 5. Check chain linking (skip Genesis)
            if i > 0:
                previous = self.chain[i - 1]
                if current.previous_hash != previous.hash:
                    return (
                        False,
                        f"Chain broken at Block #{i}! previous_hash '{current.previous_hash}' != Block #{i-1} hash '{previous.hash}'",
                        i
                    )

        return True, "Blockchain integrity 100% verified. All cryptographic proofs valid.", None

    def tamper_block_for_testing(self, block_index: int, fake_product_name: str) -> Dict[str, Any]:
        """
        Educational feature: Deliberately alters transaction data inside a block
        to demonstrate cryptographic immutability and instant fraud detection.
        """
        if block_index < 0 or block_index >= len(self.chain):
            return {"status": "ERROR", "message": f"Block index {block_index} out of range"}

        target_block = self.chain[block_index]
        if not target_block.transactions:
            return {"status": "ERROR", "message": "Target block has no transactions to tamper."}

        # Backup block for restore (deep copy to preserve original transactions)
        if self._tampered_backup is None:
            self._tampered_backup = {}
        if block_index not in self._tampered_backup:
            self._tampered_backup[block_index] = Block.from_dict(copy.deepcopy(target_block.to_dict()))

        # Alter payload without updating hash or downstream blocks
        if "payload" in target_block.transactions[0]:
            target_block.transactions[0]["payload"]["product_name"] = fake_product_name
            target_block.transactions[0]["payload"]["COUNTERFEIT_INJECTION"] = True

        return {
            "status": "TAMPERED",
            "message": f"Deliberately injected counterfeit data into Block #{block_index}. Chain is now corrupted!",
            "block_index": block_index
        }

    def restore_tampered_blocks(self) -> Dict[str, Any]:
        """Restores any deliberately corrupted blocks back to original state."""
        if not self._tampered_backup:
            return {"status": "NOTHING_TO_RESTORE", "message": "No blocks were tampered."}

        for idx, original_block in self._tampered_backup.items():
            self.chain[idx] = original_block

        self._tampered_backup = None
        return {"status": "RESTORED", "message": "Original valid chain restored successfully."}

    def verify_product(self, product_id: str) -> Dict[str, Any]:
        """
        Comprehensive authenticity check for consumers:
        Looks up smart contract state, verifies provenance history,
        and confirms block anchoring.
        """
        product = self.smart_contract.get_product(product_id)
        if not product:
            return {
                "is_genuine": False,
                "product_id": product_id,
                "verdict": "COUNTERFEIT / UNREGISTERED PRODUCT",
                "message": f"No blockchain record found for Product ID '{product_id}'. This item may be counterfeit or fraudulent.",
                "history": []
            }

        history = self.smart_contract.get_history(product_id)
        
        # Locate containing blocks
        containing_blocks = []
        for blk in self.chain:
            for tx in blk.transactions:
                if tx.get("product_id") == product_id:
                    containing_blocks.append({
                        "block_index": blk.index,
                        "block_hash": blk.hash,
                        "timestamp": blk.timestamp,
                        "tx_type": tx.get("type")
                    })

        is_tampered = product.get("tamper_detected", False)
        is_recalled = product.get("recalled", False)

        if is_tampered:
            verdict = "WARNING: TAMPER OR COUNTERFEIT DETECTED"
            is_genuine = False
        elif is_recalled:
            verdict = "WARNING: RECALLED PRODUCT"
            is_genuine = False
        else:
            verdict = "100% GENUINE PRODUCT VERIFIED ON BLOCKCHAIN"
            is_genuine = True

        return {
            "is_genuine": is_genuine,
            "product_id": product_id,
            "verdict": verdict,
            "product_details": product,
            "history": history,
            "block_confirmations": containing_blocks,
            "authenticity_hash": product.get("authenticity_hash"),
            "manufacturer": product.get("registered_by"),
            "current_owner": product.get("current_owner"),
            "current_status": product.get("current_status"),
            "current_location": product.get("current_location")
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Returns high-level blockchain and ecosystem statistics."""
        is_valid, validation_msg, faulty_block = self.validate_chain()
        total_txs = sum(len(b.transactions) for b in self.chain) + len(self.pending_transactions)

        return {
            "total_blocks": len(self.chain),
            "difficulty": self.difficulty,
            "chain_valid": is_valid,
            "validation_message": validation_msg,
            "faulty_block": faulty_block,
            "total_products_registered": len(self.smart_contract.products),
            "total_transactions": total_txs,
            "pending_transactions_count": len(self.pending_transactions),
            "authorized_entities_count": len(self.smart_contract.authorized_entities)
        }
