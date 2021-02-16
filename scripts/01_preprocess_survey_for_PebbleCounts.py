# -*- coding: utf-8 -*-
import os, glob, shutil
import numpy as np
from osgeo import gdal, gdalnumeric, ogr, osr
from shapely.geometry import Polygon
import fiona
gdal.UseExceptions()
#%%
# VARIABLES TO SET

# file path to the folder containing the survey
in_path = "/home/ben/toro/sites/site0km/"

# name of GeoTiff file including extension
fname = "site0km_ortho_wgs84_utm19s.tif"

# x and y size of the tile in pixels
tile_size_x = 2000
tile_size_y = 2000

# distance to buffer the survey edges and holes to reduce areas of lower
# image overlap. negative values indicate negative buffering, so -1 is
# a 1-m negative buffer
buff_dist = -1

# %%
# Here a number of naming variables are setup for running the script below
tile_dir = in_path + 'tiles_ortho/'
path = in_path + "tiles_ortho/site*.tif"
output_filename = fname.split('.')[0] + '_tile_'
outline_tif = in_path + fname.split('.')[0] + '_outline.tif'
outline_shp = in_path + fname.split('.')[0] + '_outline.shp'
buffer = outline_shp.split("_outline")[0]+"_outline_buff.shp"
clipped_site = in_path + fname.split('.')[0] + '_buffered.tif'

#%%
def fixed_buffer(infile,outfile,buffdist):
    """Function to buffer an input polygon"""
    try:
        ds_in=ogr.Open( infile )
        lyr_in=ds_in.GetLayer( 0 )
        drv=ds_in.GetDriver()
        if os.path.exists( outfile ):
            drv.DeleteDataSource(outfile)
        ds_out = drv.CreateDataSource( outfile )
        layer = ds_out.CreateLayer( lyr_in.GetLayerDefn().GetName(), \
            lyr_in.GetSpatialRef(), ogr.wkbPolygon)
        for i in range ( lyr_in.GetLayerDefn().GetFieldCount() ):
            field_in = lyr_in.GetLayerDefn().GetFieldDefn( i )
            fielddef = ogr.FieldDefn( field_in.GetName(), field_in.GetType() )
            layer.CreateField ( fielddef )
        for feat in lyr_in:
            geom = feat.GetGeometryRef()
            feature = feat.Clone()
            feature.SetGeometry(geom.Buffer(float(buffdist)))
            layer.CreateFeature(feature)
            del geom
        ds_out.Destroy()
    except:
        return False
    return True

#%%

print("getting rasterized outline")
if not os.path.exists(buffer):
    # This is the equivalent of:
    # gdal_translate -b 4 -ot Byte -co "NBITS=1" -a_nodata 0 site09_ortho_wgs84_utm19s.tif site09_outline.tif
    cmd = gdal.Translate(outline_tif, in_path + fname, bandList=[4], outputType=gdal.GDT_Byte,
                   creationOptions=["NBITS=1"], noData=0)
    cmd = None
print("getting polygonized outline")
if not os.path.exists(buffer):
    # This is the equivalent of:
    # gdal_polygonize site09_outline.tif site09_outline.shp -f "ESRI Shapefile"
    sourceRaster = gdal.Open(outline_tif)
    band = sourceRaster.GetRasterBand(1)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    outDatasource = driver.CreateDataSource(outline_shp)
    srs = osr.SpatialReference()
    srs.ImportFromWkt( sourceRaster.GetProjectionRef() )
    outLayer = outDatasource.CreateLayer(outline_shp, srs)
    newField = ogr.FieldDefn("outline", ogr.OFTInteger)
    outLayer.CreateField(newField)
    gdal.Polygonize(band, band,outLayer, 0,[],callback=None)
    outDatasource.Destroy()
    sourceRaster=None
    band=None
    os.remove(outline_tif)
    try:
        os.remove(outline_tif + '.aux.xml')
    except:
        pass

print("buffering outline")
if not os.path.exists(buffer):
    fixed_buffer(outline_shp, buffer, buff_dist)

print("tiling orthomosaic")

# create a tile directory
if not os.path.exists(tile_dir):
    os.makedirs(tile_dir)

# open the original dataset to get the x and y size
ds = gdal.Open(in_path + fname)
band = ds.GetRasterBand(1)
xsize = band.XSize
ysize = band.YSize
ds = None

# loop over the dataset tiling using a gdal_translate command
for i in range(0, xsize, tile_size_x):
    for j in range(0, ysize, tile_size_y):
        com_string = "gdal_translate -of GTIFF -b 1 -b 2 -b 3 -b 4 -srcwin " + str(i)+\
                    ", " + str(j) + ", " + str(tile_size_x) + ", " + str(tile_size_y) +\
                    " " + in_path + fname + " " + str(tile_dir) + str(output_filename) + str(i) + "_" + str(j) + ".tif"
        os.system(com_string)

# delete any tiles that contain ANY void pixels
files = []
for f in glob.glob(path):
    f = f.replace("\\", "/")
    files.append(f)

count=0
for f in files:
    d = gdalnumeric.LoadFile(f)
    idx = np.where(np.logical_and(d[0] == 255, d[1] == 255, d[2] == 255))
    if len(idx[0]) >= 1:
        print("remove %s"%f)
        count += 1
        os.remove(f)

# delete any remaining tiles that have areas outside of the buffered polygon
files = []
for f in glob.glob(path):
    f = f.replace("\\", "/")
    files.append(f)

# load the buffered polygon
try:
    dataSource = fiona.open(buffer)
    vertices = []
    for part in dataSource:
        try:
            for j in part["geometry"]["coordinates"]:
                vertices.append(j)
        except:
            pass
    lengths = []
    for j in vertices[0]:
        lengths.append(len(j))
    idx = np.where(lengths == np.max(lengths))[0][0]
    poly = Polygon(vertices[0][idx])
except:
    dataSource = fiona.open(buffer)
    vertices = []
    for part in dataSource:
        try:
            for j in part["geometry"]["coordinates"]:
                for k in j:
                    vertices.append(k)
        except:
            pass
    poly = Polygon(vertices)

count = 0
for f in files:
    ds = gdal.Open(f)
    cols = ds.GetRasterBand(1).XSize
    rows = ds.GetRasterBand(1).YSize
    gt = ds.GetGeoTransform()
    ds = None
    # size of grid (minx, stepx, 0, maxy, 0, -stepy)
    minx, maxy = gt[0], gt[3]
    maxx, miny = gt[0] + gt[1] * cols, gt[3] + gt[5] * rows
    vertices = [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy]]
    poly_tmp = Polygon(vertices)
    try:
        overlap_area = poly.intersection(poly_tmp).area
        if overlap_area < (gt[1]**2 * (tile_size_x*tile_size_y)) - 0.001:
            count += 1
            print("remove %s"%f)
            os.remove(f)
    except:
        pass


# create tiled sub-directories with gridded tiles (to avoid full processing)
files = []
for f in glob.glob(path):
    f = f.replace("\\", "/")
    files.append(f)

centroids = []
center_x = []
center_y = []
for f in files:
    ds = gdal.Open(f)
    cols = ds.GetRasterBand(1).XSize
    rows = ds.GetRasterBand(1).YSize
    gt = ds.GetGeoTransform()
    ds = None
    # size of grid (minx, stepx, 0, maxy, 0, -stepy)
    minx, maxy = gt[0], gt[3]
    maxx, miny = gt[0] + gt[1] * cols, gt[3] + gt[5] * rows
    centroids.append((np.average([maxx, minx]), np.average([maxy, miny])))
    center_x.append(np.average([maxx, minx]))
    center_y.append(np.average([maxy, miny]))

center_x = np.unique(center_x)
center_y = np.unique(center_y)

dir_out = path.split('site*.tif')[0]+'grid1/'
os.mkdir(dir_out)
centroids_grid = []
for x in center_x[0::2]:
    for y in center_y[0::2]:
        centroids_grid.append((x, y))
final_centroids = list(set(centroids).intersection(centroids_grid))
for c1 in final_centroids:
    for idx, c2 in enumerate(centroids):
        if c1 == c2:
            try:
                shutil.move(files[idx], dir_out)
            except:
                pass

dir_out = path.split('site*.tif')[0]+'grid2/'
os.mkdir(dir_out)
centroids_grid = []
for x in center_x[1::2]:
    for y in center_y[1::2]:
        centroids_grid.append((x, y))
final_centroids = list(set(centroids).intersection(centroids_grid))
for c1 in final_centroids:
    for idx, c2 in enumerate(centroids):
        if c1 == c2:
            try:
                shutil.move(files[idx], dir_out)
            except:
                pass

dir_out = path.split('site*.tif')[0]+'grid3/'
os.mkdir(dir_out)
centroids_grid = []
for x in center_x[0::2]:
    for y in center_y[1::2]:
        centroids_grid.append((x, y))
final_centroids = list(set(centroids).intersection(centroids_grid))
for c1 in final_centroids:
    for idx, c2 in enumerate(centroids):
        if c1 == c2:
            try:
                shutil.move(files[idx], dir_out)
            except:
                pass

dir_out = path.split('site*.tif')[0]+'grid4/'
os.mkdir(dir_out)
centroids_grid = []
for x in center_x[1::2]:
    for y in center_y[0::2]:
        centroids_grid.append((x, y))
final_centroids = list(set(centroids).intersection(centroids_grid))
for c1 in final_centroids:
    for idx, c2 in enumerate(centroids):
        if c1 == c2:
            try:
                shutil.move(files[idx], dir_out)
            except:
                pass
