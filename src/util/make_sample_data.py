import numpy as np
import xarray as xr
import glob

from src.util.shapefile_masks import add_shape_coord_from_data_array

directory_hazard = '/Users/zeliestalhanske/Documents/ch2018_sample'
kanton = 'Zürich'

nc_max_temp = glob.glob(directory_hazard + '/tasmin/' + '*SMHI-RCA_NORESM_EUR44*')[0]
tasmin = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(2015), '-01-01']),
                                                     ''.join([str(2025), '-01-01'])))
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'

tasmin = add_shape_coord_from_data_array(tasmin, shp_dir, kanton)
tasmin = tasmin.where(tasmin[kanton] == 0, other=np.nan)

tasmin = tasmin.where(tasmin['tasmin'] > 21.5).dropna(dim='time', how='all')

tasmin.to_netcdf('../../input_data/ch2018_sample/tasmin/CH2018_zurich_tasmin_SMHI-RCA_NORESM_EUR44_RCP85_QMgrid_2015-2025.nc')
