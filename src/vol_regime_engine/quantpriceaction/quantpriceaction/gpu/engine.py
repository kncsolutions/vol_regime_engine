import torch
import numpy as np
import pandas as pd
from ..patterns.registry import PatternRegistry
from ..core.constraints import Constraints


class GPUEngine:

    def __init__(self, device="cuda"):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.price = None

    # ==================================================
    # DATA LOADER (robust + safe)
    # ==================================================
    def load(self, price_array):
        """
        Accepts:
        - pandas DataFrame
        - numpy array
        - list

        Produces:
        Tensor shape (symbols, time)
        """

        # DataFrame → numeric only
        if isinstance(price_array, pd.DataFrame):
            price_array = price_array.select_dtypes(include=[np.number])
            price_array = price_array.to_numpy()

        # list → numpy
        if isinstance(price_array, list):
            price_array = np.array(price_array)

        price_array = np.asarray(price_array)

        if not np.issubdtype(price_array.dtype, np.number):
            raise ValueError("Input contains non-numeric values.")

        price_array = price_array.astype(np.float32)
        price_array = np.nan_to_num(price_array)

        if price_array.ndim == 1:
            price_array = price_array.reshape(1, -1)

        # Ensure (symbols, time)
        if price_array.shape[0] > price_array.shape[1]:
            price_array = price_array.T

        self.price = torch.from_numpy(price_array).to(self.device)

    # ==================================================
    # FULL CONTEXT BUILDER
    # ==================================================
    def _build_context(self):

        if self.price is None:
            raise ValueError("Load data before evaluating patterns.")

        price = self.price

        pivot_high, pivot_low = Constraints.pivots(price)
        compression = Constraints.compression(price)
        slopes = Constraints.slope(price)
        energy = Constraints.structural_energy(price)

        return {
            "price": price,
            "pivot_high": pivot_high,
            "pivot_low": pivot_low,
            "compression": compression,
            "slopes": slopes,
            "energy": energy
        }

    # ==================================================
    # EVALUATION
    # ==================================================
    # def evaluate(self):
    #
    #     context = self._build_context()
    #     results = {}
    #
    #     current_index = int(self.price.shape[1] - 1)
    #
    #     for pattern in PatternRegistry.get_all():
    #
    #         try:
    #             output = pattern.detect(context)
    #             print(output)
    #
    #             # If tensor mask → check last bar
    #             if isinstance(output, torch.Tensor):
    #
    #                 # If 2D mask (S, T)
    #                 if output.ndim == 2:
    #                     signal = output[:, -1]
    #
    #                     if torch.any(signal):
    #                         results[pattern.name] = {
    #                             "timestamp_index": current_index,
    #                             "symbols_triggered": torch.where(signal)[0].tolist()
    #                         }
    #
    #                 # If 1D tensor (S,)
    #                 elif output.ndim == 1:
    #                     if torch.any(output):
    #                         results[pattern.name] = {
    #                             "timestamp_index": current_index,
    #                             "symbols_triggered": torch.where(output)[0].tolist()
    #                         }
    #
    #             # If boolean
    #             elif isinstance(output, bool):
    #                 if output:
    #                     results[pattern.name] = {
    #                         "timestamp_index": current_index
    #                     }
    #
    #         except Exception as e:
    #             print(f"[WARNING] Pattern {pattern.name} failed:", e)
    #             results[pattern.name] = None
    #
    #     return results

    def evaluate(self):

        context = self._build_context()
        results = {}

        current_index = self.price.shape[1] - 1
        num_symbols = self.price.shape[0]

        for pattern in PatternRegistry.get_all():

            detected = pattern.detect(context)

            # If pattern.detect returns tensor per symbol
            if isinstance(detected, torch.Tensor):

                triggered = torch.where(detected)[0].tolist()

                if triggered:

                    if num_symbols == 1:
                        # Single symbol → simplify output
                        results[pattern.name] = {
                            "timestamp_index": int(current_index)
                        }
                    else:
                        results[pattern.name] = {
                            "timestamp_index": int(current_index),
                            "symbols_triggered": triggered
                        }

            else:
                # If simple boolean
                if detected:
                    results[pattern.name] = {
                        "timestamp_index": int(current_index)
                    }

        return results

