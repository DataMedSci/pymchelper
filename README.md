# pymchelper

Toolkit for working with particle transport codes such as [FLUKA](http://fluka.cern/) and [SHIELD-HIT12A](https://shieldhit.org/). It reads binary outputs and helps you convert, analyze, and visualize results on any platform (Linux, Windows, macOS).

## Key Features

- Convert binary outputs to plots and common formats (CSV, XLSX, HDF5, and more) using `convertmc`.
- Speed up simulations by splitting and merging runs with `runmc`.
- Use as a Python library to load results into convenient objects for further analysis.

<p float="left">
  <img src="/docs/default_1d.png" width="30%" />
  <img src="/docs/default_2d.png" width="30%" />
  <!-- Images shown here illustrate typical outputs produced by convertmc -->
</p>

## Quick Examples

Convert multiple SHIELD-HIT12A/FLUKA outputs into images:

```
convertmc image --many "*.bdo"
```

Run a simulation in parallel and export text output:

```
runmc --jobs 16 --out-type txt directory_with_input_files
```

## Installation

Minimal install via pip:

```
pip install pymchelper[full]
```

For detailed installation instructions (Linux packages, optional extras, and platform-specific notes), see the documentation links below.

## Documentation

- Project site: https://datamedsci.github.io/pymchelper/index.html
- Getting Started: https://datamedsci.github.io/pymchelper/getting_started.html
- User’s Guide: https://datamedsci.github.io/pymchelper/user_guide.html