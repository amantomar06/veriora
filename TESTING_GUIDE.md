# Testing & Quality Assurance Guide: AuthentiChain

This guide documents the verification procedures, automated unit tests, manual test scenarios, and security validation checks for the **AuthentiChain** E-Commerce Product Authenticity Platform.

---

## 1. Automated Unit & Integration Tests

The project includes an automated test suite implemented in `tests/test_blockchain.py` using Python's built-in `unittest` framework.

### How to Run Automated Tests
Open PowerShell or Command Prompt in the project directory (`c:\Users\ASUS\Desktop\XYXX`) and execute:

```powershell
python -m unittest tests/test_blockchain.py -v
```
*(Or run `run.bat` and select Option `2`)*

### Test Results Matrix
All 12 test cases pass with a 100% success rate:

```
test_ai_counterfeit_impossible_travel_anomaly ... ok
test_ai_counterfeit_price_undercut_anomaly ... ok
test_digital_signature_verification ... ok
test_genesis_block_creation ... ok
test_invalid_digital_signature_rejected ... ok
test_invalid_duplicate_product_registration_rejected ... ok
test_invalid_unauthorized_creator_rejected ... ok
test_merkle_tree_calculation ... ok
test_proof_of_work_mining ... ok
test_tamper_detection_invalidates_blockchain ... ok
test_valid_and_invalid_custody_transfer ... ok
test_valid_product_registration ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.013s
OK
```

---

## 2. Test Case Specifications (Deliverable 7)

### Test Case 1: Genesis Block Verification
- **Test ID:** TC-GENESIS-01
- **Objective:** Ensure the root of trust is created with canonical parameters.
- **Input:** Initialize `Blockchain(difficulty=2)`.
- **Expected Outcome:** Block index 0, previous hash `0`*64, block hash starting with `00`.
- **Assertion:** `self.assertEqual(genesis.index, 0)` and `genesis.hash.startswith("00")`.

### Test Case 2: Proof-of-Work Consensus Verification
- **Test ID:** TC-POW-02
- **Objective:** Verify PoW difficulty enforcement.
- **Input:** Call `block.mine_block(difficulty=2)`.
- **Expected Outcome:** Increment nonce until SHA-256 starts with `00`.
- **Assertion:** `self.assertTrue(block.hash.startswith("00"))`.

### Test Case 3: Merkle Tree Data Integrity
- **Test ID:** TC-MERKLE-03
- **Objective:** Verify Merkle root sensitivity to transaction alteration.
- **Input:** Compute Merkle root for `[Tx1, Tx2]`, then tamper `Tx2.amount = 9999`.
- **Expected Outcome:** Computed Merkle root differs from original.
- **Assertion:** `self.assertNotEqual(root1, root_tampered)`.

### Test Case 4: Digital Signature Non-Repudiation
- **Test ID:** TC-SIG-04
- **Objective:** Verify cryptographic signature integrity.
- **Input:** Sign payload using `KeyManager.sign(priv, payload)`; attempt verification with altered payload.
- **Expected Outcome:** Returns `True` for valid payload, `False` for altered payload.
- **Assertion:** `self.assertFalse(KeyManager.verify(pub, altered_payload, sig, priv))`.

### Test Case 5: Duplicate Product ID Prevention (Smart Contract)
- **Test ID:** TC-SC-DUP-05
- **Objective:** Prevent counterfeiters from registering an existing product ID twice.
- **Input:** Register product `PRD-AAPL-DUP`, then submit identical registration.
- **Expected Outcome:** Second registration throws `SmartContractError: Rejected: Product is already registered`.
- **Assertion:** `self.assertRaises(SmartContractError)`.

### Test Case 6: Role-Based Access Control (RBAC)
- **Test ID:** TC-SC-RBAC-06
- **Objective:** Ensure only authorized `MANUFACTURER`s can mint products.
- **Input:** Distributor entity `DST-101` attempts to mint a new product.
- **Expected Outcome:** Transaction rejected with error: `Only authorized MANUFACTURERS can mint`.
- **Assertion:** `self.assertRaises(SmartContractError)`.

### Test Case 7: Unauthorized Custody Transfer Prevention
- **Test ID:** TC-SC-AUTH-07
- **Objective:** Ensure an actor cannot transfer inventory they do not own.
- **Input:** Entity A attempts to transfer custody of an item currently owned by Entity B.
- **Expected Outcome:** Smart contract throws `Unauthorized transfer! Current owner is Entity B`.
- **Assertion:** `self.assertRaises(SmartContractError)`.

### Test Case 8: Blockchain Tamper Detection (Attack Simulation)
- **Test ID:** TC-CHAIN-TAMPER-08
- **Objective:** Prove immutability when database records are maliciously altered.
- **Input:** Call `blockchain.tamper_block_for_testing(1, "COUNTERFEIT_DATA")`.
- **Expected Outcome:** `blockchain.validate_chain()` returns `False` and points to Block #1.
- **Assertion:** `self.assertFalse(is_valid_after)` and `self.assertEqual(faulty_idx, 1)`.

### Test Case 9: AI Price Anomaly Detection
- **Test ID:** TC-AI-PRICE-09
- **Objective:** Detect counterfeits sold at suspicious deep discounts.
- **Input:** Test iPhone ($1199 MSRP) sold for $35.00.
- **Expected Outcome:** AI authenticity score $<60\%$, risk tier = `HIGH_RISK`.
- **Assertion:** `self.assertLess(prediction["authenticity_percentage"], 60.0)`.

### Test Case 10: AI Impossible Travel Velocity Anomaly
- **Test ID:** TC-AI-VELOCITY-10
- **Objective:** Detect cloned QR codes scanned in distant locations simultaneously.
- **Input:** Scan in Cupertino, CA, then scan in Tokyo, Japan 60 seconds later.
- **Expected Outcome:** Transit velocity $>1000\text{ km/h}$; flags `Impossible travel velocity`.
- **Assertion:** `self.assertTrue(velocity_result["is_anomaly"])`.

---

## 3. Manual Interactive UI Testing Guide

### Step 1: Start the Application
Run `run.bat` or execute in PowerShell:
```powershell
python server.py
```
Open your browser to `http://localhost:8000`.

### Step 2: Test Consumer Verification
1. Click the **"🔍 Consumer Verification"** tab.
2. Under "Quick Test Samples", click **"🏷️ Apple: PRD-APPL-..."**.
3. Click **"🛡️ Query Blockchain & AI Engine"**.
4. Observe:
   - Green Shield: `100% GENUINE PRODUCT VERIFIED ON BLOCKCHAIN`.
   - Complete Provenance Timeline (Registered $\to$ In Transit $\to$ At Retailer).
   - AI Confidence: `100.0%` Genuine.
5. Next, click **"🚨 Test Fake ID (Unregistered)"**.
6. Observe:
   - Red Banner: `COUNTERFEIT / UNREGISTERED PRODUCT`.
   - Zero block confirmations found.
   - AI score drops to `0.0%`.

### Step 3: Test Live Tampering & Chain Recovery
1. Click the **"⛓️ Blockchain Explorer & Tamper Lab"** tab.
2. In the "Tamper Demonstration Lab", select **Block #1**.
3. Click **"⚠️ Inject Tampered Data (Simulate Fraud)"**.
4. Observe:
   - The top status pill immediately flashes: `⚠️ CORRUPTION DETECTED at Block #1!`.
   - The chain turns red at Block #1.
   - Error log explains that the Merkle Root and SHA-256 hash validation failed.
5. Click **"🛡️ Restore Ledger Integrity"**.
6. Observe:
   - The ledger immediately returns to `100% VALID (Green)`.

