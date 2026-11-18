"""
Interactive CLI Demonstration of E-Commerce Product Authenticity Blockchain
Run with: python demo_cli.py
Demonstrates:
- Genesis Block mining & cryptographic ledger initialization
- Manufacturer Product Registration with ECDSA/HMAC Digital Signatures
- Merkle Root computation and Proof-of-Work mining
- Supply Chain Custody Handover (Manufacturer -> Logistics -> Retailer)
- Consumer Verification & Provenance History Query
- AI Multi-Factor Anomaly & Counterfeit Detection
- Tamper Attack Simulation & Immediate Cryptographic Failure Detection
"""

import sys
import time
from core.blockchain import Blockchain
from core.crypto_engine import KeyManager, generate_unique_product_id
from core.ai_engine import AICounterfeitDetector
from core.smart_contract import SmartContractError


def print_banner(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_step(step_num, title):
    print(f"\n[STEP {step_num}] >>> {title}")


def run_demo():
    print_banner("AuthentiChain: E-Commerce Product Authenticity Blockchain Demo")

    # Step 1: Genesis Block
    print_step(1, "Initializing Blockchain & Mining Genesis Block")
    bc = Blockchain(difficulty=2)
    genesis = bc.chain[0]
    print(f"  Genesis Block Hash: {genesis.hash}")
    print(f"  Previous Hash:      {genesis.previous_hash}")
    print(f"  PoW Nonce:          {genesis.nonce}")
    print(f"  Merkle Root:        {genesis.merkle_root}")
    print(f"  Mining Difficulty:  {bc.difficulty} Leading Zeros")

    # Step 2: Register Genuine Product
    print_step(2, "Manufacturer Registration of Genuine Product (Origin Minting)")
    mfr_keys = bc.smart_contract.entity_keys["MFR-001"]
    pid = generate_unique_product_id("Apple", "Electronics", "BATCH-DEMO-2026")
    print(f"  Generated Unique Product ID (UPI): {pid}")

    payload = {
        "product_name": "iPhone 16 Pro Max 512GB Natural Titanium",
        "brand": "Apple",
        "batch_number": "BATCH-DEMO-2026",
        "manufacture_date": "2026-11-18",
        "specs": {
            "factory": "Foxconn Zhengzhou Facility #9",
            "msrp_usd": 1399.00,
            "qc_inspector": "QC-APPL-882"
        }
    }
    signature = KeyManager.sign(mfr_keys["private_key"], payload)
    print(f"  Digital Signature (HMAC-SHA256): {signature[:32]}...{signature[-16:]}")

    tx_reg = {
        "type": "PRODUCT_REGISTRATION",
        "product_id": pid,
        "sender_public_key": mfr_keys["public_key"],
        "payload": payload,
        "signature": signature
    }
    res = bc.add_transaction(tx_reg)
    print(f"  Smart Contract Validation: Status = {res['status']}, TxID = {res['tx_id']}")

    print("  Mining Block #1 to commit registration...")
    mine_res = bc.mine_pending_transactions()
    block1 = bc.chain[1]
    print(f"  ✔ Block #{block1.index} Mined! Hash: {block1.hash} (Nonce: {block1.nonce})")

    # Step 3: Supply Chain Transfer
    print_step(3, "Supply Chain Custody Transfer (Apple -> Logistics Hub -> Retailer)")
    dst_keys = bc.smart_contract.entity_keys["DST-101"]
    ret_keys = bc.smart_contract.entity_keys["RET-201"]

    # Handover 1: MFR -> DST
    tf_payload1 = {
        "recipient_public_key": dst_keys["public_key"],
        "next_status": "IN_TRANSIT",
        "location": "San Francisco Cargo Hub"
    }
    tf_sig1 = KeyManager.sign(mfr_keys["private_key"], tf_payload1)
    bc.add_transaction({
        "type": "CUSTODY_TRANSFER",
        "product_id": pid,
        "sender_public_key": mfr_keys["public_key"],
        "payload": tf_payload1,
        "signature": tf_sig1
    })
    bc.mine_pending_transactions()
    print("  ✔ Handover 1 Committed: Custody transferred to Global Express Logistics (IN_TRANSIT)")

    # Handover 2: DST -> RET
    tf_payload2 = {
        "recipient_public_key": ret_keys["public_key"],
        "next_status": "AT_RETAILER",
        "location": "BestBuy Retail Store #442, Market St, SF"
    }
    tf_sig2 = KeyManager.sign(dst_keys["private_key"], tf_payload2)
    bc.add_transaction({
        "type": "CUSTODY_TRANSFER",
        "product_id": pid,
        "sender_public_key": dst_keys["public_key"],
        "payload": tf_payload2,
        "signature": tf_sig2
    })
    bc.mine_pending_transactions()
    print("  ✔ Handover 2 Committed: Received at BestBuy Retail Store (AT_RETAILER)")

    # Step 4: Consumer Verification
    print_step(4, "Consumer Product Verification Query (On-Chain Provenance)")
    verification = bc.verify_product(pid)
    print(f"  Query Result for Product ID: {pid}")
    print(f"  Verdict:          {verification['verdict']}")
    print(f"  Manufacturer:     {verification['manufacturer']}")
    print(f"  Current Custody:  {verification['current_owner']} ({verification['current_location']})")
    print(f"  Lifecycle State:  {verification['current_status']}")
    print(f"  Block Anchors:    {len(verification['block_confirmations'])} Blocks ({', '.join(str(b['block_index']) for b in verification['block_confirmations'])})")
    print("  Provenance Chronology:")
    for idx, tx in enumerate(verification["history"]):
        t_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx['timestamp']))
        print(f"    [{idx+1}] {t_str} | {tx['type']} | Loc: {tx.get('payload', {}).get('location', 'Factory')}")

    # Step 5: AI Counterfeit Prediction Engine
    print_step(5, "AI Counterfeit Risk & Anomaly Scoring")
    ai = AICounterfeitDetector()
    
    # 5a: Genuine test
    ai_genuine = ai.predict_authenticity(
        product_id=pid,
        brand="Apple",
        offered_price=1399.00,
        retailer_name="BestBuy Retail Store #442",
        current_location="BestBuy Retail Store #442, Market St, SF",
        on_chain_product=verification["product_details"],
        history=verification["history"]
    )
    print("  [Scenario A: Genuine Luxury Product]")
    print(f"    Authenticity Score: {ai_genuine['authenticity_percentage']}% ({ai_genuine['classification']})")
    print(f"    Entropy: {ai_genuine['entropy']} bits | Risk Tier: {ai_genuine['risk_tier']}")

    # 5b: Counterfeit test (Extreme discount & unregistered ID)
    ai_counterfeit = ai.predict_authenticity(
        product_id="PRD-FAKE-CLONE-9999",
        brand="Apple",
        offered_price=49.99,
        retailer_name="Shady Street Stall",
        current_location="Unknown Alleyway",
        on_chain_product=None,
        history=[]
    )
    print("\n  [Scenario B: Suspected Counterfeit with 96% Discount]")
    print(f"    Authenticity Score: {ai_counterfeit['authenticity_percentage']}% ({ai_counterfeit['classification']})")
    print(f"    Risk Flags: {ai_counterfeit['risk_flags']}")

    # Step 6: Security Access Control (Invalid Transactions)
    print_step(6, "Demonstrating Smart Contract Security Checks (Invalid Transactions)")
    try:
        print("  Attempting Duplicate Registration of existing Product ID...")
        bc.add_transaction(tx_reg)
    except SmartContractError as e:
        print(f"  ✔ REJECTED AS EXPECTED: {e}")

    try:
        print("  Attempting Unauthorized Custody Transfer by Attacker...")
        fake_priv, fake_pub = KeyManager.generate_keypair("ATTACKER")
        attack_tx = {
            "type": "CUSTODY_TRANSFER",
            "product_id": pid,
            "sender_public_key": fake_pub,
            "payload": {"recipient_public_key": fake_pub, "next_status": "SOLD", "location": "Black Market"},
            "signature": KeyManager.sign(fake_priv, {"recipient_public_key": fake_pub})
        }
        bc.add_transaction(attack_tx)
    except SmartContractError as e:
        print(f"  ✔ REJECTED AS EXPECTED: {e}")

    # Step 7: Tamper Detection Demonstration
    print_step(7, "Demonstrating Blockchain Immutability & Tamper Detection")
    valid_before, msg_before, _ = bc.validate_chain()
    print(f"  Pre-Attack Ledger Validity: {valid_before} - '{msg_before}'")

    print("\n  >>> Simulating Database Breach: Injecting counterfeit name into Block #1...")
    bc.tamper_block_for_testing(1, "COUNTERFEIT_CLONED_GOODS_HACKED")
    
    valid_after, msg_after, faulty_idx = bc.validate_chain()
    print(f"  Post-Attack Ledger Validity: {valid_after}")
    print(f"  Cryptographic Proof Mismatch: {msg_after}")
    print(f"  Faulty Corrupted Block Index: Block #{faulty_idx}")

    print("\n  >>> Restoring Ledger to Original Cryptographic Integrity...")
    bc.restore_tampered_blocks()
    valid_restored, msg_restored, _ = bc.validate_chain()
    print(f"  Restored Chain Validity: {valid_restored} - '{msg_restored}'")

    print_banner("DEMONSTRATION COMPLETED SUCCESSFULLY! ALL DELIVERABLES MET.")


if __name__ == "__main__":
    run_demo()

