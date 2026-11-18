# Architecture & Technical Specifications: AuthentiChain

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Client_Layer ["Client & Interface Layer"]
        UI_Consumer["Consumer Web Portal\n(QR Scanner & Lookup)"]
        UI_MFR["Manufacturer Studio\n(Minting & Certificate)"]
        UI_Supply["Supply Chain Portal\n(Custody Handover)"]
        UI_AI["AI Anomaly Workbench\n(Entropy & Velocity Risk)"]
        UI_Explorer["Blockchain Explorer\n& Tamper Testbed"]
    end

    subgraph API_Layer ["HTTP Application Layer (server.py)"]
        Router["REST API Router & Request Handler"]
        Endpoints["/api/product/register\n/api/product/transfer\n/api/product/verify\n/api/ai/predict\n/api/chain\n/api/tamper"]
    end

    subgraph Logic_Layer ["Business Logic & Intelligence"]
        Contract["Smart Contract Engine\n(ProductAuthenticityContract)\n• Role-Based Access Control (RBAC)\n• Invariant Rule Verification\n• State Machine Enforcer"]
        AI_Engine["AI Anomaly Detector\n• Shannon Entropy Classifier\n• Transit Velocity (Cloned QR)\n• Price vs MSRP Deviation"]
        Crypto_Engine["Cryptographic Engine\n• KeyManager (HMAC/ECDSA)\n• SHA-256 Hashing\n• Merkle Tree Builder\n• UPI Checksum Verifier"]
    end

    subgraph Ledger_Layer ["Distributed Ledger Layer (core/blockchain.py)"]
        Chain["Immutable Blockchain\n• Genesis Block #0\n• Mined Product Blocks #1..N"]
        PoW["Proof-of-Work Consensus Engine\n(Difficulty = 2 Leading Zeros)"]
        Tx_Pool["Pending Transactions Mempool"]
    end

    UI_Consumer --> Router
    UI_MFR --> Router
    UI_Supply --> Router
    UI_AI --> Router
    UI_Explorer --> Router

    Router --> Endpoints
    Endpoints --> Contract
    Endpoints --> AI_Engine
    Endpoints --> Crypto_Engine

    Contract --> Tx_Pool
    Crypto_Engine --> Contract
    Tx_Pool --> PoW
    PoW --> Chain
```

---

## 2. Transaction Flow & Handover Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor MFR as Brand Manufacturer
    actor DST as Logistics Hub
    actor RET as Retail Store
    actor CNS as Consumer
    participant API as REST API Server
    participant SC as Smart Contract
    participant BC as Blockchain (PoW)

    Note over MFR,BC: Stage 1: Product Origin Minting
    MFR->>API: POST /api/product/register (Product Specs, Keypair)
    API->>SC: validate_and_execute(Registration_Tx)
    SC->>SC: Check Role == MANUFACTURER & Non-Duplication
    SC->>BC: Add to Transaction Pool & Mine Block #1
    BC-->>API: Block Mined & Authenticity Hash Stored
    API-->>MFR: Return UPI & Cryptographic QR Tag

    Note over MFR,BC: Stage 2: Supply Chain Handover
    MFR->>API: POST /api/product/transfer (MFR -> DST, IN_TRANSIT)
    API->>SC: Verify MFR Signature & Custody Ownership
    SC->>BC: Mine Block #2 (Custody -> Global Logistics)
    API-->>DST: Inventory In Transit

    Note over DST,BC: Stage 3: Retail Delivery
    DST->>API: POST /api/product/transfer (DST -> RET, AT_RETAILER)
    API->>SC: Verify DST Signature & Custody Ownership
    SC->>BC: Mine Block #3 (Custody -> BestBuy Retailer)
    API-->>RET: Stocked on Retail Shelf

    Note over CNS,BC: Stage 4: Consumer Verification
    CNS->>API: GET /api/product/verify?id=PRD-XXXX
    API->>SC: Retrieve Verified Product Record
    API->>BC: Confirm Block Anchors (Blocks 1, 2, 3)
    API->>API: Run AI Anomaly Inference (Entropy, Velocity, Price)
    API-->>CNS: Display 100% GENUINE SHIELD & Complete Provenance Timeline
```

---

## 3. Blockchain Block Linking & Merkle Tree Architecture

```mermaid
flowchart LR
    subgraph Block_0 ["Genesis Block #0"]
        H0["Hash: 00b221...\nPrev: 000000...\nNonce: 104\nMerkle: e554d4..."]
    end

    subgraph Block_1 ["Block #1 (Minting)"]
        H1["Hash: 001077...\nPrev: 00b221...\nNonce: 214\nMerkle: 749d31..."]
        MR1["Merkle Root 749d31..."]
        Tx1["Tx 1: Mint iPhone"]
        MR1 --> Tx1
    end

    subgraph Block_2 ["Block #2 (Logistics Transfer)"]
        H2["Hash: 0089a4...\nPrev: 001077...\nNonce: 351\nMerkle: 8bfa92..."]
        MR2["Merkle Root 8bfa92..."]
        Tx2["Tx 2: Handover to Logistics"]
        MR2 --> Tx2
    end

    H0 -->|Previous Hash Link| H1
    H1 -->|Previous Hash Link| H2
```

---

## 4. Smart Contract State Machine

```mermaid
stateDiagram-v2
    [*] --> REGISTERED: Minted by Manufacturer
    REGISTERED --> IN_TRANSIT: Handover to Logistics
    IN_TRANSIT --> AT_DISTRIBUTOR: Warehouse Arrival
    AT_DISTRIBUTOR --> IN_TRANSIT: Dispatched to Retail
    IN_TRANSIT --> AT_RETAILER: Stocked in Store
    AT_RETAILER --> SOLD: Consumer Purchase
    SOLD --> [*]: Consumer Verified
    
    REGISTERED --> RECALLED: Safety Recall
    IN_TRANSIT --> RECALLED: Safety Recall
    AT_RETAILER --> RECALLED: Safety Recall
    
    SOLD --> FLAGGED_COUNTERFEIT: Cloned Scan Detected
    IN_TRANSIT --> FLAGGED_COUNTERFEIT: Stolen Goods Detected
```

---

## 5. API Schema Specification

### 5.1 POST `/api/product/register`
**Request Payload:**
```json
{
  "entity_id": "MFR-001",
  "product_name": "iPhone 16 Pro Max 256GB",
  "brand": "Apple",
  "category": "Electronics",
  "batch_number": "BATCH-AAPL-2026A",
  "manufacture_date": "2026-11-18",
  "specs": {
    "color": "Titanium",
    "msrp_usd": 1199.00
  }
}
```

**Success Response (200 OK):**
```json
{
  "status": "SUCCESS",
  "product_id": "PRD-APPL-ELE-6CC5D5-52E3FD-373A",
  "transaction": {
    "status": "ACCEPTED",
    "tx_id": "TX-56CE4D14BEEBBEAF"
  },
  "mining": {
    "block_index": 1,
    "block_hash": "001077ad49d12702160dc06e27200812a717eace85a00f3a0127792e0af5a60e"
  }
}
```

### 5.2 GET `/api/product/verify?id=<product_id>`
**Success Response (200 OK):**
```json
{
  "is_genuine": true,
  "product_id": "PRD-APPL-ELE-6CC5D5-52E3FD-373A",
  "verdict": "100% GENUINE PRODUCT VERIFIED ON BLOCKCHAIN",
  "product_details": {
    "product_name": "iPhone 16 Pro Max 256GB",
    "brand": "Apple",
    "batch_number": "BATCH-AAPL-2026A",
    "current_owner": "BestBuy Retail Store #442",
    "current_status": "AT_RETAILER",
    "current_location": "BestBuy Retail Store #442, San Francisco, CA"
  },
  "history": [
    { "type": "PRODUCT_REGISTRATION", "timestamp": 1731908000 },
    { "type": "CUSTODY_TRANSFER", "timestamp": 1731908500 }
  ],
  "ai_prediction": {
    "authenticity_percentage": 100.0,
    "classification": "GENUINE",
    "risk_tier": "LOW_RISK",
    "entropy": 3.619
  }
}
```
