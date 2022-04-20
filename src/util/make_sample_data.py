import numpy as np
import xarray as xr
import glob

from src.util.shapefile_masks import add_shape_coord_from_data_array


directory_hazard = '/Users/szelie/OneDrive - ETH Zurich/data/ch2018_sample'
kanton = 'Zürich'

nc_max_temp = glob.glob(directory_hazard + '/tasmax/' + '*SMHI-RCA_NORESM_EUR44*')[0]
tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(2055), '-01-01']),
                                                     ''.join([str(2065), '-01-01'])))
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'

tasmax = add_shape_coord_from_data_array(tasmax, shp_dir, kanton)
tasmax = tasmax.where(tasmax[kanton] == 0, other=np.nan)

tasmax = tasmax.where(tasmax['tasmax'] > 21.5).dropna(dim='time', how='all')

tasmax.to_netcdf('../../input_data/ch2018_sample/2020/tasmax/CH2018_zurich_tasmax_SMHI-RCA_NORESM_EUR44_RCP85_QMgrid_2015-2025.nc')



nc_min_temp = glob.glob(directory_hazard + '/tasmin/' + '*SMHI-RCA_NORESM_EUR44*')[0]
tasmin = xr.open_dataset(nc_min_temp).sel(time=slice(''.join([str(2055), '-01-01']),
                                                     ''.join([str(2065), '-01-01'])))
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'

tasmin = add_shape_coord_from_data_array(tasmin, shp_dir, kanton)
tasmin = tasmin.where(tasmin[kanton] == 0, other=np.nan)

tasmin = tasmin.where(tasmax['tasmax'] > 21.5).dropna(dim='time', how='all')

tasmin.to_netcdf('../../input_data/ch2018_sample/2020/tasmin/CH2018_zurich_tasmin_SMHI-RCA_NORESM_EUR44_RCP85_QMgrid_2015-2025.nc')

