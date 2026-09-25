from ..geometry import cosine
from ..types import Flag


class DirectionRules:
    def __init__(self, scene):
        self.scene = scene
        self.wrong = {}

    def step(self, vehicles, t):
        flags, groups = [], {}
        for track in vehicles:
            obs = track.observation
            lane = self.scene.lane(obs.foot)
            track.lane = lane["id"] if lane else None
            if lane:
                groups.setdefault(lane["id"], []).append(track)
            point = self.scene.point(obs.foot)
            previous = self.scene.point(
                (obs.foot[0] - track.velocity[0], obs.foot[1] - track.velocity[1])
            )
            motion = (point[0] - previous[0], point[1] - previous[1])
            opposed = (
                lane
                and lane.get("verified")
                and t - track.first >= 1
                and track.speed > obs.height * 0.15
                and cosine(motion, lane["vector"]) < -0.75
            )
            state = self.wrong.get(obs.id)
            if opposed and state is None:
                self.wrong[obs.id] = state = {
                    "start": t,
                    "last": t,
                    "lane": lane,
                    "score": obs.score,
                }
            if state:
                same_lane = lane and lane["id"] == state["lane"]["id"]
                if same_lane:
                    state["last"] = t
                flags.append(
                    Flag(
                        "wrong_way",
                        str(obs.id),
                        state["start"],
                        state["score"],
                        state["lane"]["id"],
                        "Sustained opposing motion in a direction verified from the supplied camera; interval continues while stopped in that lane.",
                        end=None if same_lane else t,
                    )
                )
                if not same_lane:
                    self.wrong.pop(obs.id)
        for identity, state in list(self.wrong.items()):
            if t - state["last"] > 1:
                flags.append(
                    Flag(
                        "wrong_way",
                        str(identity),
                        state["start"],
                        state["score"],
                        state["lane"]["id"],
                        end=state["last"],
                    )
                )
                self.wrong.pop(identity)
        for group in self.scene.config.get("directions", []):
            if not group.get("verified") or not group.get("all_lanes_visible"):
                continue
            queues = [groups.get(identity, []) for identity in group["lanes"]]
            if queues and all(
                len(queue) >= 2
                and all(tr.speed / tr.observation.height < 0.09 for tr in queue)
                for queue in queues
            ):
                flags.append(
                    Flag(
                        "congestion",
                        group["id"],
                        t,
                        0.65,
                        group["id"],
                        "Slow tracked traffic occupies every separately mapped lane of this observed direction.",
                    )
                )
        return flags
