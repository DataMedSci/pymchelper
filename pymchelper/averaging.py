from dataclasses import dataclass

# resource https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
# also https://justinwillmert.com/posts/2022/notes-on-calculating-online-statistics/
# TODO add tests

# weight_fraction = weight_factor / total_weight
# omega_n = w_n / W_n


@dataclass
class WeightedStats:
    mean: float = 0
    total_weight: float = 0

    def update(self, value: float, weight: float = 1.0):
        if weight < 0:
            raise ValueError("Weight must be non-negative")
        # W_n = W_{n-1} + w_n
        self.total_weight += weight

        # mu_n = (1 - w_n / W_n) * mu_{n-1} + (w_n / W_n) * x_n
        first_part = (1 - weight / self.total_weight) * self.mean
        second_part = (weight / self.total_weight) * value
        self.mean = first_part + second_part
