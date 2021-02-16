# PebbleCounts-Application

This is a collection of _Python_ scripts implementing some of the methods outlined in an upcoming manuscript. In this manuscript we up-scale the use of the [PebbleCounts](https://github.com/UP-RS-ESP/PebbleCounts) algorithm to large photo-surveyed channel cross sections in high mountain rivers to count grain-size distributions. The percentile uncertainty estimation via binomial theory is taken from recent work by Brett Eaton, published [here](https://esurf.copernicus.org/articles/7/789/2019/esurf-7-789-2019.html) and available as _R_ code [here](https://github.com/bceaton/GSDtools). In this repository, the main _R_ function _QuantBD_ has simply been translated without modification into _Python_.

## Citation

If you use this repository in publications you should cite these sources:

_Purinton, B. and Bookhagen, B.: Introducing PebbleCounts: a grain-sizing tool for photo surveys of dynamic gravel-bed rivers, Earth Surf. Dynam., 7, 859–877, [https://doi.org/10.5194/esurf-7-859-2019](https://doi.org/10.5194/esurf-7-859-2019), 2019._

_Eaton, B. C., Moore, R. D., and MacKenzie, L. G.: Percentile-based grain size distribution analysis tools (GSDtools) – estimating confidence limits and hypothesis tests for comparing two samples, Earth Surf. Dynam., 7, 789–806, [https://doi.org/10.5194/esurf-7-789-2019](https://doi.org/10.5194/esurf-7-789-2019), 2019._

_Purinton, B. and Bookhagen, B.: Tracking downstream variability in large grain-size distributions in the south-central Andes, submitted._


## License

GNU General Public License, Version 3, 29 June 2007

Copyright © 2021 Benjamin Purinton, University of Potsdam, Potsdam, Germany

PebbleCounts-Application is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. PebbleCounts-Application is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.


## Scripts

You will need all of the _Python_ packages from PebbleCounts to run these scripts, so it's recommended that you first install these as described in [that manual](https://github.com/UP-RS-ESP/PebbleCounts/blob/master/docs/PebbleCounts_Manual.pdf). The scripts here are presented as is without guidelines for exact implementation since use cases may vary significantly. They are well commented and users are welcome to simply steal functions or for-loops that look useful to them. The following scripts can be found in the folder `scripts`:

* `01_preprocess_survey_for_PebbleCounts`: This script is used to take a full photo survey orthomosaic GeoTiff and first buffer it to remove areas of low overlap and then tile the area into four grids in a checkerboard-like pattern, with the tile size in pixels set by the user.

* `02_loop_through_tiles_for_automatic_AIF_counting.py`: This script allows the user to loop over the tiles contained in one of the grid directories output by the first script and run the `PebbleCountsAuto.py` automatic AIF counting tool on each tile. This is just a fancy wrapper for this command line function so you don't need to enter every tile name manually.

* `03_select_tiles_for_manual_KMS_counting.py`: This script takes the completed grid of automatically counted tiles and sub-selects representative tiles for running the manual KMS validation. Once output into new directories by this script, it is up to the user to run the `PebbleCounts.py` tool for manual counting via the command line. We don't include a looper function for this, but the previous script for looping the automatic AIF counting could be modified for this purpose.


## Percentile uncertainty functions

This is a collection of functions taken from the original _R_ code of [Eaton et al. (2019)](https://doi.org/10.5194/esurf-7-789-2019) and translated into _Python_. Below the function definitions is an example usage to calculate percentile uncertainties.


**FUNCTIONS:**

```
import numpy as np
from scipy import interpolate as interp
from scipy import stats

def p_c_fripp(n=100, p=0.84):
    """"calculates confidence interval under normal
    approximation of Fripp and Diplas (1993)
    (see Eaton 2019 Appendix A - https://doi.org/10.5194/esurf-7-789-2019)"""
    s = np.sqrt((n * p * (1 - p)) / n) * 10
    z = 1.96 # at alpha=0.05, 95% CI
    p_u = (p*100) + (s * z)
    p_l = (p*100) - (s * z)
    return p_l/100, p_u/100

def pbinom_diff(a, b, n, p):
    """cf. Eaton 2019 Eq (2) - https://doi.org/10.5194/esurf-7-789-2019"""
    return stats.binom.cdf(b-1, n, p) - stats.binom.cdf(a-1, n, p)

def QuantBD(n=200, p=0.84, alpha=0.05):
    """after Eaton 2019 - https://doi.org/10.5194/esurf-7-789-2019
    and:
    https://stats.stackexchange.com/questions/99829/how-to-obtain-a-confidence-interval-for-a-percentile/284970#284970
    The default parameters will recreate the example in Section 2.1.2 of Eaton 2019"""

    # get the upper and lower confidence bound range
    u = stats.binom.ppf(1 - alpha/2, n, p) + np.array([-2, -1, 0, 1, 2]) + 1
    l = stats.binom.ppf(alpha/2, n, p) + np.array([-2, -1, 0, 1, 2])
    u[u > n] = np.inf
    l[l < 0] = -np.inf

    # get the binomial difference (cf. Eaton eq(2))
    p_c = np.zeros((len(u),len(l)))
    for i in range(len(u)):
        for j in range(len(l)):
            p_c[i,j] = pbinom_diff(l[i], u[j], n, p)

    # handle the edges
    if np.max(p_c) < (1 - alpha):
        i = np.where(p_c == np.max(p_c))
    else:
        i = np.where(p_c == np.min(p_c[p_c >= 1 - alpha]))

    # assymetric bounds (cf. Eaton 2019 - Section 2.1.2)
    # this is the "true" interval with uneven tails
    l = l[i[0]]
    u = u[i[0]]

    # symmetric bounds via interpolation (cf. Eaton 2019 - Section 2.1.3)
    k = np.arange(1, n+1, 1)
    pcum = stats.binom.cdf(k, n, p)
    interp_func = interp.interp1d(pcum, k)
    lu_approx = interp_func([alpha/2, 1 - alpha/2])

    # take the number of measurements and translate
    # to lower and upper percentiles
    p_l, p_u = lu_approx[0]/n, lu_approx[1]/n

    return p_l, p_u
```

**EXAMPLE:**

```
# your grain size distribution, here drawn randomly from a log-normal distribution
# with mu=1 and sigma=0.8
gsd = np.random.lognormal(mean=1, sigma=0.8, size=1000)

# number of measurement in the grain-size distribution
n = len(gsd)

# percentile of interest (given as a fractional percentile)
p = 0.95

# confidence level (0.05 is 95% confidence)
alpha = 0.05

# calculate the upper and lower confidence bounds based on binomial theory
p_l, p_u = QuantBD(n, p, alpha)

# get the grain size of interest at the 95% confidence about the size
grain_size = np.percentile(gsd, p*100)
grain_size_l = np.percentile(gsd, p_l*100)
grain_size_u = np.percentile(gsd, p_u*100)

# calculate the percentage error after Eaton eq(3)
error = 0.5 * ((grain_size_u - grain_size_l) / grain_size)
```
