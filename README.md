# AuthentiChain: E-Commerce Product Authenticity Blockchain System

A product-registration, supply-chain provenance, and consumer verification system built using an educational blockchain framework, smart contract state machine, and AI counterfeit anomaly detection engine.

---

## 🌟 Key Features

- **Decentralized Ledger (PoW Consensus):** Blocks linked with SHA-256 hashes, Proof-of-Work mining, and Merkle tree transaction proofs.
- **Smart Contract Governance:** Role-Based Access Control (RBAC) ensuring only authorized brand manufacturers can mint products, and only verified custodians can transfer inventory.
- **Asymmetric Cryptographic Signatures:** Digital signatures for transactions ensuring non-repudiation and origin proof.
- **AI Counterfeit Anomaly Detection:** Multi-factor analysis evaluating serial number Shannon entropy, impossible travel velocity (cloned QR codes), and price undercutting.
- **Interactive Web Interface:** Modern, responsive single-page web app with real-time verification shield, QR code rendering, and live blockchain visualizer.
- **Tamper Demonstration Lab:** Educational sandbox allowing users to inject counterfeit data into a block and watch the blockchain immediately detect and report the cryptographic corruption.

---

## 📋 Common Implementation Requirements Mapping

| Deliverable | Description | Implementation Location |
|---|---|---|
| **1. Problem Definition** | Counterfeit challenges in e-commerce and why blockchain is suitable | [PROJECT_REPORT.md](file:///c:/Users/ASUS/Desktop/XYXX/PROJECT_REPORT.md#L18-L46) |
| **2. System Design** | Users, components, and transaction flow | [ARCHITECTURE.md](file:///c:/Users/ASUS/Desktop/XYXX/ARCHITECTURE.md), [PROJECT_REPORT.md](file:///c:/Users/ASUS/Desktop/XYXX/PROJECT_REPORT.md#L48-L100) |
| **3. Blockchain Implementation** | Blocks, hashing, linking, and PoW consensus | [core/block.py](file:///c:/Users/ASUS/Desktop/XYXX/core/block.py), [core/blockchain.py](file:///c:/Users/ASUS/Desktop/XYXX/core/blockchain.py) |
| **4. Data Integrity** | SHA-256, Merkle roots, digital signatures, UPI checksum | [core/crypto_engine.py](file:///c:/Users/ASUS/Desktop/XYXX/core/crypto_engine.py) |
| **5. Smart Contracts** | Programmable rules, RBAC, state transitions | [core/smart_contract.py](file:///c:/Users/ASUS/Desktop/XYXX/core/smart_contract.py) |
| **6. User Interface** | Responsive web interface for minting, transfers, and scanning | [static/index.html](file:///c:/Users/ASUS/Desktop/XYXX/static/index.html), [static/app.js](file:///c:/Users/ASUS/Desktop/XYXX/static/app.js), [static/style.css](file:///c:/Users/ASUS/Desktop/XYXX/static/style.css) |
| **7. Testing** | Valid vs invalid transactions, access control, tamper tests | [tests/test_blockchain.py](file:///c:/Users/ASUS/Desktop/XYXX/tests/test_blockchain.py), [TESTING_GUIDE.md](file:///c:/Users/ASUS/Desktop/XYXX/TESTING_GUIDE.md) |
| **8. Documentation** | Project report, architecture diagrams, and test suite | [PROJECT_REPORT.md](file:///c:/Users/ASUS/Desktop/XYXX/PROJECT_REPORT.md), [ARCHITECTURE.md](file:///c:/Users/ASUS/Desktop/XYXX/ARCHITECTURE.md) |

---

## 🚀 Quickstart Guide

### Option 1: 1-Click Launch on Windows
Double-click `run.bat` in this folder:
- Press `1` to start the Web Server and launch the UI in your browser (`http://localhost:8000`).
- Press `2` to run the 12 automated unit and security tests.
- Press `3` to launch the interactive terminal CLI demonstration.

### Option 2: Command Line Execution

**1. Start the Web Server & Application:**
```powershell
python server.py
```
Then open [http://localhost:8000](http://localhost:8000) in your browser.

**2. Run Automated Test Suite:**
```powershell
python -m unittest tests/test_blockchain.py -v
```

**3. Run CLI Demonstration:**
```powershell
python demo_cli.py
```

---

## 📁 Project Structure

```
c:\Users\ASUS\Desktop\XYXX\
├── core/
│   ├── block.py            # Block structure, SHA-256 header hashing, PoW mining
│   ├── blockchain.py       # Distributed ledger, chain validation, tamper simulator
│   ├── crypto_engine.py    # Merkle tree, KeyManager, digital signatures, UPI checksums
│   ├── smart_contract.py   # ProductAuthenticityContract (RBAC, state machine)
│   └── ai_engine.py        # Shannon entropy, travel velocity & price anomaly model
├── static/
│   ├── index.html          # Responsive Web UI (Single Page App)
│   ├── app.js              # Frontend logic, QR code renderer, API client
│   └── style.css           # Glassmorphism styling, responsive layout
├── tests/
│   └── test_blockchain.py  # 12 automated unit & security tests (100% pass)
├── server.py               # REST API HTTP server (Zero external dependencies)
├── demo_cli.py             # Console presentation and test runner
├── run.bat                 # Windows 1-click launcher
├── PROJECT_REPORT.md       # Comprehensive academic project report
├── ARCHITECTURE.md         # System architecture & sequence diagrams (Mermaid)
├── TESTING_GUIDE.md        # Step-by-step test specifications & QA manual
└── README.md               # Quickstart and deliverables summary
```
