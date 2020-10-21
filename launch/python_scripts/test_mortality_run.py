import sys
import pandas as pd
from climada.entity import Exposures
from src.impact_calculation.impact_heat import ImpactsHeatMortality
from src.write_entities.define_exposures import call_exposures_switzerland_mortality

sys.path.append('../../')

directory_output = '../../output/impact_ch/'  # where to save to output
directory_hazard = '../../input_data/ch2018_sample/'  # test data
n_mc = 2
years = [2020]
scenarios = ['RCP85']
nyears_hazards = 10

directory_if = '../../input_data/impact_functions/'
annual_deaths = pd.read_excel(''.join([directory_if, 'annual_deaths.xlsx']))

directory_exposures = '../../input_data/exposures/'
file_info = ''.join([directory_exposures, 'age_categories.csv'])
file_locations = ''.join([directory_exposures, 'STATPOP2018.csv'])
shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/'
file_cantons = ''.join([shp_dir, 'swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'])
#exposures = call_exposures_switzerland_mortality(file_info, file_locations, file_cantons, annual_deaths, save=True)
exposures = {}
for category in ['O', 'U']:
    exposures_file = ''.join([directory_exposures, 'exposures_mortality_ch_',category,'.h5'])
    exposures[category] = Exposures()
    exposures[category].read_hdf5(exposures_file)
    exposures[category] = exposures[category][exposures[category]['canton'] == 'Zürich']

impacts_mortality = ImpactsHeatMortality(scenarios, years, n_mc)
impacts_mortality.impacts_years_scenarios(exposures, directory_hazard, nyears_hazards)
