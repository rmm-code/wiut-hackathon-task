from ..geometry import distance
from ..types import Flag, VEHICLES
from .conflicts import clipped
from .crossing import CrossingRules, is_rider, occluded
from .direction import DirectionRules


class RoadRules:
    # Ground-point clearance, in pedestrian heights: inside the kerb, and away from crossings.
    edge_margin, crossing_margin = 0.12, 0.12

    def __init__(self, scene):
        self.scene = scene
        self.crossing_rules = CrossingRules(scene)
        self.direction_rules = DirectionRules(scene)

    def step(self, tracks, t, frame=None):
        flags = []
        vehicles = [
            tr
            for tr in tracks
            if tr.observation.kind in VEHICLES
            and self.scene.on_road(tr.observation.foot)
        ]
        people = [
            tr
            for tr in tracks
            if tr.observation.kind == "person"
            and not is_rider(tr, tracks)
            and not occluded(tr, tracks)
        ]
        flags.extend(self.crossing_rules.step(tracks, people, t))
        flags.extend(self.direction_rules.step(vehicles, t, frame))
        for track in vehicles:
            observation = track.observation
            if track.stopped_since is not None and t - track.stopped_since >= 10:
                nearby = sum(
                    other is not track
                    and other.stopped_since is not None
                    and distance(other.observation.foot, observation.foot)
                    < 2.8 * observation.height
                    for other in vehicles
                )
                if (
                    not self.scene.queue_zone(observation.foot)
                    and not clipped(observation.box)
                    and nearby == 0
                ):
                    flags.append(
                        Flag(
                            "stopped_vehicle",
                            str(observation.id),
                            track.stopped_since,
                            observation.score,
                            track.lane,
                            "Stationary for at least 10 seconds with no stationary vehicle beside it, outside signal queues, turn-waiting areas and kerb parking.",
                        )
                    )
        for track in people:
            obs = track.observation
            edge = max(0.006, obs.height * self.edge_margin)
            gap = max(0.006, obs.height * self.crossing_margin)
            if self.scene.on_road(obs.foot, edge) and not self.scene.near_crossing(
                obs.foot, gap
            ):
                flags.append(
                    Flag(
                        "jaywalking",
                        str(obs.id),
                        t,
                        obs.score,
                        None,
                        "Pedestrian ground point lies on the roadway outside crossings and islands.",
                    )
                )
        for track in tracks:
            obs = track.observation
            if not self.scene.on_road(obs.foot):
                continue
            if (
                obs.kind in {"dog", "cat", "horse", "cow", "sheep", "debris"}
                and obs.score >= 0.65
            ):
                flags.append(
                    Flag(
                        "road_obstacle",
                        str(obs.id),
                        t,
                        obs.score,
                        None,
                        f"Detected {obs.kind} on the roadway; generic debris coverage depends on a specialist detector.",
                    )
                )
            if obs.kind in {"fire", "smoke"} and obs.score >= 0.65:
                flags.append(
                    Flag(
                        "fire_smoke",
                        str(obs.id),
                        t,
                        obs.score,
                        None,
                        "Specialist detector identifies fire or smoke on the roadway.",
                    )
                )
        return flags
