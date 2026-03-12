import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime, timezone
import pandas as pd
import numpy as np
from .sanitizer import sanitize, clean_scalar


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
            option_chain: pd.DataFrame
    ):
        timestamp = int(datetime.now(timezone.utc).timestamp())

        ts = str(timestamp)

        ref = self.root_ref.child("vol-regime-metrics").child(stock_id).child('metrics').child(ts)
        print(f"Uploading to: vol-regime-metrics/{stock_id}/{ts}")
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
            "option_chain": option_chain
        }

        payload = sanitize(payload)
        # import json
        # try:
        #     json.dumps(payload, allow_nan=False)
        # except ValueError as e:
        #     print("Payload contains invalid number:")
        #     print(payload)
        #     raise e

        ref.set(payload)
