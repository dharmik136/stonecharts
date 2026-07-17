# CartesianFrame Python Skeleton
class CartesianFrame:
    def __init__(self, spec, chart_noun, x_scale, include_zero):
        self.spec = spec
        self.theme = spec.theme
        self.plot_x = 0.0
        self.plot_y = 0.0
        self.plot_w = 0.0
        self.plot_h = 0.0
        self.n = 0
        self.cats = []

    def xpix(self, i: int) -> float:
        # Point scale: plot_x + plot_w * i / (n - 1)
        # Band scale: plot_x + band_width * i + band_width / 2
        return 0.0

    def ypix(self, v: float) -> float:
        return 0.0

    def band_width(self) -> float:
        return 0.0
