# StoneCharts Python

The StoneCharts Python package renders the governed StoneCharts JSON-compatible
chart specification to deterministic SVG and self-contained interactive HTML. It
also installs the `stoneverify` command for local conformance evidence generation.

This package is proprietary and is not authorized for public package-index upload.
See the repository-level `README.md`, `LICENSE`, and controlled release evidence for
the supported chart catalog, guarantees, installation profiles, and distribution
boundary.

## Local development installation

```bash
python -m pip install -e ".[dev]"
```

Python 3.9 or later is required. The renderer has no runtime dependencies.

For an authorized evaluation, install the exact wheel supplied in the qualified
evaluation kit with `python -m pip install --no-index <wheel-path>`. No public PyPI
release is authorized, and `pip install stonecharts` is not a supported distribution
path.
