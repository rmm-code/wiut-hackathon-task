from ..geometry import cosine, distance
from ..types import Flag, VEHICLES
from .crossing import CrossingRules, is_rider


class RoadRules:
    def __init__(self, scene):
        self.scene = scene
        self.crossing_rules = CrossingRules(scene)

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
            if tr.observation.kind == "person" and not is_rider(tr, tracks)
        ]
        flags.extend(self.crossing_rules.step(tracks, people, t))
        lane_tracks = {}
        for track in vehicles:
            observation = track.observation
            lane = self.scene.lane(observation.foot)
            track.lane = lane["id"] if lane else None
            if lane:
                lane_tracks.setdefault(lane["id"], []).append(track)
            stable = t - track.first >= 1.0
            if (
                lane
                and lane.get("verified")
                and stable
                and track.speed > observation.height * 0.15
            ):
                if cosine(track.velocity, lane["vector"]) < -0.75:
                    flags.append(
                        Flag(
                            "wrong_way",
                            str(observation.id),
                            t,
                            observation.score,
                            track.lane,
                            "Sustained movement against a verified lane direction.",
                        )
                    )
            if track.stopped_since is not None and t - track.stopped_since >= 10:
                nearby = sum(
                    other is not track
                    and other.stopped_since is not None
                    and distance(other.observation.foot, observation.foot)
                    < 2.8 * observation.height
                    for other in vehicles
                )
                if not self.scene.queue_zone(observation.foot) and nearby < 2:
                    flags.append(
                        Flag(
                            "stopped_vehicle",
                            str(observation.id),
                            track.stopped_since,
                            observation.score,
                            track.lane,
                            "Stationary for at least 10 seconds outside the mapped signal queue.",
                        )
                    )
        for track in people:
            obs = track.observation
            margin = max(0.006, obs.height * 0.12)
            if self.scene.on_road(obs.foot, margin) and not self.scene.near_crossing(
                obs.foot, margin
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
        directions = {
            lane["direction"]
            for lane in self.scene.config["lanes"]
            if lane.get("verified")
        }
        for direction in directions:
            lanes = [
                lane
                for lane in self.scene.config["lanes"]
                if lane.get("verified") and lane["direction"] == direction
            ]
            queues = [lane_tracks.get(lane["id"], []) for lane in lanes]
            if queues and all(
                len(queue) >= 3
                and all(tr.speed / tr.observation.height < 0.09 for tr in queue)
                for queue in queues
            ):
                flags.append(
                    Flag(
                        "congestion",
                        direction,
                        t,
                        0.65,
                        direction,
                        "Crawling or stationary traffic across every configured lane in this direction.",
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
