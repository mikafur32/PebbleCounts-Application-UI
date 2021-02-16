# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import glob
import cv2
import shutil
#%%
# VARIABLES TO SET

# PebbleCountsAuto command line tool
pc_cmd = "/home/ben/PebbleCounts/PebbleCountsAuto.py"

# path to a grid of tiles produced in the script 01_preprocess_survey_for_PebbleCounts
path = "/home/ben/toro/sites/site0km/tiles_ortho/grid1"

# tophat threshold for connecting edges, default is 0.9, but can be lowered to e.g., 0.8
# if too many edges are found
tophat_th = 0.8

# sobel threshold for connecting edges, default is 0.9, but can be lowered to e.g., 0.8
# if too many edges are found
sobel_th = 0.8

# first non-local means denoising value, default is 5, but can be lowered to 1-4
# if the user notes blurring of edges
first_nl_denoise = 5

# lower b-axis cutoff in pixels to use for pebblecounts, default is 20
cutoff = 20

# %%

# create a master list of images to use for looping over
imgs = []
master_list = path +"/master_list.txt"
if not os.path.exists(master_list):
    imgs_list = open(master_list, 'w')
    for f in glob.glob(path +"/*.tif"):
        f = f.replace("\\", "/")
        imgs_list.write(f + '\n')
    imgs_list.close()
    with open(master_list) as file:
        for line in file:
            imgs.append(line.strip())
else:
    with open(master_list) as file:
        for line in file:
            imgs.append(line.strip())

# create directories for tiles run ('done') and not run ('skipped')
skipped = path +"/PCAuto/skipped/"
if not os.path.exists(skipped):
    os.makedirs(skipped)

done = path +"/PCAuto/done/"
if not os.path.exists(done):
    os.makedirs(done)

#%%
def resizeWin(img, resize_factor=0.8):
    """
    Get the system screen resolution and resize input image by a factor. Factor
    must be in the range (0, 1].
    """
    # this import needs to be within the function or else openCV throws errors
    import tkinter as tk
    root = tk.Tk()
    resize_factor = (1 - resize_factor) + 1
    sys_w, sys_h = root.winfo_screenwidth()/resize_factor, root.winfo_screenheight()/resize_factor
    root.destroy()
    root.quit()
    del root
    scale_width = sys_w / img.shape[1]
    scale_height = sys_h / img.shape[0]
    dimensions = min(scale_width, scale_height)
    window_width = int(img.shape[1] * dimensions)
    window_height = int(img.shape[0] * dimensions)
    return window_width, window_height

def image_check(im, resize_factor=0.7):
    """
    Open a given image and proceed with script on 'y' or end on 'n'
    """
    img = cv2.imread(im)
    win_name = "image check ('y'/'n'?)"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    while cv2.getWindowProperty(win_name, 0) >= 0:
        cv2.imshow(win_name, img)
        cv2.moveWindow(win_name, 0, 0)
        cv2.resizeWindow(win_name, resizeWin(img, resize_factor)[0],
                         resizeWin(img, resize_factor)[1])
        k = cv2.waitKey(1)
        if k == ord('n') & 0xFF:
            cv2.destroyAllWindows()
            return False
#            raise ValueError("\n\nSkipping image, ending script\n")
        elif k == ord('y') & 0xFF:
            print("\nProceeding with image\n")
            cv2.destroyAllWindows()
            return True
            break
        elif cv2.getWindowProperty(win_name, 0) == -1:
            cv2.destroyAllWindows()
            return False
#            raise ValueError("\n\nSkipping image, ending script\n")

#%%

# loop through the list of images and run each one through the PebbleCountsAuto tool
for img in imgs:
    print(img)

    name = img.split("tile_")[-1].split(".tif")[0]

    if not os.path.exists(done + img.split("/")[-1].split(".tif")[0]+"_PebbleCountsAuto_CSV.csv") and not os.path.exists(skipped + img.split("/")[-1]):
        print("not clicked in current round, doing PC")

        # flash the image and skip it if need be
        flag = image_check(img, 0.9)
        if flag:
            pass
        if not flag:
            shutil.move(img, skipped)
            continue

        # HERE is the command that would normaly be entered at the command line
        cmd = "python " + pc_cmd + " -im " + img + " -ortho y -resize 0.9 -tophat_th " \
                + tophat_th + " -sobel_th " + sobel_th + " -canny_sig 2" \
                + " -first_nl_denoise " + first_nl_denoise + " -cutoff " + cutoff

        print(cmd)

        # we run the command in a subprocess shell
        subprocess.call(cmd, shell=True)

        # and move the results to the appropriate directory
        shutil.move(img, done)
        shutil.move(img.split('.')[0] + "_PebbleCountsAuto_CSV.csv", done)
        shutil.move(img.split('.')[0] + "_PebbleCountsAuto_LABELS.tif", done)
        shutil.move(img.split('.')[0] + "_PebbleCountsAuto_FIGURE.png", done)
        try:
            shutil.move(img.split('.')[0] + "_PebbleCounts_SandMask_TIFF.tif", done)
            shutil.move(img.split('.')[0] + "_PebbleCounts_SandMask_SHP.shp", done)
            shutil.move(img.split('.')[0] + "_PebbleCounts_SandMask_SHP.dbf", done)
            shutil.move(img.split('.')[0] + "_PebbleCounts_SandMask_SHP.prj", done)
            shutil.move(img.split('.')[0] + "_PebbleCounts_SandMask_SHP.shx", done)
        except:
            pass

        another = input("do another one? ")
        if another == 'y':
            continue
        elif another == 'n':
            sys.exit()
    else:
        print("already clicked or skipped, next image")
