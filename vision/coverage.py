from .types import CLASSES


def coverage(scene, detector_names, specialist_labels=()):
    cfg = scene.config
    reasons = {
        "accident": "Requires a validated contact classifier; experimental heuristics are disabled.",
        "near_miss": "Requires validated evasive-action detection; experimental heuristics are disabled.",
        "red_light": "Governing signal and stop-line mapping are not verified.",
        "wrong_way": "Legal lane directions are not verified.",
        "illegal_u_turn": "No verified no-U-turn zone is configured.",
        "illegal_turn": "No verified prohibited lane-to-exit movement is configured.",
        "solid_line_crossing": "No verified solid marking is configured.",
        "stop_line": "Governing signal and stop-line mapping are not verified.",
        "congestion": "Direction-level lane coverage is not verified.",
        "fire_smoke": "The installed road-user detector has no fire/smoke classes.",
    }
    enabled = {"stopped_vehicle", "jaywalking", "failure_to_yield", "road_obstacle"}
    enabled.update(specialist_labels)
    if any(lane.get("verified") for lane in cfg["lanes"]):
        enabled.add("wrong_way")
    if any(
        group.get("verified") and group.get("all_lanes_visible")
        for group in cfg.get("directions", [])
    ):
        enabled.add("congestion")
    if any(signal.get("verified") for signal in cfg.get("signals", [])):
        enabled.update(["red_light", "stop_line"])
    for key, label in [
        ("turn_rules", "illegal_turn"),
        ("prohibited_u_turns", "illegal_u_turn"),
        ("solid_lines", "solid_line_crossing"),
    ]:
        if any(item.get("verified") for item in cfg.get(key, [])):
            enabled.add(label)
    if cfg.get("near_miss", {}).get("enabled"):
        enabled.add("near_miss")
    if {"fire", "smoke"} & set(detector_names):
        enabled.add("fire_smoke")
    return [
        {
            "label": label,
            "enabled": label in enabled and scene.matched,
            "status": "provisional"
            if label in enabled and scene.matched
            else "disabled",
            "reason": (
                "Input does not match the configured camera."
                if not scene.matched
                else "Rule implemented; accuracy not yet validated. Obstacle coverage is limited to detected animals/debris classes."
                if label == "road_obstacle" and label in enabled
                else "Rule implemented; scene geometry and event accuracy remain provisional."
                if label in enabled
                else reasons.get(label, "Not enabled.")
            ),
        }
        for label in CLASSES
    ]
