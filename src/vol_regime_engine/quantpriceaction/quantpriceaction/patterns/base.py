import torch


class BasePattern:

    def __init__(self, name, constraints, required_keys=None):
        self.name = name
        self.constraints = constraints
        self.required_keys = required_keys or []

    def detect(self, context):

        # Validate required context keys
        for key in self.required_keys:
            if key not in context:
                raise KeyError(f"{key} missing in context")

        outputs = []

        for constraint in self.constraints:
            result = constraint(context)
            outputs.append(result)

        # ===============================
        # If first output is tensor → all must be tensors
        # ===============================
        if isinstance(outputs[0], torch.Tensor):

            combined = outputs[0]

            for out in outputs[1:]:
                if not isinstance(out, torch.Tensor):
                    raise TypeError(
                        f"Constraint mix error in {self.name}: "
                        "Cannot mix tensor and boolean outputs."
                    )

                combined = combined & out

            return combined

        # ===============================
        # If scalar booleans
        # ===============================
        else:
            return all(outputs)