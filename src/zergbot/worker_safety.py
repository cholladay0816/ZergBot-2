"""Bounded experimental worker protection; used only by the scenario harness."""


def worker_action(health_fraction, threat_distance, selected, elapsed, max_frames=224):
    if threat_distance > 5 or elapsed >= max_frames:
        return "mine"
    if health_fraction < 0.45 and threat_distance < 3:
        return "evacuate"
    if selected and health_fraction >= 0.45 and threat_distance < 4:
        return "defend"
    return "mine"
