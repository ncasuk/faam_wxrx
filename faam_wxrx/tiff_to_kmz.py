'''
Created on 29 Jul 2012

@author: axel
'''


import gdal
import os
import subprocess
import sys
import tempfile


KML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<GroundOverlay>
        <name>%s</name>
        <visibility>1</visibility>
        <open>0</open>
        <color>b5ffffff</color>
        <Icon>
                <href>files/%s</href>
                <viewBoundScale>0.75</viewBoundScale>
        </Icon>
        <LatLonBox>
                <north>%f</north>
                <south>%f</south>
                <east>%f</east>
                <west>%f</west>
        </LatLonBox>
</GroundOverlay>
</kml>
"""


def calc_kmz_boundaries(tiff_file):
    ds = gdal.Open(tiff_file)
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5]
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3]
    ds = None
    return(miny, maxy, minx, maxx)


def gdalwarp(ifile, ofile, *epsg):
    if not epsg:
        epsg = 4326
    cmd = """gdalwarp -t_srs EPSG:%i "%s" "%s" """ % (epsg, ifile, ofile)
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()


def tiff_to_kmz(tiff_file, *args):
    """convert geo-tiff file to kmz file
    :param str tiff_file: tiff_filename
    """
    if args:
        outpath = args[0]
    else:
        outpath = os.environ['HOME']
    # create a temporary folder, which will hold the kmz content
    root_path = tempfile.mktemp()
    os.mkdir(root_path)
    # create "files" folder inside the root_path directory
    os.mkdir(os.path.join(root_path, 'files'))
    png = os.path.join(root_path, 'files', os.path.splitext(os.path.basename(tiff_file))[0]+'.png')
    # create a png from the
    cmd = """gdal_translate -of PNG %s %s""" % (tiff_file, png)
    os.system(cmd)
    # flip the png file in the vertical inplace
    cmd = """convert -flip %s %s""" % (png, png)
    os.system(cmd)
    miny, maxy, minx, maxx = calc_kmz_boundaries(tiff_file)

    kml = KML_TEMPLATE % (os.path.splitext(os.path.basename(tiff_file))[0],
                          os.path.basename(png),
                          miny,
                          maxy,
                          minx,
                          maxx)
    f = open(os.path.join(root_path, 'doc.kml'), 'w')
    f.write(kml)
    f.close()
    if outpath:
        kmz_filename = os.path.join(outpath,
                                    os.path.splitext(os.path.basename(tiff_file))[0] + '.kmz')
    else:
        kmz_filename = os.path.join(os.path.dirname(tiff_file),
                                    os.path.splitext(os.path.basename(tiff_file))[0] + '.kmz')
    cmd = """cd %s && zip -r %s doc.kml files/ """ % (root_path, kmz_filename)
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()
    return kmz_filename


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Converts tiff file to kmz.')
    parser.add_argument('tiff_file', action="store", type=str,
                        help='Input tiff_file.')
    parser.add_argument('outpath', action="store", type=str,
                        help='Outpath for kmz file')
    args = parser.parse_args()

    try:
        outfile = os.path.join(args.outpath, os.path.splitext(args.tiff_file)[0]+'_4326.tif')
        gdalwarp(args.tiff_file, outfile)
        tiff_to_kmz(outfile, args.outpath)
        sys.stdout.write("Created outfile.\n Leaving ...\n")
    except:
        sys.stdout.write("Problem processing ... %s.\n" % (args.tiff_file))
