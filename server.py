"""
HTTP REST Server for E-Commerce Product Authenticity Blockchain
Zero external dependencies (uses standard library http.server).
Serves Web UI and provides complete JSON REST APIs for the supply chain network.
"""

import os
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from core.blockchain import Blockchain
from core.crypto_engine import KeyManager, generate_unique_product_id, sha256
from core.smart_contract import SmartContractError
from core.ai_engine import AICounterfeitDetector

# Initialize Global Shared Blockchain and AI Engine
blockchain = Blockchain(difficulty=2)
ai_engine = AICounterfeitDetector()


def seed_demo_data():
    """Populates realistic demo products across different supply chain stages."""
    print("[INIT] Seeding initial supply chain products into blockchain...")

    # 1. Apple iPhone 16 Pro Max (Fully delivered to Retailer)
    mfr_apple = blockchain.smart_contract.entity_keys["MFR-001"]
    dst_logistics = blockchain.smart_contract.entity_keys["DST-101"]
    ret_bestbuy = blockchain.smart_contract.entity_keys["RET-201"]

    pid_iphone = generate_unique_product_id("Apple", "Electronics", "BATCH-AAPL-2026A")
    tx_reg_apple = {
        "type": "PRODUCT_REGISTRATION",
        "product_id": pid_iphone,
        "sender_public_key": mfr_apple["public_key"],
        "payload": {
            "product_name": "iPhone 16 Pro Max 256GB Titanium",
            "brand": "Apple",
            "batch_number": "BATCH-AAPL-2026A",
            "manufacture_date": "2026-09-15",
            "specs": {
                "color": "Natural Titanium",
                "storage": "256GB",
                "msrp_usd": 1199.00,
                "factory": "Foxconn Zhengzhou Plant #4"
            }
        }
    }
    tx_reg_apple["signature"] = KeyManager.sign(mfr_apple["private_key"], tx_reg_apple["payload"])
    blockchain.add_transaction(tx_reg_apple)
    blockchain.mine_pending_transactions()

    # Transfer Apple to Logistics
    tx_tf_1 = {
        "type": "CUSTODY_TRANSFER",
        "product_id": pid_iphone,
        "sender_public_key": mfr_apple["public_key"],
        "payload": {
            "recipient_public_key": dst_logistics["public_key"],
            "next_status": "IN_TRANSIT",
            "location": "San Francisco International Freight Terminal"
        }
    }
    tx_tf_1["signature"] = KeyManager.sign(mfr_apple["private_key"], tx_tf_1["payload"])
    blockchain.add_transaction(tx_tf_1)
    blockchain.mine_pending_transactions()

    # Logistics delivers to BestBuy Retailer
    tx_tf_2 = {
        "type": "CUSTODY_TRANSFER",
        "product_id": pid_iphone,
        "sender_public_key": dst_logistics["public_key"],
        "payload": {
            "recipient_public_key": ret_bestbuy["public_key"],
            "next_status": "AT_RETAILER",
            "location": "BestBuy Retail Store #442, San Francisco, CA"
        }
    }
    tx_tf_2["signature"] = KeyManager.sign(dst_logistics["private_key"], tx_tf_2["payload"])
    blockchain.add_transaction(tx_tf_2)
    blockchain.mine_pending_transactions()

    # 2. Nike Air Jordan 1 Retro (At Logistics Hub)
    mfr_nike = blockchain.smart_contract.entity_keys["MFR-002"]
    pid_nike = generate_unique_product_id("Nike", "Apparel", "BATCH-JORDAN-88")
    tx_reg_nike = {
        "type": "PRODUCT_REGISTRATION",
        "product_id": pid_nike,
        "sender_public_key": mfr_nike["public_key"],
        "payload": {
            "product_name": "Air Jordan 1 High OG Chicago Edition",
            "brand": "Nike",
            "batch_number": "BATCH-JORDAN-88",
            "manufacture_date": "2026-10-01",
            "specs": {
                "size": "US 10.5",
                "colorway": "Varsity Red / Black-White",
                "msrp_usd": 180.00,
                "factory": "Nike Vietnam Facility #12"
            }
        }
    }
    tx_reg_nike["signature"] = KeyManager.sign(mfr_nike["private_key"], tx_reg_nike["payload"])
    blockchain.add_transaction(tx_reg_nike)
    blockchain.mine_pending_transactions()

    # Transfer Nike to Logistics
    tx_nike_dst = {
        "type": "CUSTODY_TRANSFER",
        "product_id": pid_nike,
        "sender_public_key": mfr_nike["public_key"],
        "payload": {
            "recipient_public_key": dst_logistics["public_key"],
            "next_status": "AT_DISTRIBUTOR",
            "location": "Chicago Central Distribution Hub, IL"
        }
    }
    tx_nike_dst["signature"] = KeyManager.sign(mfr_nike["private_key"], tx_nike_dst["payload"])
    blockchain.add_transaction(tx_nike_dst)
    blockchain.mine_pending_transactions()

    # 3. Pfizer Paxlovid Antiviral Medicine (Delivered to CVS Pharmacy)
    mfr_pfizer = blockchain.smart_contract.entity_keys["MFR-003"]
    ret_cvs = blockchain.smart_contract.entity_keys["RET-203"]
    pid_pharma = generate_unique_product_id("Pfizer", "Medicine", "BATCH-PAX-7740")
    tx_reg_pharma = {
        "type": "PRODUCT_REGISTRATION",
        "product_id": pid_pharma,
        "sender_public_key": mfr_pfizer["public_key"],
        "payload": {
            "product_name": "Paxlovid Nirmatrelvir/Ritonavir Co-pack 30 Tablets",
            "brand": "Pfizer",
            "batch_number": "BATCH-PAX-7740",
            "manufacture_date": "2026-08-20",
            "specs": {
                "dosage": "300mg / 100mg",
                "storage_temp": "20°C to 25°C",
                "expiry_date": "2028-08-20",
                "ndc_code": "0069-5318-30",
                "msrp_usd": 45.00
            }
        }
    }
    tx_reg_pharma["signature"] = KeyManager.sign(mfr_pfizer["private_key"], tx_reg_pharma["payload"])
    blockchain.add_transaction(tx_reg_pharma)
    blockchain.mine_pending_transactions()

    # Transfer Pfizer to Logistics
    tx_pharma_dst = {
        "type": "CUSTODY_TRANSFER",
        "product_id": pid_pharma,
        "sender_public_key": mfr_pfizer["public_key"],
        "payload": {
            "recipient_public_key": dst_logistics["public_key"],
            "next_status": "IN_TRANSIT",
            "location": "Boston Regional Cold-Chain Distribution Depot"
        }
    }
    tx_pharma_dst["signature"] = KeyManager.sign(mfr_pfizer["private_key"], tx_pharma_dst["payload"])
    blockchain.add_transaction(tx_pharma_dst)
    blockchain.mine_pending_transactions()

    # Logistics delivers to CVS Pharmacy Store
    tx_pharma_cvs = {
        "type": "CUSTODY_TRANSFER",
        "product_id": pid_pharma,
        "sender_public_key": dst_logistics["public_key"],
        "payload": {
            "recipient_public_key": ret_cvs["public_key"],
            "next_status": "AT_RETAILER",
            "location": "CVS Pharmacy Store #110, Boston, MA"
        }
    }
    tx_pharma_cvs["signature"] = KeyManager.sign(dst_logistics["private_key"], tx_pharma_cvs["payload"])
    blockchain.add_transaction(tx_pharma_cvs)
    blockchain.mine_pending_transactions()

    print(f"[INIT] Seeding complete! Mined {len(blockchain.chain)} blocks.")


class BlockchainRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the Blockchain Authenticity application."""

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Serve static assets
        if path == "/" or path == "/index.html":
            self._serve_file("static/index.html", "text/html; charset=utf-8")
            return
        elif path == "/style.css":
            self._serve_file("static/style.css", "text/css; charset=utf-8")
            return
        elif path == "/app.js":
            self._serve_file("static/app.js", "application/javascript; charset=utf-8")
            return

        # REST API Endpoints
        if path == "/api/chain":
            chain_data = [b.to_dict() for b in blockchain.chain]
            is_valid, msg, faulty_idx = blockchain.validate_chain()
            self._send_json({
                "chain": chain_data,
                "length": len(blockchain.chain),
                "is_valid": is_valid,
                "validation_message": msg,
                "faulty_block_index": faulty_idx,
                "difficulty": blockchain.difficulty,
                "pending_transactions": blockchain.pending_transactions
            })
            return

        elif path == "/api/statistics":
            stats = blockchain.get_summary_stats()
            self._send_json(stats)
            return

        elif path == "/api/entities":
            # List authorized participants
            entities = []
            for pub, info in blockchain.smart_contract.authorized_entities.items():
                entities.append({
                    "entity_id": info["entity_id"],
                    "name": info["name"],
                    "role": info["role"],
                    "location": info["location"],
                    "public_key": pub
                })
            self._send_json({"entities": entities})
            return

        elif path == "/api/products":
            # List all registered products
            prods = list(blockchain.smart_contract.products.values())
            self._send_json({"products": prods})
            return

        elif path == "/api/product/verify":
            product_id = query.get("id", [""])[0].strip()
            if not product_id:
                self._send_json({"error": "Missing product ID"}, status_code=400)
                return

            verification = blockchain.verify_product(product_id)
            # Enhance with AI prediction
            prod_record = verification.get("product_details")
            hist = verification.get("history", [])
            brand = prod_record.get("brand", "Unknown") if prod_record else "Unknown"
            price = prod_record.get("specs", {}).get("msrp_usd", 100.0) if prod_record else 0.0

            ai_result = ai_engine.predict_authenticity(
                product_id=product_id,
                brand=brand,
                offered_price=price,
                retailer_name=prod_record.get("current_owner", "Unknown") if prod_record else "Unknown",
                current_location=prod_record.get("current_location", "Unknown") if prod_record else "Unknown",
                on_chain_product=prod_record,
                history=hist
            )

            verification["ai_prediction"] = ai_result
            self._send_json(verification)
            return

        # Fallback 404
        self._send_json({"error": "Endpoint not found"}, status_code=404)

    def do_POST(self):
        path = self.path
        body = self._read_json_body()

        if body is None and path != "/api/restore":
            self._send_json({"error": "Invalid or missing JSON payload"}, status_code=400)
            return

        try:
            if path == "/api/product/register":
                entity_id = body.get("entity_id", "MFR-001")
                if entity_id not in blockchain.smart_contract.entity_keys:
                    self._send_json({"error": f"Unknown entity ID '{entity_id}'"}, status_code=400)
                    return

                keys = blockchain.smart_contract.entity_keys[entity_id]
                brand = body.get("brand", "CustomBrand")
                category = body.get("category", "General")
                batch_number = body.get("batch_number", f"BATCH-{int(time.time())}")

                # Auto-generate verifiable product ID
                product_id = body.get("product_id") or generate_unique_product_id(brand, category, batch_number)

                payload = {
                    "product_name": body.get("product_name", "Authenticated Goods"),
                    "brand": brand,
                    "batch_number": batch_number,
                    "manufacture_date": body.get("manufacture_date", time.strftime("%Y-%m-%d")),
                    "specs": body.get("specs", {"standard": "ISO-9001", "msrp_usd": float(body.get("msrp_usd", 99.0))})
                }

                signature = KeyManager.sign(keys["private_key"], payload)

                tx = {
                    "type": "PRODUCT_REGISTRATION",
                    "product_id": product_id,
                    "sender_public_key": keys["public_key"],
                    "payload": payload,
                    "signature": signature
                }

                res = blockchain.add_transaction(tx)
                mine_res = blockchain.mine_pending_transactions()

                self._send_json({
                    "status": "SUCCESS",
                    "product_id": product_id,
                    "transaction": res,
                    "mining": mine_res,
                    "product": blockchain.smart_contract.get_product(product_id)
                })
                return

            elif path == "/api/product/transfer":
                product_id = body.get("product_id")
                sender_id = body.get("sender_entity_id")
                recipient_id = body.get("recipient_entity_id")
                next_status = body.get("next_status")
                location = body.get("location")

                if sender_id not in blockchain.smart_contract.entity_keys:
                    self._send_json({"error": f"Invalid sender '{sender_id}'"}, status_code=400)
                    return
                if recipient_id not in blockchain.smart_contract.entity_keys:
                    self._send_json({"error": f"Invalid recipient '{recipient_id}'"}, status_code=400)
                    return

                sender_keys = blockchain.smart_contract.entity_keys[sender_id]
                recipient_keys = blockchain.smart_contract.entity_keys[recipient_id]

                payload = {
                    "recipient_public_key": recipient_keys["public_key"],
                    "next_status": next_status,
                    "location": location
                }

                signature = KeyManager.sign(sender_keys["private_key"], payload)

                tx = {
                    "type": "CUSTODY_TRANSFER",
                    "product_id": product_id,
                    "sender_public_key": sender_keys["public_key"],
                    "payload": payload,
                    "signature": signature
                }

                res = blockchain.add_transaction(tx)
                mine_res = blockchain.mine_pending_transactions()

                self._send_json({
                    "status": "SUCCESS",
                    "product_id": product_id,
                    "transaction": res,
                    "mining": mine_res,
                    "updated_record": blockchain.smart_contract.get_product(product_id)
                })
                return

            elif path == "/api/ai/predict":
                product_id = body.get("product_id", "")
                brand = body.get("brand", "Unknown")
                offered_price = float(body.get("offered_price", 0.0))
                current_location = body.get("current_location", "Unknown Hub")

                prod = blockchain.smart_contract.get_product(product_id)
                history = blockchain.smart_contract.get_history(product_id)

                prediction = ai_engine.predict_authenticity(
                    product_id=product_id,
                    brand=brand,
                    offered_price=offered_price,
                    retailer_name=body.get("retailer_name", "Unknown Store"),
                    current_location=current_location,
                    on_chain_product=prod,
                    history=history
                )
                self._send_json(prediction)
                return

            elif path == "/api/tamper":
                block_index = int(body.get("block_index", 1))
                fake_name = body.get("fake_product_name", "COUNTERFEIT_CLONED_ITEM_INJECTED")
                tamper_res = blockchain.tamper_block_for_testing(block_index, fake_name)
                is_valid, msg, faulty_idx = blockchain.validate_chain()
                tamper_res["chain_valid"] = is_valid
                tamper_res["validation_message"] = msg
                tamper_res["faulty_block_index"] = faulty_idx
                self._send_json(tamper_res)
                return

            elif path == "/api/restore":
                restore_res = blockchain.restore_tampered_blocks()
                is_valid, msg, _ = blockchain.validate_chain()
                restore_res["chain_valid"] = is_valid
                restore_res["validation_message"] = msg
                self._send_json(restore_res)
                return

            elif path == "/api/mine":
                mine_res = blockchain.mine_pending_transactions()
                self._send_json(mine_res)
                return

            self._send_json({"error": "Unknown POST endpoint"}, status_code=404)

        except SmartContractError as sce:
            self._send_json({"error": f"Smart Contract Rule Violation: {str(sce)}"}, status_code=400)
        except Exception as e:
            self._send_json({"error": f"Internal Server Error: {str(e)}"}, status_code=500)

    def _read_json_body(self) -> Any:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            raw_data = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_data)
        except Exception:
            return None

    def _send_json(self, data: Any, status_code: int = 200):
        self._set_headers(status_code, "application/json; charset=utf-8")
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def _serve_file(self, filepath: str, content_type: str):
        if not os.path.exists(filepath):
            self._send_json({"error": f"File not found: {filepath}"}, status_code=404)
            return
        with open(filepath, "rb") as f:
            content = f.read()
        self._set_headers(200, content_type)
        self.wfile.write(content)

    def log_message(self, format, *args):
        # Clean terminal logging
        print(f"[HTTP] {self.address_string()} - {args[0]}")


def start_server(port: int = 8000):
    seed_demo_data()
    server_address = ("", port)
    httpd = HTTPServer(server_address, BlockchainRequestHandler)
    print("=" * 75)
    print(f"  E-Commerce Product Authenticity Blockchain Server Running")
    print(f"  Access Web UI at: http://localhost:{port}")
    print(f"  API Documentation & Explorer: http://localhost:{port}/api/chain")
    print("=" * 75)
    httpd.serve_forever()


if __name__ == "__main__":
    start_server(8000)
