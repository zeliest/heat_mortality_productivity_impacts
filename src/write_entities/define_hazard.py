import copy
import joblib
import numpy as np
import xarray as xr
import random
import glob
from pandas import Timestamp
from scipy import sparse
from climada.hazard import Hazard
import pandas as pd


uncertainty_sun = 1.8145035579153919
uncertainty_shadow = 1.0704528967117959
uncertainty_inside = 0.96
rf_inside = joblib.load("../../input_data/regressions/random_forest_wbgt_inside.joblib")
rf_sun = joblib.load("../../input_data/regressions/random_forest_wbgt_sun.joblib")
rf_shadow = joblib.load("../../input_data/regressions/random_forest_wbgt_shadow.joblib")


# In[ ]:


def call_hazard_mortality(directory_hazard, scenario, year, nyears_hazards, model_subset=None):
    """Compute heat hazard for the CH2018 data, considered as any day where the T_max is higher than 22 degrees celsius

            Parameters:
                directory_hazard (str): directory to a folder containing one tasmax folder with all the data files
                scenario (str): scenario for which to compute the hazards
                year(str): year for which to compute the hazards
                uncertainty_variable (str): variable for which to consider the uncertainty. Default: 'all'
                region (str or None): Name of canton. Default: None (all of Switzerland)

            Returns:
                hazards(dict): dictionary containing the hazard heat
                  """
    ny = random.randint(-(nyears_hazards/2), nyears_hazards/2)  # to be added to the year, so that any year in the +5 to -5 range can be picked

    list_files = list(set(glob.glob(''.join([directory_hazard, 'tasmax/', '*', scenario, '*']))))
    if model_subset:
        list_files = [s for s in list_files if any(xs in s for xs in model_subset)]
    nc_max_temp = np.random.choice(list_files)
    tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year + ny), '-05-01']),
                                                         ''.join([str(year + ny), '-10-01'])))  # open as xr dataset
    if not len(tasmax.tasmax):
        tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year), '-05-01']),
                                                             ''.join([str(year), '-10-01'])))

    # replace all values where the maximum
    # temperature does not reach 22 degrees by nas in TASMAX and drop time steps that only have NAs
    # for the entire area: (21.5 because of rounding that happens later)
    tasmax = tasmax.where(tasmax['tasmax'] >= 22).dropna(dim='time', how='all')

    nlats = len(tasmax.lat)  # number of latitudes
    nlons = len(tasmax.lon)  # number of longitudes

    number_days = len(tasmax.time)

    dates = [Timestamp(tasmax.time.values[t]).toordinal() for t in range(number_days)]

    nevents = len(dates)  # number of events
    events = range(len(dates))  # number of each event

    grid_x, grid_y = np.meshgrid(tasmax.lon.values, tasmax.lat.values)
    heat = Hazard('heat')
    heat.centroids.set_lat_lon(grid_y.flatten(), grid_x.flatten(), crs={'init': 'epsg:4326'})
    heat.units = 'degrees C'
    tasmax.tasmax.values[np.isnan(tasmax.tasmax.values)] = 0.  # replace NAs by 0
    heat.intensity = sparse.csr_matrix(tasmax.tasmax.values.reshape(nevents, nlons * nlats))
    heat.event_id = np.array(events)
    heat.event_name = heat.event_id
    heat.frequency = np.ones(nevents)/nevents
    heat.fraction = heat.intensity.copy()
    heat.fraction.data.fill(1)
    heat.date = np.array(dates)
    heat.check()

    tasmax.close()
    del tasmax

    return heat  # return the hazards


def call_hazard_productivity(directory_hazard, scenario, year, nyears_hazard=6, uncertainty_variable='all'):
    """Compute heat inside and heat outside hazards for the ch2018 data, considered as any hour where the WBGT is higher
        than 22 degrees celsius

            Parameters:
                directory_hazard (str): directory to a folder containing one tasmax and one tasmin folder with all the
                                        data files
                scenario (str): scenario for which to compute the hazards
                year(str): year for which to compute the hazards
                uncertainty_variable (str): variable for which to consider the uncertainty. Default: 'all'
                kanton (str or None): Name of canton. Default: None (all of Switzerland)
                sun_protection (bool): rather to consider the adaptation measure sun_protection. Default: False
                working_hours (list): hours where people are working. list with the first number being when they
                        start in the day, the second when they start their midday break,
                        third when they start in the afternoon and last when they finished in the evening
                        Default:[8,12,13,17]
                only_outside (bool): rather damage occurs only outside (buildings are well insulated from heat)
                        Default: False

            Returns:
                hazards(dict): dictionary containing the hazard 'heat outside' and 'heat inside'
                  """

    if uncertainty_variable == 'all' or uncertainty_variable == 'years':
        ny = random.randint(-nyears_hazard/2, nyears_hazard/2)  # to be added to the year, so that any year in the +5 to -5 range can be picked
    else:  # if we are testing the sensitivity to the change in variables, we always want to be taking
        # the same year and therefore add 0
        ny = 0

    if uncertainty_variable == 'simulations' or uncertainty_variable == 'all':
        nc_max_temp = np.random.choice(list(set(glob.glob(''.join([directory_hazard, 'tasmax/', '*', scenario, '*'])))))
    else:
        nc_max_temp = glob.glob(directory_hazard + '/tasmax/' + '*SMHI-RCA_NORESM_EUR44*')[0]

    nc_min_temp = nc_max_temp.replace('max', 'min')  # take equivalent tasmin file
    tasmax = xr.open_dataset(nc_max_temp).sel(time=slice(''.join([str(year + ny), '-05-01']),
                                                         ''.join([str(year + ny), '-10-01'])))  # open as xr dataset
    tasmin = xr.open_dataset(nc_min_temp).sel(time=slice(''.join([str(year + ny), '-05-01']),
                                                         ''.join([str(year + ny), '-10-01'])))
    condition = ((tasmax['tasmax'] > 23)&(tasmax.time.dt.dayofweek < 6))
    #if len(np.unique(condition))==1:
    #    condition = ((tasmax['tasmax'] > 22) & (tasmax.time.dt.dayofweek < 6))
    tasmax = tasmax.where(condition, drop=True).fillna(0)
    tasmin = tasmin.where(condition, drop=True).fillna(0)

    hours = np.array([9,10,11,12,14,15,16,17])

    # replace all values where the maximum
    # temperature does not reach 22 degrees by nas in both TASMIN and TASMAX and drop time steps that only have NAs
    # for the entire area:

    nlats = len(tasmax.lat)  # number of latitudes
    nlons = len(tasmax.lon)  # number of longitudes
    dates = np.repeat([pd.to_datetime(x).toordinal() for x in tasmax.time.values], 8)
    tasmax = sparse.csr_matrix((np.tile(tasmax.tasmax.values.flatten(), 8)))
    tasmin = sparse.csr_matrix((np.tile(tasmin.tasmin.values.flatten(), 8)))

    time = np.repeat(np.array(hours),tasmax[tasmax>0].shape[1]/8)
    input_matrix = np.column_stack([time,tasmin.data, tasmax.data])

    wbgt_outside = copy.deepcopy(tasmax)
    wbgt_inside = copy.deepcopy(tasmax)
    del tasmax
    del tasmin

    if uncertainty_variable == 'sun_protection' or uncertainty_variable == 'all':
        sun_shadow = [rf_shadow, rf_sun]
        uncertainty_sun_shadow = [uncertainty_shadow, uncertainty_sun]
        rd = np.random.choice([0, 1])
        rf_outside = sun_shadow[rd]
        uncertainty_outside = uncertainty_sun_shadow[rd]
    else:
        rf_outside = rf_sun
        uncertainty_outside = uncertainty_sun

    if uncertainty_variable == 'wbgt' or uncertainty_variable == 'all':
        data = rf_outside.predict(input_matrix) + np.random.normal(0, uncertainty_outside)
        data[data<22] = 0
        wbgt_outside.data = data
        data = rf_inside.predict(input_matrix) + np.random.normal(0, uncertainty_inside)
        data[data<22] = 0
        wbgt_inside.data = data

    else:
        data = rf_outside.predict(input_matrix)
        data[data<22] = 0
        wbgt_outside.data = data
        data = rf_inside.predict(input_matrix)
        data[data <22] = 0
        wbgt_inside.data = data

    wbgt_outside =  sparse.csr_matrix(wbgt_outside.reshape(len(dates), nlons * nlats))
    wbgt_inside = sparse.csr_matrix(wbgt_inside.reshape(len(dates), nlons * nlats))
    wbgt_data = {'outside': wbgt_outside, 'inside': wbgt_inside}
    hazards = {}

    for hazard_type in wbgt_data:  # write down the events in Hazard class
        subset = wbgt_data[hazard_type].sum(axis=1).A1 > 0
        subset[0] = True
        wbgt_data[hazard_type] = wbgt_data[hazard_type][subset]
        dates_subset = dates[subset]
        hazards[hazard_type] = Hazard.from_hdf5("".join(['../../input_data/hazard_',hazard_type,'.hdf5']))
        #grid_x, grid_y = np.meshgrid(lon, lat)
        #hazards[hazard_type] = Hazard('heat')
        #hazards[hazard_type].centroids.set_lat_lon(grid_y.flatten(), grid_x.flatten(), crs='epsg:4326')
        #hazards[hazard_type].units = 'degrees c'
        hazards[hazard_type].intensity = wbgt_data[hazard_type]
        hazards[hazard_type].event_id = np.arange(1, len(dates_subset)+1)
        hazards[hazard_type].event_name = hazards[hazard_type].event_id
        hazards[hazard_type].frequency = np.ones(len(dates_subset))
        hazards[hazard_type].fraction = hazards[hazard_type].intensity.copy()
        hazards[hazard_type].fraction.data.fill(1)
        hazards[hazard_type].date = np.array(dates_subset)
    return hazards  # return the hazards
