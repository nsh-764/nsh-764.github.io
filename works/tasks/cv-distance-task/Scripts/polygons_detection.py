# -*- coding: utf-8 -*-
"""
title                : Polygon Detection from Images
author(s)            : Nikhil S Hubballi
last modified on     : 23-11-2020
version              : 1.1
verified by          :
verified on          :
description          : Detection of Road and Building Polygons from images.
project              : CV Distance Task
working directory(s) : 
remarks              :
"""

# imports
import os
import argparse
from glob import glob
# from argparse import Namespace

import cv2
import numpy as np
#from tqdm import tqdm
from rich.progress import track

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.affinity import scale



def import_image(file):
    """ 
        Fetch and read the png image.
    """
    img = cv2.imread(file, cv2.IMREAD_COLOR)
    # cv2.imshow('img', img)
    return img


def detect_roads(img):
    """  
        Identify and extract the road segments from the image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    roads = gray*(gray >= 254)
    # cv2.imshow('img', roads)
    return roads


def detect_gray_area(img):
    """ 
        Identify and extract the gray background areay from the image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = np.where(np.logical_and(gray >= 246, gray <= 249), gray, 0)
    # cv2.imshow('img', gray)
    return gray


def detect_parks(img):
    """ 
        Identify and extract the park regions from the image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = np.where(np.logical_and(gray >= 210, gray <= 220), gray, 0)
    # cv2.imshow('img', gray)
    return gray
    
    
def get_building_edges(img):
    """
        Identify and extract the building edges from the image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = np.where(np.logical_and(gray >= 225, gray <= 240), gray, 0)
    # cv2.imshow('img', gray)
    return gray


def get_3d_build(img):
    """ 
        Identify and extract the special colored/commercial buildings from the image.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (14,12,252), (27,15,255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    # cv2.imshow('img', mask)
    return mask


def mask_array(im):
    """ 
        Extract the zero values from the mask into an image.
    """
    return np.array((im == 0)*255, dtype='uint8')


def detect_buildings(img):
    """ 
        Detect building regions from the image.
    """
    # get 3d and commercial/special color buildings
    mask = get_3d_build(img)
    
    # detect roads and remove from image
    roads = detect_roads(img)
    img = cv2.bitwise_and(img, img, mask=mask_array(roads))

    # detect gray no land use area from image (background gray)
    rem = detect_gray_area(img)
    img = cv2.bitwise_and(img, img, mask=mask_array(rem))

    # use kernel to remove noise from the image
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

    # detect the gray edges between buildings and remove from the image
    edges = get_building_edges(img)
    img = cv2.bitwise_and(img, img, mask=mask_array(edges))
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    # detect and remove parks region from the image.
    park = detect_parks(img)
    img = cv2.bitwise_and(img, img, mask=mask_array(park))
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    
    # merge the above image with 3d/special buildings.    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_OTSU)
    # img = cv2.bitwise_or(thresh, thresh, mask=mask)
    img = cv2.add(thresh, mask)
    
    # remove the map data info from the image bottom corner.
    img = cv2.rectangle(img, (550,480), (639,499), (0), -1)
    img = cv2.erode(img, kernel2)
    # cv2.imshow('img', img)
    return img


def contours2geom(cnt, r=0.009):
    """
        Convert the contours calculated into shapely polygons.
    """
    epsilon = r*cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    approx = np.append(approx, [approx[0]], axis=0).astype(int)
    approx = approx.reshape(approx.shape[0],approx.shape[-1])
    coords = list(map(tuple, approx))
    geom = Polygon(coords)

    return geom


def clean_polygons(geom):
    """ 
        Clean the polygon orientation and validate the geometries.
    """
    geom = MultiPolygon(geom).buffer(0)
    geom = scale(geom, yfact=-1, origin=(320, 250))        
    geom = list(geom) if type(geom) == MultiPolygon else [geom]
    return geom


def transform(geom, gclass='road'):
    """ 
        Transform the geometries into a geopandas dataframe with respective class.
    """
    g = gpd.GeoDataFrame(geometry=geom, crs={'init':'EPSG:3006'})
    g['gclass'] = gclass

    return g


def get_polygon_df(build, roads):
    """
        Identify and Convert the building and road contours into geopandas 
        dataframe with shapely polygon geometries.
    """
    # roads
    _, contour_r, _ = cv2.findContours(
            roads, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    geom_r = clean_polygons(
            [contours2geom(cnt, r=0.0009) for cnt in contour_r if cnt.shape[0] >= 3]
            )
    gr = transform(geom_r)
    
    
    # buildings
    _, contour_b, _ = cv2.findContours(
            build, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )  
    geom_b = clean_polygons(
            [contours2geom(cnt) for cnt in contour_b if cnt.shape[0] >= 3]
            )
    gb = transform(geom_b, gclass='building')

    # combine geodataframes.
    gdf = pd.concat([gb, gr])
    gdf = gdf.reset_index(drop=True).reset_index()

    return gdf


def main(file):
    """
        Detection of Road and Building Polygons from images and export png and
        geojson outputs of extracted regions.
    """
    basename = os.path.basename(file)
    img = import_image(file)
    
    road = detect_roads(img)
    cv2.imwrite(os.path.join(args.outpath, f'roads_{basename}'), road)

    img = detect_buildings(img)
    cv2.imwrite(os.path.join(args.outpath, f'buildings_{basename}'), img)
    gdf = get_polygon_df(img, road)
    gdf.to_file(
            os.path.join(
                    args.outpath, f'geoms_{basename.replace(".png", ".geojson")}'
                    ), 
            driver='GeoJSON'
    )

    return True

if __name__ == '__main__':

    # args = Namespace(
    #         pngpath='./Data/raw',
    #         outpath='./Data/wip'
    #         ) 

    parser = argparse.ArgumentParser()
    parser.add_argument('-pngpath', type=str,
                        help='Path to folder containing raw images.')
    parser.add_argument('-outpath', type=str,
                        help='Path to folder for exporting output images')

    args = parser.parse_args()
    print(args)

    kernel = np.array(
             [[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]],
             dtype=np.uint8
    )

    kernel2 = np.array(
             [[0, -1, 0], [-1, 4, -1], [0, -1, 0]],
             dtype=np.uint8
    )
    
    png_files = glob(f'{args.pngpath}/*.png')

    print(f'No. of input png files: {len(png_files)}')
    _ = [main(file) for file in track(png_files, description='Detecting Polygons..')]
