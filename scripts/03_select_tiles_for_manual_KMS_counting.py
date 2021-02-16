# -*- coding: utf-8 -*-
import os, glob, shutil, random
import numpy as np
import pandas as pd
#%%

# VARIABLES TO SET

# path to the survey data, there should be a tile_ortho directory in this
# folder and some tiles should have already been processed with the PebbleCountsAuto.py tool
path = "/home/ben/toro/sites/site0km/"

# percent fraction of total tiles to validate with (e.g., 0.25 means 25%)
count_frac = 0.15


# %%

# read in all the PebbleCountsAuto data
csvs = glob.glob(path + "tiles_ortho/grid*/PCAuto/done/*.csv")

# create an output path for the subset of tiles to run manual counting on
kms_path = path + "KMS_validation/"
if not os.path.exists(kms_path):
    os.mkdir(kms_path)

#%%

# loop over the tiles and create a dataframe containing the tile identifier and
# the 95th/50th percentile ratio for that tile
df = pd.DataFrame()
for f in csvs:
    df = pd.read_csv(f)
    df["b (mm)"] = df["b (m)"].values*1000
    if len(df) == 0:
        continue
    percentiles = np.percentile(df["b (mm)"], [5, 16, 25, 50, 75, 84, 95])
    name = f.split("tile_")[1].split("_PebbleCounts")[0]

    df = df.append(pd.DataFrame({"tile" : name, "95_50" : percentiles[6]/percentiles[3]}), ignore_index=True)

#%%

# bin the 95/50th percentile ratio (here called "skew")
skew = df["95_50"].values

# we use log-spaced bins given the log-normal grain size distribution, but this could be
# changed to linear
bins = np.logspace(np.log10(skew.min()-0.0001), np.log10(skew.max()+0.0001), 6)
labels = [1, 2, 3, 4, 5] 
df["binned"] = pd.cut(df['skew'], bins=bins, labels=labels)

# get the counts in each bin
count = np.histogram(skew, bins=bins)[0]

# using the histogram counts, select a fractional count in each bin
frac_count = count * count_frac

# get a number of tiles to select in each bin
tiles_per_bin = np.ceil(frac_count)

#%%

# loop through the 5 bins and create a sub-directory then randomly sample the
# available bins in each skewness bin and pull out the number of tiles
for i in labels:

    ntiles = int(tiles_per_bin[i-1])

    kms_path_label = kms_path + "skew_bin" + str(i) + "/"
    if not os.path.exists(kms_path_label):
        os.mkdir(kms_path_label)

    df_bin = df[df["binned"] == i]
    tiles = list(df_bin.tile.values)

    tiles_counter = len(glob.glob(kms_path_label + '/*.tif'))
    while tiles_counter < ntiles:
        tile2move = random.sample(tiles, 1)[0]
        file2move = glob.glob(path + "/tiles_ortho/grid*/PCAuto/done/*_" + tile2move + ".tif")[0]
        shutil.copy(file2move, kms_path_label)
        try:
            file2move = glob.glob(path + "/tiles_ortho/grid*/PCAuto/done/*_" + tile2move + "*SandMask*.tif")[0]
            shutil.copy(file2move, kms_path_label)
        except:
            print("no sand mask for {}".format(tile2move))
        tiles.remove(tile2move)
        tiles_counter += 1
