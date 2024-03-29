import pickle
import sys
import pandas as pd
from climada.entity import Exposures
import time

from src.write_entities.define_hazard import call_hazard_mortality

sys.path.append('../../')
from src.impact_calculation.impact_heat import ImpactsHeatMortality
from src.write_entities.define_exposures import call_exposures_switzerland_mortality

directory_output = '../../output/mortality_results/'  # where to save to output
#directory_hazard = '/Users/zeliestalhanske/Desktop/Master/Thesis/Hazard/ch20182/'  # test data
directory_hazard ='/Users/szelie/OneDrive - ETH Zurich/data/ch2018_sample/'  # test data

  # test data
n_mc = 10
years = [2020]
scenarios = ['RCP85']
nyears_hazards = 10

directory_if = '../../input_data/impact_functions/'
annual_deaths_file = ''.join([directory_if, 'summer_deaths.xlsx'])

directory_exposures = '../../input_data/exposures/'
file_info = ''.join([directory_exposures, 'age_categories.csv'])
file_locations = ''.join([directory_exposures, 'STATPOP2018.csv'])
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'
file_cantons = ''.join([shp_dir, 'swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'])
#exposures = call_exposures_switzerland_mortality(file_info, file_locations, file_cantons, annual_deaths_file,
#                                              cantonal_average_deaths=False, save=True)
exposures = {}
for code, category in {'O': 'Over 75', 'U': 'Under 75'}.items():
    exposures_file = ''.join([directory_exposures, 'exposures_mortality_ch_', code, '2.h5'])
    exposures[category] = Exposures()
    exposures[category].read_hdf5(exposures_file)
    #exposures[category].assign_centroids(hazard)
    exposures[category].gdf = exposures[category].gdf[exposures[category].gdf['canton'] == 'Zürich']
    exposures[category].check()
    #exposures[category].write_hdf5(exposures_file)


startTime = time.time()
impacts_mortality = ImpactsHeatMortality(scenarios, years, n_mc)
impacts_mortality.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards)
i1 = impacts_mortality.agg_impacts_mc


#with open(''.join([directory_output, 'impact_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
#    pickle.dump(impacts_mortality, handle, protocol=pickle.HIGHEST_PROTOCOL)

executionTime = (time.time() - startTime)

print('Execution time in seconds: ' + str(executionTime))