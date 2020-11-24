# -*- coding: utf-8 -*-
"""
title                : Get Distance to closest road/building
author(s)            : Nikhil S Hubballi
last modified on     : 23-11-2020
version              : 1.1
verified by          :
verified on          :
description          : Find the distance from the front side of the shop to 
                        the nearest road/building in the same direction.
project              : CV Task - Kawa Space
working directory(s) : 
remarks              :
"""

# imports

import os
import warnings
import argparse
# from glob import glob
# from argparse import Namespace

import geopandas as gpd
import matplotlib.pyplot as plt
# from shapely.affinity import scale, rotate
from shapely.geometry import Point, LinearRing, MultiPolygon, LineString

warnings.filterwarnings('ignore')


def get_projection(point, poly):
    """ 
        Get the projection point on the polygon and its distance 
        from the anchor point.
    """
    pol_ext = LinearRing(poly.exterior.coords)
    distance = pol_ext.project(point)
    p = pol_ext.interpolate(distance)
    closest_point_coords = list(p.coords)[0]
    
    return distance, closest_point_coords


def find_closest_building(gdf, geom):
    """
        Find the closest building and its features from the anchor point.
    """
    gdf['d'] = gdf['geometry'].apply(lambda x: geom.distance(x))
    idx = gdf['d'].idxmin()

    return gdf.loc[idx]


def get_side(line, point):
    """ 
        Function to calculate which side of the line the point lies on the plane.
    """
    line_coords = list(line.coords)
    x1y1 = line_coords[0]
    x2y2 = line_coords[1]
    xy = list(point.coords)[0]
    
    d = (xy[0] - x1y1[0])*(x2y2[1] - x1y1[1]) - (xy[1] - x1y1[1])*(x2y2[0] - x1y1[0])
    return 'left' if d < 0 else 'right'


def get_build_side_anchor_point(point, geom):
    """ 
        Find which side of the building front side the anchor point lies 
        and also the front side line segment.
    """
    coords = list(geom.boundary.coords)
    lines = [LineString([coords[i], coords[i+1]]) for i, x in enumerate(coords) if i+1 < len(coords)]
    d, coords = get_projection(point, geom)
    front = Point(coords)
    line = [line for line in lines if line.distance(front) < 1e-8]
    line.sort()
    bside = get_side(line[0], point)
    return bside, line[0]


def get_front_side(point, geom):
    """ 
        Get Front side line segment if the anchor point lies within the 
        building else return the anchor point itself.
    """
    if point.within(geom):
        d, coords = get_projection(point, geom)
        front = Point(coords)
        coords = list(geom.boundary.coords)
        lines = [LineString([coords[i], coords[i+1]]) for i, x in enumerate(coords) if i+1 < len(coords)]
        line = [line for line in lines if line.distance(front) < 1e-8]
        line.sort()
        return line[0], 'front side'
    else:
        return point, 'anchor point'


def main():
    """ 
        Process the input geojson file with building and road polygons to
        to get the nearest building/road from the anchor point or front side
        of the building.
    """
    # read the geometry file
    gdf = gpd.read_file(args.filepath)
    
    # get the centroid (considered as the location of the shop.)
    point = MultiPolygon(gdf.geometry.tolist()).envelope.centroid
    # point = Point(319.5, 250.5)
    coords = list(point.coords)[0]
    
    # filter vector file by class and separate roads and buildings.
    build = gdf.query('gclass == "building"').copy()
    road = gdf.query('gclass == "road"').copy()

    # find the closest building to the centroid point
    bdg = find_closest_building(build, point)
    print(f'Index of the building within/closest to which the anchor point lies: {bdg["index"]}')
    build = build[build['index'] != bdg['index']] # fetch buildings other than closest one

    # get the front side line segment if the point lies inside else anchor point.
    front_side, cat = get_front_side(point, bdg.geometry)
    
    # find all the buildings in the direction of the front side or anchor point from the building.
    if type(front_side) == LineString:
        bside = get_side(front_side, bdg.geometry.representative_point())
        
        build['side'] = build['geometry'].apply(
                lambda x: get_side(front_side, x.representative_point())
                )
        
        build = build.query(f'side != "{bside}"')
    elif type(front_side) == Point:
        bside, front_line = get_build_side_anchor_point(front_side, bdg.geometry)
        
        build['side'] = build['geometry'].apply(
                lambda x: get_side(front_line, x.representative_point())
                )
        
        build = build.query(f'side == "{bside}"')
    
    # find the closest building from front side or anchor point.
    if not build.empty:
        build_close = find_closest_building(build, front_side)
        cbd = build_close.d
        print(f'Index of the building closest to {cat}: {build_close["index"]}')
        print(f'Distance to the closest building from the {cat}: {round(cbd,3)} units')
    else:
        cbd = 100000
        print('No building on the front side of the building wrt anchor point')
    
    # find the closest road from the front side or anchor point.
    crd = front_side.distance(MultiPolygon(road.geometry.tolist()))
    print(f'Distance to the closest road from the {cat}: {round(crd,3)} units')
    print("\n")

    if cbd < crd:
        print(f'{os.path.basename(args.filepath)}, {round(cbd,3)} units, "Building"')
    else:
        print(f'{os.path.basename(args.filepath)}, {round(crd,3)} units, "Road"')

    # plot the building and road geometries and the anchor point for reference.
    ax = gdf.plot(column='index', legend=True, categorical=True)
    ax.plot(coords[0], coords[1], 'k*')
    plt.show()
    

if __name__ == '__main__':

    # args = Namespace(
    #         filepath='./Data/wip/geoms_tmp_9.geojson'
    #         ) 

    parser = argparse.ArgumentParser()
    parser.add_argument('-filepath', type=str,
                        help='Path to geojson file with road and building polygons.')

    args = parser.parse_args()
    print("\n")
    print(args)

    main()
