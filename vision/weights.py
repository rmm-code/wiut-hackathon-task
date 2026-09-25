import importlib
import os
from pathlib import Path


def load_model(path):
    import torch
    from ultralytics import YOLO

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Local model weights are missing: {path.name}")
    classes = []
    for name in torch.serialization.get_unsafe_globals_in_checkpoint(path):
        module, attribute = name.rsplit(".", 1)
        if not module.startswith(
            ("torch.nn.modules.", "ultralytics.nn.modules.", "ultralytics.nn.tasks")
        ):
            raise ValueError(f"Unapproved checkpoint global: {name}")
        value = getattr(importlib.import_module(module), attribute)
        if not isinstance(value, type) or not issubclass(value, torch.nn.Module):
            raise ValueError(f"Checkpoint global is not a model layer: {name}")
        classes.append(value)
    previous = os.environ.get("TORCH_FORCE_WEIGHTS_ONLY_LOAD")
    os.environ["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = "1"
    try:
        with torch.serialization.safe_globals(classes):
            return YOLO(str(path))
    finally:
        if previous is None:
            os.environ.pop("TORCH_FORCE_WEIGHTS_ONLY_LOAD", None)
        else:
            os.environ["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = previous
