# Electronegativity Findings Seed

This file is a starting point for the markdown discussion of the cleaner regression plots.

## Main observations

- `S` with `max` shows a `negative` correlation of `-0.515` and slope `-0.0990`.
- `O` with `min` shows a `positive` correlation of `0.315` and slope `0.3384`.
- `O` with `max` shows a `negative` correlation of `-0.258` and slope `-0.0878`.
- `S` with `min` shows a `positive` correlation of `0.206` and slope `0.1813`.

## Suggested discussion points

- The strongest trends appear in the extreme statistics (`min` or `max`) rather than in `mean` or `median`.
- Oxygen and sulfur do not show the same regression behavior for every statistic.
- Mean and median trends are comparatively weak, so the extreme points may be driving most of the visible behavior.
- Any interpretation should mention the role of outliers, especially for the `min` delta_E values.

## Files to reference

- `plots/binary_o_clean_multiple_regression.png`
- `plots/binary_s_clean_multiple_regression.png`
- `plots/binary_clean_statistic_comparison_grid.png`
- `tables/clean_regression_summary.csv`
