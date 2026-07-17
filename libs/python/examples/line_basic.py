"""Generate the basic line chart demo -> interactive HTML.

Run from libs/python/:  python examples/line_basic.py
Writes line_basic.out.html next to this script and prints the path.
"""
import sys
from pathlib import Path

# Allow running without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from peakcharts import Axis, ChartSpec, Series, save_html  # noqa: E402

spec = ChartSpec(
    title="Monthly Average Temperature",
    subtitle="Source: sample data",
    x_axis=Axis(
        title="Month",
        categories=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    ),
    y_axis=Axis(title="Temperature (°C)"),
    series=[
        Series(name="Tokyo", data=[7.0, 6.9, 9.5, 14.5, 18.2, 21.5,
                                   25.2, 26.5, 23.3, 18.3, 13.9, 9.6]),
        Series(name="London", data=[3.9, 4.2, 5.7, 8.5, 11.9, 15.2,
                                     17.0, 16.6, 14.2, 10.3, 6.6, 4.8]),
    ],
)

if __name__ == "__main__":
    out = save_html(spec, Path(__file__).with_name("line_basic.out.html"))
    print("wrote", out)
