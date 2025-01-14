# GEE Task - Hybrid Coordinate Ocean Model, Water Velocity
## generate ocean current direction for the last 10 days

Bounding Box: [lowerleft_longitude: 69,lowerleft_latitude: 15.7, upperright_longitude: 74, upperright_latitude: 20.37]

Date Range: 2020-11-05T00:00 - 2020-11-14T21:00 (with 3hr intervals)

Output Data: GeoTiff files with bands `velocity_u_0`, `velocity_v_0`, `speed_0` and `direction_0` for multiple resolutions of 0.08deg, 5x5km and 10x10km.

The visualization of the data is done on the Jupyter Notebook using geemap module available for python.

![Raw Data Map](raw_data_map.png)
Raw Data Map

![Ocean Current Direction](ocean_current_Direction.png)
Ocean Current Direction

![Ocean Current Speed](ocean_current_speed.png)
Ocean Current Speed