import sys
import pandas as pd
from climada.entity import Exposures
import time

from climada.hazard import Hazard

from src.write_entities.define_hazard import call_hazard_productivity

sys.path.append('../../')
from src.impact_calculation.impact_heat import ImpactsHeatMortality, ImpactsHeatProductivity
from src.write_entities.define_exposures import call_exposures_switzerland_mortality, \
    call_exposures_switzerland_productivity



sensibility_analysis=True
directory_output = '../../output/productivity_results/'  # where to save to output
directory_hazard ='/Users/szelie/OneDrive - ETH Zurich/data/ch2018_sample/'  # test data
n_mc = 1
years = [2060]
scenarios = ['RCP85']
nyears_hazards = 8
#hazards = [call_hazard_productivity(directory_hazard, scenarios[0], 2060, nyears_hazard=8, uncertainty_variable='all') for n in range(10)]
#hazard_outside = [hazard['outside'] for hazard in hazards]
#hazard_inside = [hazard['inside'] for hazard in hazards]


directory_if = '../../input_data/impact_functions/'
directory_exposures = '../../input_data/exposures/'

file_info = ''.join([directory_exposures, 'work_intensity.csv'])
file_locations = ''.join([directory_exposures, 'lv95_vollzeitequivalente.csv'])
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'



#exposures = call_exposures_switzerland_productivity(file_info, file_locations, shp_dir, save=True,
#                                                    directory_hazard=directory_hazard)
exposures = {}
for code, category in {'IL': 'inside low physical activity', 'IM': 'inside moderate physical activity',
                       'OM': 'outside moderate physical activity', 'OH': 'outside high physical activity'}.items():
    exposures_file = ''.join([directory_exposures, 'exposures_productivity_ch_', code, '.h5'])
    exposures[category] = Exposures()
    exposures[category].read_hdf5(exposures_file)
    #exposures[category].gdf = exposures[category].gdf[exposures[category].gdf['canton'] == 'Zürich']
    exposures[category] = exposures[category].to_crs('epsg:4326')
    exposures[category].check()
    #exposures[category].write_hdf5(exposures_file)

startTime = time.time()

impacts_productivity = ImpactsHeatProductivity(scenarios, years, n_mc)

if sensibility_analysis:
    uncertainty_variables = ['sun_protection', 'wbgt']
    impacts_productivity_sensibility = {}
    scenarios_str = "_".join(scenarios)
    impacts_productivity = ImpactsHeatProductivity(scenarios, years, n_mc)
    for variable in uncertainty_variables:
        impacts_productivity.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards,save_median_mat=False, uncertainty_variable=variable)
        impacts_productivity_sensibility[variable] =impacts_productivity.agg_impacts_mc
else:
    impacts_productivity.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards, save_median_mat=False, uncertainty_variable='wbgt')

#with open(''.join([directory_output, 'impact_', str(n_mc), 'mc', '.pickle']), 'wb') as handle:
#    pickle.dump(impacts_mortality, handle, protocol=pickle.HIGHEST_PROTOCOL)

executionTime = (time.time() - startTime)

print('Execution time in seconds: ' + str(executionTime))