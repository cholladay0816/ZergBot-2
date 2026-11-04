"""Search known map sites; locations are hypotheses, never unseen enemy facts."""

from math import dist


class ExpansionSearch:
    def __init__(self):
        self.route: list[tuple[float, float]] = []
        self.index = 0
        self.next_advance_frame = 0

    def target(self, enemy_start, expansion_sites, own_bases):
        if not self.route:
            start = tuple(enemy_start)
            sites = {tuple(p) for p in expansion_sites}
            sites = {
                p
                for p in sites
                if dist(p, start) > 8 and all(dist(p, home) > 15 for home in own_bases)
            }
            self.route = [start, *sorted(sites, key=lambda p: (dist(p, start), p))]
        return self.route[self.index]

    def observe(self, army_positions, target_visible, frame):
        if not self.route:
            raise ValueError("Initialize search route before observing")
        target = self.route[self.index]
        if (
            frame >= self.next_advance_frame
            and target_visible
            and any(dist(position, target) <= 8 for position in army_positions)
        ):
            self.index = (self.index + 1) % len(self.route)
            self.next_advance_frame = frame + 112
        return self.route[self.index]
