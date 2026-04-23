# delta analysis

Folders reviewed:

- `packing_efficiency_results/`
- `max_delta_point_results/`
- `bar_graph_statistics/`
- `binary_electronegativity_vs_delta/`
- `binary_electronegativity_multi_regression_clean/`

The emphasis here is interpretation from the figures themselves, supported by the summary tables where needed.

## 1. Packing efficiency vs delta_E

### Main binary plots

![Binary configuration-level packing vs delta_E](packing_efficiency_results/binary/plots/configuration_level_packing_vs_delta.png)

![Binary inter-compound packing comparison](packing_efficiency_results/binary/plots/chemsys_level_median_packing_vs_best_delta.png)

![Binary within-chemsys correlation histogram](packing_efficiency_results/binary/plots/within_chemsys_correlation_histogram.png)

### Main ternary plots

![Ternary configuration-level packing vs delta_E](packing_efficiency_results/ternary/plots/configuration_level_packing_vs_delta.png)

![Ternary inter-compound packing comparison](packing_efficiency_results/ternary/plots/chemsys_level_median_packing_vs_best_delta.png)

![Ternary within-chemsys correlation histogram](packing_efficiency_results/ternary/plots/within_chemsys_correlation_histogram.png)

### Interpretation

The binary configuration-level scatter shows a broad negative tendency: many points with higher packing fraction still sit below zero, and the deepest negative outliers appear in the medium-to-high packing region rather than only at low packing. So packing is related to `delta_E`, but the figure does not support a simple "denser packing always fixes the problem" interpretation.

The binary inter-compound plot makes that even clearer. `Ti-O` is the strongest outlier, with a very negative best-in-chemsys value near `-1.61`, but it is not low-packing. Other labeled systems such as `Nb-S`, `Ti-S`, `Zr-S`, `V-O`, `Y-O`, and `Cu-O` also show that strongly negative `delta_E` can survive across a wide range of median packing fractions.

The binary histogram is skewed toward negative within-chemsys correlations, which supports the visual impression that increasing packing often pushes `delta_E` downward inside a given chemical system. But the positive side is not empty. A few chemsys clearly go the other way, so packing is useful but not universal.

The ternary configuration-level plot shows the same general pattern, but more strongly. Oxygen ternaries span the deepest negative region, while sulfur ternaries are somewhat more compressed, though still clearly below zero. There is also a visible high-packing cluster around `0.9-1.0` that still contains substantial negative values.

The ternary inter-compound plot highlights several persistent outliers, especially `V-Zr-O`, `Sc-Zr-O`, `Nb-Ni-O`, `Ni-Ti-O`, `W-Y-O`, `Hf-Re-S`, `Pd-Zr-O`, `Mo-Zr-S`, and `V-Zr-S`. Many of these are not low-packing systems, which again argues that chemistry and motif matter at least as much as packing fraction.

The ternary histogram is much broader than the binary one and has a large spike near both `-1` and `+1`. That immediately suggests caution: many ternary within-chemsys correlations come from very small numbers of configurations, so some extreme correlation values are mathematically sharp but not chemically robust. Even so, the left side of the histogram remains heavily populated, so the negative packing association is still real at the broader level.

### Packing-efficiency takeaway

Across both binary and ternary plots, higher packing fraction often accompanies more negative `delta_E`, but the effect is not monotonic and not sufficient by itself. The figures support using packing as one structural descriptor, not as a standalone explanation.

## 2. Maximum delta_E point results

### Plots

![Binary maximum delta_E points](max_delta_point_results/plots/binary_max_delta_points.png)

![Ternary maximum delta_E points](max_delta_point_results/plots/ternary_max_delta_points.png)

### Interpretation

These plots answer a specific best-case question: if we keep only the numerically largest `delta_E` point for each category, how close to zero can each system get?

The binary plot is tightly clustered near zero for most metals, which means many binary systems have at least one strain point where the artifact is weak. But a few systems still stand out as persistent negatives even in their best-case point. The most obvious visual outliers are `Cu-O`, `Rh-S`, `Mo-O`, `Tc-O`, and `Zn-O`. So binary systems are often recoverable, but not always.

The ternary maximum-point plot is visibly broader and more negative overall. Many ternary points remain below about `-0.05`, and a smaller but important subset stays below `-0.3` or even `-0.5`. The strongest persistent cases include `Pd-Zr-O`, `Mo-Zr-S`, `V-Zr-S`, `Fe-Zr-S`, `Mo-Zr-O`, `Re-Zr-O`, `W-Zr-O`, `W-Zr-S`, and `Hf-V-S`.

### Maximum-point takeaway

The best-case binary picture is often near-zero, but the best-case ternary picture remains appreciably negative for many systems. That is a strong indication that ternary systems are harder to rescue than binary systems even after selecting the most favorable available point.

## 3. Bar graph statistics

### Representative bar plots

![Binary oxygen min delta_E bars](bar_graph_statistics/plots/binary_oxygen_min_delta_bar.png)

![Binary sulfur min delta_E bars](bar_graph_statistics/plots/binary_sulfur_min_delta_bar.png)

![Ternary oxygen min delta_E bars](bar_graph_statistics/plots/ternary_oxygen_min_delta_bar.png)

![Ternary sulfur min delta_E bars](bar_graph_statistics/plots/ternary_sulfur_min_delta_bar.png)

![Binary oxygen mean delta_E bars](bar_graph_statistics/plots/binary_oxygen_mean_delta_bar.png)

### Interpretation of the min-bar family

The `min delta_E` bar plots are the clearest way to see the worst-case ordering.

For binary oxygen, `Ti-O` is the dominant outlier by a wide margin at about `-1.606`. The next tier includes `V-O`, `Y-O`, `Mn-O`, `Fe-O`, and `Cu-O`, but none approach the severity of `Ti-O`.

For binary sulfur, the deepest outlier is `Nb-S` at about `-1.084`, followed by `Zr-S`, `Ti-S`, and `V-S`. The sulfur distribution is broad, but again one system clearly separates itself from the rest.

For ternary oxygen, the strongest outlier is `V-Zr-O` at about `-1.683`, and it is visually isolated from the rest of the pair set. Below that, systems such as `Sc-Zr-O`, `Nb-Ni-O`, `Mn-Ni-O`, `W-Y-O`, and `Ni-Ti-O` define the next severe tier.

For ternary sulfur, the deep tail is led by systems such as `Hf-Re-S`, `Mo-Zr-S`, `V-Zr-S`, `Fe-Zr-S`, and several other transition-metal/Zr or Hf combinations. The sulfur ternary panel is not dominated by one single point as strongly as the oxygen ternary panel, but it still shows a clear severe-outlier group.

### Interpretation of the mean/median/max bar families

The mean and median bar plots compress much of the spread seen in the `min` panels. That means many systems have strongly negative excursions without having uniformly negative behavior across all sampled points.

The binary oxygen mean plot shows this nicely: `Cu-O` still remains the most negative even in the mean because it has only one configuration, while `Ti-O`, `Y-O`, `Hf-O`, `Zn-O`, and `Sc-O` remain clearly below the rest. This tells us some systems are not only extreme in the worst case, but broadly shifted downward.

The max bar families are much closer to zero, which matches the dedicated maximum-point plots. Most groups have at least one relatively benign point, but a small number remain stubbornly negative even at their maximum retained value.

### Bar-graph takeaway

The bar graphs make the hierarchy of problematic chemistries very easy to see. They show that:

- a few systems dominate the worst-case tail
- the worst-case ranking is not the same as the mean/median ranking
- ternary outliers are both more numerous and more persistent than binary ones

## 4. Binary electronegativity vs delta_E

### Single-regression plots

![Binary oxygen min electronegativity plot](binary_electronegativity_vs_delta/plots/binary_oxygen_min_electronegativity_vs_delta.png)

![Binary sulfur max electronegativity plot](binary_electronegativity_vs_delta/plots/binary_sulfur_max_electronegativity_vs_delta.png)

### Multi-regression plot

![Binary electronegativity multi-regression grid](binary_electronegativity_multi_regression_clean/plots/binary_clean_statistic_comparison_grid.png)

### Interpretation

The single-regression plots and the multi-regression grid tell the same overall story: electronegativity has some signal, but it is not the main organizing variable for the full binary `delta_E` behavior.

The clearest oxygen trend is in `min delta_E`, where the regression is moderately positive (`r = 0.315`). In the oxygen figure, lower-electronegativity metals such as `Y`, `Sc`, and especially `Ti` sit deeper in the negative region, while higher-electronegativity metals such as `Mo` and `Rh` are less negative on the `min` axis. But the spread is still wide, so this is not a tight predictive line.

The clearest sulfur trend is in `max delta_E`, where the regression is more clearly negative (`r = -0.515`). The sulfur maximum plot shows higher-electronegativity metals like `Rh`, `Mo`, and `Pd` tending to retain more negative maximum values, while several lower-electronegativity systems lie closer to zero.

The multi-regression grid is especially useful because it shows that the stronger trends sit in the extreme statistics, not in the central ones:

- `O min`: positive trend
- `S min`: weak positive trend
- `O max`: weak negative trend
- `S max`: strongest negative trend
- `mean` and `median`: nearly flat for both ligands

That means electronegativity is affecting the edge behavior more than the center of the distribution. In other words, it may help explain how extreme the dips can get, but it does not strongly explain the overall average response.

### Electronegativity takeaway

Electronegativity is a secondary descriptor in this dataset. It shows some ligand-dependent trends, especially in the extreme statistics, but the plots do not support treating it as the main driver of `delta_E`.

## 5. Overall picture from all plot folders

Putting all figure families together, the main picture is:

- packing efficiency has a clearer global relationship with `delta_E` than electronegativity does
- severe negative outliers persist even at medium or high packing fraction
- ternary systems are generally more difficult than binary systems, especially in best-case and worst-case views
- a recurring set of chemistries, especially several Zr-containing ternaries, repeatedly appear among the strongest negative outliers
- the worst-case (`min`) statistics contain the strongest chemical differentiation, while mean/median compress much of that spread

## 6. Report-style summary

One concise way to describe the results is:

> The packing-efficiency plots show a broad negative association between packing fraction and `delta_E`, but the relationship is not sufficient to explain the full behavior because strongly negative values persist even in fairly dense systems. The bar-graph and maximum-point views show that ternary systems retain more severe and more persistent negative `delta_E` values than binary systems, with several Zr-containing ternaries standing out repeatedly. Electronegativity contributes weaker, ligand-dependent trends that are clearest in the extreme statistics rather than in the mean or median values.

## 7. Good next checks

- trace the repeated Zr-containing ternary outliers back to their structural motifs
- compare packing fraction with volume-per-atom and coordination descriptors
- test whether the strongest ternary outliers are driven by a small number of configuration families
- use robust regression for electronegativity to reduce outlier leverage in the `min` and `max` statistics
