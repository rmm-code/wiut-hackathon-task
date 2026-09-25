from .road import RoadRules
from .signals import SignalRules
from .turns import TurnRules
from .conflicts import ConflictRules


class Rules:
    def __init__(self, scene):
        self.scene = scene
        self.modules = [
            RoadRules(scene),
            SignalRules(scene),
            TurnRules(scene),
            ConflictRules(scene),
        ]

    def step(self, tracks, t, frame=None):
        if not self.scene.matched:
            return []
        return [
            flag for module in self.modules for flag in module.step(tracks, t, frame)
        ]
