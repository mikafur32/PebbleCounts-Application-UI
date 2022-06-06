import subprocess
import os


# print(len(next(os.walk('C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho'))[1]))


def yn(f, prompt, y_other, y_other_f):
    inp = f(prompt)
    while inp != 'y' and inp != 'n':
        inp = f(prompt)

    if inp == 'y':
        y_other_f(y_other)

    return inp


'''

subset = yn(input, 'Would you like to subset the image? y/n ', pass)

if subset == 'y':
    # Enter the file location of 01_preprocess_survey_for_PebbleCounts.py
    subprocess.call('cd ' + input('Enter the file location of 01_preprocess_survey_for_PebbleCounts: '))
    # cd C:\\Users\Mikey\Desktop\Research\Pebblecount-working\PebbleCounts\scripts'
    # Tile (subset) the image
    subprocess.call('python 01_preprocess_survey_for_PebbleCounts.py')

# Enter the file location of PebbleCounts.py
subprocess.call('cd ' + input('Enter the file location of PebbleCounts.py: ').rstrip())
# 'cd C:\\Users\Mikey\Desktop\Research\Pebblecount-working\PebbleCounts
'''

#####################################################################################################################
'''
    PEBBLECOUNTING
'''
#####################################################################################################################
file = input('Enter the folder location of the tiles: ')
start = int(input('Which tile would you like to start on? '))

# make sure to add '\' to every '\' so that the Python compiler doesn't think it's the beginning of an escape code
# Example: 'C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho'


# Naming convention for the tiles:
# 1. Name each tile 1 through x
# 1.tif, 2.tif, 3.tif... x.tif
# 2. Place each numbered tile into a folder with the same number name
# 1.tif goes into the folder 1
# C:\  ...  \1\1.tif

for i in range(start, len(next(os.walk('C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho'))[1])):
    print('Counting Pebbles on tile %d' % i)

    subprocess.call(
        'python PebbleCounts.py -im C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho\\%d\\%d.tif -ortho y'
        % (i, i)
    )
    yn(input, 'Redo %d? y/n ' % i,
       'python PebbleCounts.py -im C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho\\%d\\%d.tif -ortho y'
       % (i, i),
       subprocess.call
       )

'''
EXAMPLE:

for i in range(start, len(next(os.walk('C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho'))[1])):
    print(i)

    subprocess.call(
        'python PebbleCounts.py -im C:\\Users\\Mikey\\Desktop\\Clips\\LC1\\LC1Steeptiles_ortho\\%d\\%d.tif -ortho y' % (i, i)
    )
    
'''
