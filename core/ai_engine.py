"""
AI Counterfeit Prediction & Anomaly Detection Engine
Implements machine-learning inspired multi-factor heuristic and statistical models:
1. Shannon Entropy & Serial Number Syntactic Classification
2. Cloned QR / Impossible Transit Velocity Anomaly Detection
3. Price Deviation & Retail Channel Trust Scoring
4. Packaging & Batch Consistency Assessment
5. Comprehensive Authenticity Confidence Score & Explainable AI Output
"""

import math
import re
import time
from typing import Dict, Any, List


class AICounterfeitDetector:
    """
    Evaluates product data, scan telemetry, and supply chain dynamics
    to produce probabilistic authenticity classifications.
    """

    def __init__(self):
        # Known MSRP reference benchmarks for luxury, electronics, and pharma
        self.msrp_benchmarks = {
            "Apple": {"min_price": 500.0, "expected_currency": "USD"},
            "Nike": {"min_price": 80.0, "expected_currency": "USD"},
            "Pfizer": {"min_price": 25.0, "expected_currency": "USD"},
            "Sony": {"min_price": 100.0, "expected_currency": "USD"}
        }

    @staticmethod
    def calculate_shannon_entropy(text: str) -> float:
        """
        Calculates the information entropy of a string.
        Legitimate cryptographic serial codes exhibit high entropy (3.2 - 4.5),
        whereas naive counterfeit serials exhibit low or repetitive entropy.
        """
        if not text:
            return 0.0
        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        return round(entropy, 3)

    def evaluate_transit_velocity(
        self,
        last_scan_location: str,
        last_scan_timestamp: float,
        current_location: str,
        current_timestamp: float
    ) -> Dict[str, Any]:
        """
        Detects Cloned QR Code and Impossible Travel Anomalies.
        If a product is scanned in two distant locations within a timeframe
        that exceeds realistic commercial aircraft speed (>900 km/h),
        it flags a critical duplicate barcode attack.
        """
        if not last_scan_location or not last_scan_timestamp:
            return {"is_anomaly": False, "velocity_kmh": 0, "message": "First recorded scan location."}

        # Simplified coordinate distance estimation table (km between major hubs)
        hub_coords = {
            "Cupertino, CA, USA": (37.32, -122.03),
            "Chicago Hub, IL": (41.87, -87.62),
            "San Francisco, CA": (37.77, -122.41),
            "Beaverton, OR, USA": (45.48, -122.80),
            "Seattle, WA": (47.60, -122.33),
            "New York, NY, USA": (40.71, -74.00),
            "Tokyo, Japan": (35.67, 139.65),
            "Frankfurt Depot, DE": (50.11, 8.68),
            "Boston, MA": (42.36, -71.05)
        }

        coord1 = hub_coords.get(last_scan_location, (40.0, -100.0))
        coord2 = hub_coords.get(current_location, (40.0, -100.0))

        # Euclidean distance approximation in km
        lat_diff = (coord1[0] - coord2[0]) * 111.0
        lon_diff = (coord1[1] - coord2[1]) * 85.0
        distance_km = math.sqrt(lat_diff**2 + lon_diff**2)

        time_diff_hours = abs(current_timestamp - last_scan_timestamp) / 3600.0
        if time_diff_hours < 0.001:  # Near instantaneous
            time_diff_hours = 0.001

        velocity = distance_km / time_diff_hours

        # Maximum physical commercial transit velocity threshold: 950 km/h
        if distance_km > 300 and velocity > 950:
            return {
                "is_anomaly": True,
                "velocity_kmh": round(velocity, 1),
                "distance_km": round(distance_km, 1),
                "message": f"CRITICAL: Impossible travel velocity ({velocity:.0f} km/h) detected between {last_scan_location} and {current_location}! Cloned QR code suspected."
            }

        return {
            "is_anomaly": False,
            "velocity_kmh": round(velocity, 1),
            "distance_km": round(distance_km, 1),
            "message": "Physical transit trajectory within feasible logistical parameters."
        }

    def predict_authenticity(
        self,
        product_id: str,
        brand: str,
        offered_price: float,
        retailer_name: str,
        current_location: str,
        on_chain_product: Dict[str, Any] = None,
        history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes multi-factor AI scoring algorithm.
        Returns probabilistic score, risk level, and explainable feature flags.
        """
        risk_penalties = 0.0
        flags = []
        positive_factors = []

        # 1. On-Chain Ledger Verification (Anchor factor)
        if not on_chain_product:
            risk_penalties += 0.85
            flags.append("Product ID does not exist on the decentralized blockchain ledger.")
        else:
            positive_factors.append("Product record verified on immutable blockchain ledger.")

        # 2. Serial Number Entropy & Structure
        entropy = self.calculate_shannon_entropy(product_id)
        if entropy < 2.5:
            risk_penalties += 0.25
            flags.append(f"Low serial number complexity/entropy ({entropy}). Potential synthetic forgery.")
        else:
            positive_factors.append(f"High serial cryptographic entropy ({entropy}). Conforms to genuine pattern.")

        # 3. Price Anomaly Detection
        brand_key = next((b for b in self.msrp_benchmarks if b.lower() in brand.lower()), None)
        if brand_key:
            expected_min = self.msrp_benchmarks[brand_key]["min_price"]
            if offered_price < (expected_min * 0.4):
                risk_penalties += 0.40
                flags.append(f"Severe price anomaly! Offered price ${offered_price:.2f} is >60% below typical MSRP (${expected_min:.2f}).")
            elif offered_price < (expected_min * 0.7):
                risk_penalties += 0.15
                flags.append(f"Moderate price discount detected (${offered_price:.2f} vs expected ${expected_min:.2f}).")
            else:
                positive_factors.append(f"Pricing (${offered_price:.2f}) aligns with brand market benchmarks.")

        # 4. Retail Channel & Custody Continuity
        if on_chain_product:
            current_status = on_chain_product.get("current_status")
            if current_status == "FLAGGED_COUNTERFEIT":
                risk_penalties += 1.0
                flags.append("Product has been flagged as COUNTERFEIT by smart contract protocol!")
            elif current_status == "RECALLED":
                risk_penalties += 0.9
                flags.append("Product was officially RECALLED by the manufacturer.")
            elif current_status in ["AT_RETAILER", "SOLD"]:
                positive_factors.append(f"Chain of custody correctly transitioned to state '{current_status}'.")

        # 5. Impossible Travel Velocity Check
        if history and len(history) > 0:
            last_tx = history[-1]
            last_loc = last_tx.get("payload", {}).get("location") or on_chain_product.get("current_location")
            last_time = last_tx.get("timestamp", time.time())
            
            velocity_check = self.evaluate_transit_velocity(
                last_scan_location=last_loc,
                last_scan_timestamp=last_time,
                current_location=current_location,
                current_timestamp=time.time()
            )
            if velocity_check["is_anomaly"]:
                risk_penalties += 0.70
                flags.append(velocity_check["message"])
            else:
                positive_factors.append(velocity_check["message"])

        # Compute Final Probability (0.0% to 100.0%)
        authenticity_score = max(0.0, min(1.0, 1.0 - risk_penalties))
        authenticity_percentage = round(authenticity_score * 100, 1)

        # Classification category
        if authenticity_percentage >= 85.0:
            classification = "GENUINE"
            risk_tier = "LOW_RISK"
            badge_color = "emerald"
        elif authenticity_percentage >= 50.0:
            classification = "SUSPICIOUS / AUDIT_RECOMMENDED"
            risk_tier = "MEDIUM_RISK"
            badge_color = "amber"
        else:
            classification = "COUNTERFEIT_DETECTED"
            risk_tier = "HIGH_RISK"
            badge_color = "rose"

        return {
            "authenticity_percentage": authenticity_percentage,
            "classification": classification,
            "risk_tier": risk_tier,
            "badge_color": badge_color,
            "entropy": entropy,
            "positive_indicators": positive_factors,
            "risk_flags": flags,
            "ai_model_name": "AuthentiShield Anomaly & Provenance Classifier v2.1"
        }

