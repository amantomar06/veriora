"""
Smart Contract: Product Authenticity & Chain of Custody
Enforces programmable rules, role-based access control (RBAC),
and state transition validation for all transactions.
"""

import time
from typing import Dict, Any, List, Optional
from core.crypto_engine import sha256, KeyManager, verify_product_id_checksum


class SmartContractError(Exception):
    """Raised when a smart contract rule is violated."""
    pass


class ProductAuthenticityContract:
    """
    Implements the programmable business logic and state machine
    for registering products, tracking custody, and validating authenticity.
    """

    # Permitted Lifecycle States
    STATE_REGISTERED = "REGISTERED"
    STATE_IN_TRANSIT = "IN_TRANSIT"
    STATE_AT_DISTRIBUTOR = "AT_DISTRIBUTOR"
    STATE_AT_RETAILER = "AT_RETAILER"
    STATE_SOLD = "SOLD"
    STATE_FLAGGED_COUNTERFEIT = "FLAGGED_COUNTERFEIT"
    STATE_RECALLED = "RECALLED"

    VALID_TRANSITIONS = {
        STATE_REGISTERED: [STATE_IN_TRANSIT, STATE_AT_DISTRIBUTOR, STATE_RECALLED],
        STATE_IN_TRANSIT: [STATE_AT_DISTRIBUTOR, STATE_AT_RETAILER, STATE_RECALLED],
        STATE_AT_DISTRIBUTOR: [STATE_IN_TRANSIT, STATE_AT_RETAILER, STATE_RECALLED],
        STATE_AT_RETAILER: [STATE_SOLD, STATE_RECALLED],
        STATE_SOLD: [STATE_FLAGGED_COUNTERFEIT],
        STATE_RECALLED: [],
        STATE_FLAGGED_COUNTERFEIT: []
    }

    def __init__(self):
        # Global state registry: product_id -> state record
        self.products: Dict[str, Dict[str, Any]] = {}
        # History of transactions per product: product_id -> list of transactions
        self.product_history: Dict[str, List[Dict[str, Any]]] = {}
        # Authorized actors: public_key -> entity profile
        self.authorized_entities: Dict[str, Dict[str, Any]] = {}
        # Registry of known private keys for system testing and validation
        self.entity_keys: Dict[str, Dict[str, str]] = {}
        
        self._initialize_default_entities()

    def _initialize_default_entities(self):
        """Initializes standard demo stakeholders with cryptographic credentials."""
        default_actors = [
            ("MFR-001", "Apple Official Inc.", "MANUFACTURER", "Cupertino, CA, USA"),
            ("MFR-002", "Nike Global HQ", "MANUFACTURER", "Beaverton, OR, USA"),
            ("MFR-003", "Pfizer Pharmaceuticals", "MANUFACTURER", "New York, NY, USA"),
            ("MFR-004", "Sony Electronics", "MANUFACTURER", "Tokyo, Japan"),
            ("DST-101", "Global Express Logistics", "DISTRIBUTOR", "Chicago Hub, IL"),
            ("DST-102", "EuroTrans Freight", "DISTRIBUTOR", "Frankfurt Depot, DE"),
            ("RET-201", "BestBuy Retail Store #442", "RETAILER", "San Francisco, CA"),
            ("RET-202", "Amazon Fulfillment Center", "RETAILER", "Seattle, WA"),
            ("RET-203", "CVS Pharmacy Store #110", "RETAILER", "Boston, MA"),
            ("AUD-901", "Fair Trade & Anti-Counterfeit Bureau", "AUDITOR", "Geneva, CH")
        ]

        for entity_id, name, role, location in default_actors:
            priv, pub = KeyManager.generate_keypair(entity_id)
            self.entity_keys[entity_id] = {
                "private_key": priv,
                "public_key": pub
            }
            self.authorized_entities[pub] = {
                "entity_id": entity_id,
                "name": name,
                "role": role,
                "location": location,
                "registered_at": time.time()
            }

    def register_entity(self, entity_id: str, name: str, role: str, location: str) -> Dict[str, str]:
        """Registers a new authorized participant in the supply chain network."""
        if role not in ["MANUFACTURER", "DISTRIBUTOR", "RETAILER", "AUDITOR"]:
            raise SmartContractError(f"Invalid role '{role}'. Must be MANUFACTURER, DISTRIBUTOR, RETAILER, or AUDITOR.")
        
        priv, pub = KeyManager.generate_keypair(entity_id)
        self.entity_keys[entity_id] = {
            "private_key": priv,
            "public_key": pub
        }
        self.authorized_entities[pub] = {
            "entity_id": entity_id,
            "name": name,
            "role": role,
            "location": location,
            "registered_at": time.time()
        }
        return {"entity_id": entity_id, "public_key": pub, "private_key": priv}

    def validate_and_execute(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes programmable smart contract validation logic against a transaction.
        Updates state if valid, or raises SmartContractError if rules are violated.
        """
        tx_type = tx.get("type")

        if tx_type == "PRODUCT_REGISTRATION":
            return self._execute_registration(tx)
        elif tx_type == "CUSTODY_TRANSFER":
            return self._execute_transfer(tx)
        elif tx_type == "STATUS_UPDATE":
            return self._execute_status_update(tx)
        elif tx_type == "FLAG_COUNTERFEIT":
            return self._execute_flag_counterfeit(tx)
        else:
            raise SmartContractError(f"Unknown transaction type: {tx_type}")

    def _execute_registration(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart Contract Rule 1: Origin Authenticity & Identity Verification
        Smart Contract Rule 2: Non-Duplication of Product IDs
        """
        product_id = tx.get("product_id")
        sender_pub = tx.get("sender_public_key")
        payload = tx.get("payload", {})
        signature = tx.get("signature")

        # 1. Check Product ID formatting and cryptographic checksum
        if not product_id or not verify_product_id_checksum(product_id):
            raise SmartContractError(f"Rejected: Invalid or forged Product ID '{product_id}'. Checksum failed.")

        # 2. Check if product already exists
        if product_id in self.products:
            raise SmartContractError(f"Rejected: Product '{product_id}' is already registered. Duplicate registration disallowed.")

        # 3. Check sender identity and role
        entity = self.authorized_entities.get(sender_pub)
        if not entity:
            raise SmartContractError("Rejected: Sender public key is not registered on the blockchain network.")
        if entity["role"] != "MANUFACTURER":
            raise SmartContractError(f"Rejected: Only authorized MANUFACTURERS can mint products. Sender role is '{entity['role']}'.")

        # 4. Check digital signature
        entity_id = entity["entity_id"]
        priv_key = self.entity_keys[entity_id]["private_key"]
        if not KeyManager.verify(sender_pub, payload, signature, priv_key):
            raise SmartContractError("Rejected: Digital signature verification failed! Transaction may be forged.")

        # 5. Required payload fields
        required_fields = ["product_name", "brand", "batch_number", "manufacture_date", "specs"]
        for field in required_fields:
            if not payload.get(field):
                raise SmartContractError(f"Rejected: Missing required product specification field '{field}'.")

        # Update contract state
        new_product = {
            "product_id": product_id,
            "product_name": payload["product_name"],
            "brand": payload["brand"],
            "batch_number": payload["batch_number"],
            "manufacture_date": payload["manufacture_date"],
            "specs": payload["specs"],
            "registered_by": entity["name"],
            "manufacturer_id": entity["entity_id"],
            "current_owner": entity["name"],
            "current_owner_pub": sender_pub,
            "current_location": entity["location"],
            "current_status": self.STATE_REGISTERED,
            "registration_timestamp": tx.get("timestamp", time.time()),
            "authenticity_hash": sha256(f"{product_id}:{payload['brand']}:{payload['batch_number']}:{sender_pub}"),
            "tamper_detected": False,
            "recalled": False
        }

        self.products[product_id] = new_product
        self.product_history[product_id] = [tx]
        return new_product

    def _execute_transfer(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Smart Contract Rule 3: Valid Custody Handover
        Smart Contract Rule 4: Ownership Verification
        """
        product_id = tx.get("product_id")
        sender_pub = tx.get("sender_public_key")
        payload = tx.get("payload", {})
        signature = tx.get("signature")

        if product_id not in self.products:
            raise SmartContractError(f"Rejected: Product '{product_id}' does not exist on blockchain.")

        current_record = self.products[product_id]

        if current_record.get("recalled"):
            raise SmartContractError(f"Rejected: Product '{product_id}' has been recalled. Further transfers blocked.")

        # Verify sender is the current custodian
        if current_record["current_owner_pub"] != sender_pub:
            sender_name = self.authorized_entities.get(sender_pub, {}).get("name", "Unknown")
            raise SmartContractError(
                f"Rejected: Unauthorized transfer! Current owner is '{current_record['current_owner']}', but sender is '{sender_name}'."
            )

        # Verify signature
        sender_entity = self.authorized_entities.get(sender_pub)
        if not sender_entity:
            raise SmartContractError("Rejected: Unrecognized sender entity.")
        priv_key = self.entity_keys[sender_entity["entity_id"]]["private_key"]
        if not KeyManager.verify(sender_pub, payload, signature, priv_key):
            raise SmartContractError("Rejected: Digital signature mismatch on custody transfer.")

        recipient_pub = payload.get("recipient_public_key")
        recipient_entity = self.authorized_entities.get(recipient_pub)
        if not recipient_entity:
            raise SmartContractError("Rejected: Recipient is not a registered supply chain node.")

        next_status = payload.get("next_status", self.STATE_IN_TRANSIT)
        if next_status not in self.VALID_TRANSITIONS.get(current_record["current_status"], []):
            raise SmartContractError(
                f"Rejected: Invalid state transition from '{current_record['current_status']}' to '{next_status}'."
            )

        # Update state
        current_record["current_owner"] = recipient_entity["name"]
        current_record["current_owner_pub"] = recipient_pub
        current_record["current_location"] = payload.get("location", recipient_entity["location"])
        current_record["current_status"] = next_status

        self.product_history[product_id].append(tx)
        return current_record

    def _execute_status_update(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Updates product status (e.g., Retail Store received, Sold to Consumer)."""
        product_id = tx.get("product_id")
        sender_pub = tx.get("sender_public_key")
        payload = tx.get("payload", {})

        if product_id not in self.products:
            raise SmartContractError(f"Product '{product_id}' not found.")

        current_record = self.products[product_id]
        new_status = payload.get("status")

        if new_status not in self.VALID_TRANSITIONS.get(current_record["current_status"], []):
            raise SmartContractError(
                f"Invalid transition from {current_record['current_status']} to {new_status}"
            )

        current_record["current_status"] = new_status
        if payload.get("location"):
            current_record["current_location"] = payload["location"]

        self.product_history[product_id].append(tx)
        return current_record

    def _execute_flag_counterfeit(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Flags an attempted counterfeit or duplicate scan."""
        product_id = tx.get("product_id")
        payload = tx.get("payload", {})
        
        if product_id in self.products:
            self.products[product_id]["current_status"] = self.STATE_FLAGGED_COUNTERFEIT
            self.products[product_id]["tamper_detected"] = True
            self.product_history[product_id].append(tx)
            return self.products[product_id]
        return {"status": "FLAGGED", "product_id": product_id, "reason": payload.get("reason")}

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves verified on-chain product record."""
        return self.products.get(product_id)

    def get_history(self, product_id: str) -> List[Dict[str, Any]]:
        """Retrieves complete chronological chain of custody for a product."""
        return self.product_history.get(product_id, [])

