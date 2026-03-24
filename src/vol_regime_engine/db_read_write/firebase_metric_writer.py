import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from .sanitizer import sanitize, clean_scalar, sanitize_keys


class FirebaseMetricWriter:

    def __init__(self, service_account_path: str, database_url: str):
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(
                cred,
                {
                    "databaseURL": database_url
                }
            )
        print(firebase_admin._apps)

        self.root_ref = db.reference("/")



    def upload_metrics(
            self,
            stock_id: str,
            iv: float,
            hv: float,
            spot: float,
            gamma_flip: float,
            k: float,
            I1: float,
            I2: float,
            amplification: float,
            bifurcation_proximity_ratio: float,
            gex_gradient: float,
            gamma_zones: dict,
            fragility_score: float,
            lot_size: int,
            option_chain: pd.DataFrame
    ):
        timestamp = int(datetime.now(timezone.utc).timestamp())
        ts = str(timestamp)

        # ---------- BASE REF ----------
        metrics_ref = self.root_ref.child("vol-regime-metrics").child(stock_id).child('metrics').child(ts)

        print(f"Uploading to: vol-regime-metrics/{stock_id}/{ts}")

        # ---------- COMPUTE GAMMA EXPLOSION ----------
        explosion_score = None

        try:
            if isinstance(option_chain, pd.DataFrame):
                chain_records = option_chain.to_dict(orient="records")
            else:
                chain_records = option_chain

            gex = [o["net_gex"] for o in chain_records if o.get("net_gex") is not None]

            if len(gex) >= 3:
                gradient = np.gradient(gex)
                explosion_score = float(np.max(gradient ** 2))
            else:
                explosion_score = 0.0

        except Exception as e:
            print("Explosion calc error:", stock_id, e)
            explosion_score = 0.0

        # ---------- UPDATE GAMMA ZONES ----------
        if not gamma_zones:
            gamma_zones = {}

        gamma_zones["gamma_explosion_score"] = explosion_score

        # ---------- BUILD PAYLOAD ----------
        payload = {
            "timestamp": ts,
            "stock_id": stock_id,
            "iv": iv,
            "hv": hv,
            "spot": spot,
            "gamma_flip": gamma_flip,
            "impact_coefficient_k": k,
            "linear_instability_I1": I1,
            "convexity_instability_I2": I2,
            "amplification_factor": amplification,
            "bifurcation_proximity_ratio": bifurcation_proximity_ratio,
            "gex_gradient": gex_gradient,
            "gamma_zones": gamma_zones,
            "fragility_score": fragility_score,
            "lot_size": lot_size,
            "option_chain": chain_records
        }

        payload = sanitize(payload)

        # ---------- WRITE HISTORICAL ----------
        metrics_ref.set(payload)

        # ============================================================
        # 🔥 NEW: UPDATE LATEST SNAPSHOT
        # ============================================================
        latest_ref = self.root_ref.child("latest-vol-regime-metrics").child(stock_id)
        latest_ref.set(payload)

        # ============================================================
        # 🔥 NEW: UPDATE FLIPZONE NODE
        # ============================================================
        flipzone_ref = self.root_ref.child("flipzone-latest")

        if spot and gamma_flip:
            distance = (spot - gamma_flip) / gamma_flip * 100

            if abs(distance) <= 2:
                flipzone_ref.child(stock_id).set({
                    "distance": distance,
                    "gamma_explosion_score": explosion_score,
                    "timestamp": ts
                })
            else:
                # remove if no longer in flipzone
                flipzone_ref.child(stock_id).delete()

        print(f"✅ Updated latest + flipzone for {stock_id}")

    def upload_regime_state(
            self,
            stock_id: str,
            option_chains: dict,
            spot_snapshot: dict,
            strategy_outputs: dict,
            regime_state: dict,
            lot_size: int
    ):
        timestamp = int(datetime.now(timezone.utc).timestamp())
        ts = str(timestamp)

        ref = self.root_ref.child("vol-regime-states").child(stock_id).child('states').child(ts)
        print(f"Uploading to: vol-regime-states/{stock_id}/{ts}")
        payload = {
            "timestamp": ts,
            "stock_id": stock_id,
            "lot_size": lot_size,

            # ✅ market data
            "spot_snapshot": spot_snapshot,
            "option_chains": option_chains,

            # ✅ analytics
            "regime_state": regime_state,

            # ✅ strategy
            "strategy_output": strategy_outputs,
            "analysis_response": "Manual Interpretation Required.."
        }

        payload = sanitize(payload)
        payload = sanitize_keys(payload)
        # import json
        # try:
        #     json.dumps(payload, allow_nan=False)
        # except ValueError as e:
        #     print("Payload contains invalid number:")
        #     print(payload)
        #     raise e
        ref.set(payload)

