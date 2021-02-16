# -*- coding: utf-8 -*-
import numpy as np
from scipy import interpolate as interp
from scipy import stats

# %%

# FUNCTIONS

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

# EXAMPLE USE

QuantBD

            for g in range(len(q_subset)):
                p_l, p_u = QuantBD(n=len(subset), p=q_subset[g])

                # Eaton eq(3)
                error = 0.5 * ((np.percentile(subset, p_u*100) - np.percentile(subset, p_l*100)) / np.percentile(subset, q_subset[g]*100))

                if g == 0:
                    color='k'
                if g == 1:
                    color='gray'
                if g == 2:
                    color='b'
                if g == 3:
                    color='r'

                axes[g].scatter(k, error*100, marker='.', s=1, c=color, alpha=0.5)

    for g in range(len(q_subset)):
        axes[g].text(len(a_manual)+60, 15.5, "{:.0f}th perc. (Auto)".format(q_subset[g]*100), fontsize=8)
        axes[g].set_xlim(len(a_manual), len(a_auto))
        axes[g].set_xlabel('Sample size', fontsize=9, labelpad=0.1)
        if g == 0:
            axes[g].set_ylabel('Uncertainty (percentage)', fontsize=9)
        else:
            axes[g].set_yticklabels([])
        axes[g].set_ylim(0, 20)
        axes[g].grid(lw=0.4)
        axes[g].tick_params(labelsize=8)
        axes[g].set_xticklabels(["{:,}".format(int(x)) for x in axes[g].get_xticks()], rotation=30, ha='right', position=(0,.03))
# %
    plt.savefig(out_dir + "NEW_fig_EatonEq3_uncert_vs_sample_site{}km_SSS.png".format(name), dpi=300)
    # plt.savefig(out_dir + "NEW_fig_EatonEq3_uncert_vs_sample_site{}km_SSS.pdf".format(name), dpi=300)
    plt.close()
