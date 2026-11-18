"""
Unit & Integration Test Suite for E-Commerce Product Authenticity Blockchain
Fulfills Deliverables 4, 5, and 7:
- Data Integrity (Hashing, Merkle Trees, Digital Signatures)
- Smart Contract Business Logic & RBAC
- Testing: Valid transactions, invalid transactions, security checks, and tamper detection
"""

import unittest
import time
from core.crypto_engine import (
    sha256,
    hash_dict,
    compute_merkle_root,
    KeyManager,
    generate_unique_product_id,
    verify_product_id_checksum
)
from core.block import Block
from core.blockchain import Blockchain
from core.smart_contract import ProductAuthenticityContract, SmartContractError
from core.ai_engine import AICounterfeitDetector


class TestProductAuthenticityBlockchain(unittest.TestCase):

    def setUp(self):
        """Set up clean isolated blockchain instance for each test."""
        self.blockchain = Blockchain(difficulty=2)
        self.ai_engine = AICounterfeitDetector()
        
        # Test actors
        self.mfr_apple = self.blockchain.smart_contract.entity_keys["MFR-001"]
        self.mfr_nike = self.blockchain.smart_contract.entity_keys["MFR-002"]
        self.dst_logistics = self.blockchain.smart_contract.entity_keys["DST-101"]
        self.ret_bestbuy = self.blockchain.smart_contract.entity_keys["RET-201"]

    # -------------------------------------------------------------
    # 1. Blockchain Ledger & Consensus Tests (Deliverable 3 & 4)
    # -------------------------------------------------------------

    def test_genesis_block_creation(self):
        """Verify genesis block initialization and PoW compliance."""
        genesis = self.blockchain.chain[0]
        self.assertEqual(genesis.index, 0)
        self.assertEqual(genesis.previous_hash, "0" * 64)
        self.assertTrue(genesis.hash.startswith("00"))
        self.assertEqual(len(self.blockchain.chain), 1)

    def test_proof_of_work_mining(self):
        """Verify Proof-of-Work difficulty target satisfaction."""
        dummy_tx = [{
            "type": "TEST_TX",
            "product_id": "PRD-TEST-001",
            "timestamp": time.time()
        }]
        block = Block(index=1, transactions=dummy_tx, previous_hash=self.blockchain.chain[-1].hash, difficulty=2)
        stats = block.mine_block(difficulty=2)
        
        self.assertTrue(block.hash.startswith("00"))
        self.assertGreater(stats["nonce"], 0)
        self.assertEqual(block.calculate_hash(), block.hash)

    def test_merkle_tree_calculation(self):
        """Demonstrate Merkle Root hashing and tamper sensitivity (Deliverable 4)."""
        tx1 = {"tx_id": "TX1", "amount": 100}
        tx2 = {"tx_id": "TX2", "amount": 200}
        root1 = compute_merkle_root([tx1, tx2])

        # Same transactions produce identical Merkle Root
        root2 = compute_merkle_root([tx1, tx2])
        self.assertEqual(root1, root2)

        # Tampered transaction produces completely different Merkle Root
        tx2_tampered = {"tx_id": "TX2", "amount": 9999}
        root_tampered = compute_merkle_root([tx1, tx2_tampered])
        self.assertNotEqual(root1, root_tampered)

    def test_digital_signature_verification(self):
        """Demonstrate asymmetric cryptographic signature verification (Deliverable 4)."""
        priv, pub = KeyManager.generate_keypair("MFR-TEST")
        payload = {"product_name": "Authentic Watch", "batch": "B1"}
        
        signature = KeyManager.sign(priv, payload)
        self.assertEqual(len(signature), 64)

        # Valid signature verification
        is_valid = KeyManager.verify(pub, payload, signature, priv)
        self.assertTrue(is_valid)

        # Altered payload must fail verification
        altered_payload = {"product_name": "Counterfeit Watch", "batch": "B1"}
        is_valid_altered = KeyManager.verify(pub, altered_payload, signature, priv)
        self.assertFalse(is_valid_altered)

    # -------------------------------------------------------------
    # 2. Smart Contract Rules & Access Control (Deliverable 5)
    # -------------------------------------------------------------

    def test_valid_product_registration(self):
        """Test valid product minting by authorized manufacturer."""
        pid = generate_unique_product_id("Apple", "Phone", "BATCH-AAPL-01")
        payload = {
            "product_name": "iPhone 16 Pro",
            "brand": "Apple",
            "batch_number": "BATCH-AAPL-01",
            "manufacture_date": "2026-11-01",
            "specs": {"color": "Black", "msrp_usd": 999.00}
        }
        sig = KeyManager.sign(self.mfr_apple["private_key"], payload)
        
        tx = {
            "type": "PRODUCT_REGISTRATION",
            "product_id": pid,
            "sender_public_key": self.mfr_apple["public_key"],
            "payload": payload,
            "signature": sig
        }

        res = self.blockchain.add_transaction(tx)
        self.assertEqual(res["status"], "ACCEPTED")
        
        mine_res = self.blockchain.mine_pending_transactions()
        self.assertEqual(mine_res["status"], "MINED_SUCCESSFULLY")
        self.assertEqual(len(self.blockchain.chain), 2)

        # Verify on-chain product record
        prod = self.blockchain.smart_contract.get_product(pid)
        self.assertIsNotNone(prod)
        self.assertEqual(prod["current_status"], "REGISTERED")
        self.assertEqual(prod["current_owner"], "Apple Official Inc.")

    def test_invalid_duplicate_product_registration_rejected(self):
        """Security Check: Reject duplicate product ID registration (Deliverable 5 & 7)."""
        pid = generate_unique_product_id("Apple", "Phone", "BATCH-AAPL-DUP")
        payload = {
            "product_name": "iPhone Original",
            "brand": "Apple",
            "batch_number": "BATCH-AAPL-DUP",
            "manufacture_date": "2026-11-01",
            "specs": {"msrp_usd": 999.00}
        }
        sig = KeyManager.sign(self.mfr_apple["private_key"], payload)
        tx = {
            "type": "PRODUCT_REGISTRATION",
            "product_id": pid,
            "sender_public_key": self.mfr_apple["public_key"],
            "payload": payload,
            "signature": sig
        }

        # First registration succeeds
        self.blockchain.add_transaction(tx)
        self.blockchain.mine_pending_transactions()

        # Second registration attempt with identical Product ID must be rejected by Smart Contract
        with self.assertRaises(SmartContractError) as context:
            self.blockchain.add_transaction(tx)
        self.assertIn("already registered", str(context.exception))

    def test_invalid_unauthorized_creator_rejected(self):
        """Security Check: Only MANUFACTURERS can mint new products (Deliverable 5 & 7)."""
        pid = generate_unique_product_id("FakeBrand", "Shoes", "BATCH-FAKE-01")
        payload = {
            "product_name": "Unauthorized Sneakers",
            "brand": "FakeBrand",
            "batch_number": "BATCH-FAKE-01",
            "manufacture_date": "2026-11-01",
            "specs": {"msrp_usd": 150.00}
        }
        # Logistics entity attempts to mint
        sig = KeyManager.sign(self.dst_logistics["private_key"], payload)
        tx = {
            "type": "PRODUCT_REGISTRATION",
            "product_id": pid,
            "sender_public_key": self.dst_logistics["public_key"],
            "payload": payload,
            "signature": sig
        }

        with self.assertRaises(SmartContractError) as context:
            self.blockchain.add_transaction(tx)
        self.assertIn("Only authorized MANUFACTURERS can mint", str(context.exception))

    def test_invalid_digital_signature_rejected(self):
        """Security Check: Forged or corrupted digital signatures must be rejected (Deliverable 4, 5 & 7)."""
        pid = generate_unique_product_id("Apple", "Phone", "BATCH-BAD-SIG")
        payload = {
            "product_name": "iPhone with Bad Sig",
            "brand": "Apple",
            "batch_number": "BATCH-BAD-SIG",
            "manufacture_date": "2026-11-01",
            "specs": {"msrp_usd": 999.00}
        }
        # Forged signature
        fake_signature = "0" * 64
        tx = {
            "type": "PRODUCT_REGISTRATION",
            "product_id": pid,
            "sender_public_key": self.mfr_apple["public_key"],
            "payload": payload,
            "signature": fake_signature
        }

        with self.assertRaises(SmartContractError) as context:
            self.blockchain.add_transaction(tx)
        self.assertIn("Digital signature verification failed", str(context.exception))

    def test_valid_and_invalid_custody_transfer(self):
        """Test valid custody handover vs unauthorized thief transfer (Deliverable 5 & 7)."""
        # 1. Mint genuine product
        pid = generate_unique_product_id("Nike", "Apparel", "BATCH-NIKE-77")
        payload = {
            "product_name": "Air Jordan Sneakers",
            "brand": "Nike",
            "batch_number": "BATCH-NIKE-77",
            "manufacture_date": "2026-11-01",
            "specs": {"msrp_usd": 200.00}
        }
        sig = KeyManager.sign(self.mfr_nike["private_key"], payload)
        self.blockchain.add_transaction({
            "type": "PRODUCT_REGISTRATION",
            "product_id": pid,
            "sender_public_key": self.mfr_nike["public_key"],
            "payload": payload,
            "signature": sig
        })
        self.blockchain.mine_pending_transactions()

        # 2. Valid Transfer: Nike -> Logistics
        transfer_payload = {
            "recipient_public_key": self.dst_logistics["public_key"],
            "next_status": "IN_TRANSIT",
            "location": "Oregon Distribution Center"
        }
        transfer_sig = KeyManager.sign(self.mfr_nike["private_key"], transfer_payload)
        self.blockchain.add_transaction({
            "type": "CUSTODY_TRANSFER",
            "product_id": pid,
            "sender_public_key": self.mfr_nike["public_key"],
            "payload": transfer_payload,
            "signature": transfer_sig
        })
        self.blockchain.mine_pending_transactions()

        prod = self.blockchain.smart_contract.get_product(pid)
        self.assertEqual(prod["current_status"], "IN_TRANSIT")
        self.assertEqual(prod["current_owner"], "Global Express Logistics")

        # 3. Invalid Transfer: Apple tries to transfer Nike's shoe currently owned by Logistics!
        unauthorized_payload = {
            "recipient_public_key": self.ret_bestbuy["public_key"],
            "next_status": "AT_RETAILER",
            "location": "Stolen Warehouse"
        }
        unauthorized_sig = KeyManager.sign(self.mfr_apple["private_key"], unauthorized_payload)
        with self.assertRaises(SmartContractError) as context:
            self.blockchain.add_transaction({
                "type": "CUSTODY_TRANSFER",
                "product_id": pid,
                "sender_public_key": self.mfr_apple["public_key"],
                "payload": unauthorized_payload,
                "signature": unauthorized_sig
            })
        self.assertIn("Unauthorized transfer", str(context.exception))

    # -------------------------------------------------------------
    # 3. Tamper Detection & Immutability Verification (Deliverable 7)
    # -------------------------------------------------------------

    def test_tamper_detection_invalidates_blockchain(self):
        """Security Check: Altering block contents breaks cryptographic chain validation."""
        # Add a block
        pid = generate_unique_product_id("Sony", "Audio", "BATCH-SNY-01")
        payload = {
            "product_name": "Sony Headphones",
            "brand": "Sony",
            "batch_number": "BATCH-SNY-01",
            "manufacture_date": "2026-11-01",
            "specs": {"msrp_usd": 350.00}
        }
        mfr_sony = self.blockchain.smart_contract.entity_keys["MFR-004"]
        sig = KeyManager.sign(mfr_sony["private_key"], payload)
        self.blockchain.add_transaction({
            "type": "PRODUCT_REGISTRATION",
            "product_id": pid,
            "sender_public_key": mfr_sony["public_key"],
            "payload": payload,
            "signature": sig
        })
        self.blockchain.mine_pending_transactions()

        # Chain must initially be 100% valid
        is_valid, msg, faulty_idx = self.blockchain.validate_chain()
        self.assertTrue(is_valid)
        self.assertIsNone(faulty_idx)

        # Inject tamper attack
        tamper_res = self.blockchain.tamper_block_for_testing(1, "COUNTERFEIT_CLONED_PRODUCT")
        self.assertEqual(tamper_res["status"], "TAMPERED")

        # Chain validation must now FAIL
        is_valid_after, msg_after, faulty_idx_after = self.blockchain.validate_chain()
        self.assertFalse(is_valid_after)
        self.assertEqual(faulty_idx_after, 1)
        self.assertTrue("tampered" in msg_after.lower() or "corrupted" in msg_after.lower())

        # Restore chain
        restore_res = self.blockchain.restore_tampered_blocks()
        self.assertEqual(restore_res["status"], "RESTORED")
        is_valid_restored, _, _ = self.blockchain.validate_chain()
        self.assertTrue(is_valid_restored)

    # -------------------------------------------------------------
    # 4. AI Counterfeit Detection Engine Tests
    # -------------------------------------------------------------

    def test_ai_counterfeit_price_undercut_anomaly(self):
        """Verify AI detector flags extreme price undercutting counterfeit."""
        prediction = self.ai_engine.predict_authenticity(
            product_id="PRD-APPL-SAMPLE-1234",
            brand="Apple",
            offered_price=35.00,  # Extreme discount vs $1199 MSRP
            retailer_name="Unknown Shady Merchant",
            current_location="San Francisco, CA"
        )
        self.assertLess(prediction["authenticity_percentage"], 60.0)
        self.assertIn(prediction["risk_tier"], ["MEDIUM_RISK", "HIGH_RISK"])
        self.assertTrue(any("price anomaly" in flag.lower() for flag in prediction["risk_flags"]))

    def test_ai_counterfeit_impossible_travel_anomaly(self):
        """Verify AI detector flags impossible travel velocity (Cloned QR Code attack)."""
        velocity_result = self.ai_engine.evaluate_transit_velocity(
            last_scan_location="Cupertino, CA, USA",
            last_scan_timestamp=time.time() - 60,  # 1 minute ago
            current_location="Tokyo, Japan",
            current_timestamp=time.time()
        )
        self.assertTrue(velocity_result["is_anomaly"])
        self.assertGreater(velocity_result["velocity_kmh"], 1000)
        self.assertIn("Impossible travel velocity", velocity_result["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
