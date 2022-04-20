import numpy as np
import pandas as pd
from climada.entity import Exposures
import geopandas as gpd
from shapely.geometry import Point

from src.write_entities.define_hazard import call_hazard_productivity, call_hazard_mortality


def call_exposures_switzerland(population_info, population_loc, shp_cantons_file, epsg_input, epsg_output):
    exposures = Exposures()
    categories = np.unique(population_info['category'])
    exposures.gdf['latitude'] = np.concatenate([np.asarray(population_loc['N_KOORD']).flatten() for cat in categories])
    exposures.gdf['longitude'] = np.concatenate([np.asarray(population_loc['E_KOORD']).flatten() for cat in categories])
    exposures.gdf['if_heat'] = np.concatenate([np.ones(len(population_loc))*(n+1) for n in range(len(categories))])
    exposures.gdf['category'] = np.concatenate([[categories[c]
                                             for n in range(len(population_loc))] for c in range(len(categories))])
    categories_code = {cat: population_info['GIS_Data_code'][population_info['category'] == cat] for cat in categories}
    exposures.gdf['value'] = np.concatenate([np.asarray(population_loc[categories_code[cat]]).sum(axis=1) for cat in categories])
    exposures.gdf.crs = {'init': ''.join(['epsg:', str(epsg_input)])}  # crs: Coordinate Reference Systems
    exposures.set_geometry_points()
    exposures.gdf.fillna(0)
    exposures.to_crs(epsg=epsg_output, inplace=True)
    exposures.gdf = add_cantons(exposures.gdf, shp_cantons_file)
    return exposures


def add_average_deaths(exposures, annual_deaths_file, cantonal_average_deaths):
    average_deaths = pd.read_excel(annual_deaths_file)
    if cantonal_average_deaths:
        exposures.gdf = pd.merge(exposures.gdf, average_deaths[['canton', 'category', 'daily_deaths']], on=['canton', 'category'])
    else:
        exposures.gdf['daily_deaths'] = np.zeros(len(exposures.gdf['value']))
        for category in exposures.gdf['category'].unique():
            exposures.gdf.loc[exposures.gdf['category'] == category, 'daily_deaths'] = \
                average_deaths[(average_deaths['canton'] == 'CH') & (average_deaths['category']==category)]['daily_deaths'].values[0]

    return exposures


def call_exposures_switzerland_mortality(file_info, file_locations, shp_cantons, annual_deaths_file, epsg_input=2056,
                                         epsg_output=4326, population_ratio=True, save=False,
                                         cantonal_average_deaths=True, total_population_ch=8237700, directory_hazard=None):
    population_info = pd.read_csv(file_info)  # file containing the information on the categories
    population_loc = pd.read_csv(file_locations)
    exposures = call_exposures_switzerland(population_info, population_loc, shp_cantons, epsg_input, epsg_output)
    correction_factor_population = total_population_ch/exposures.gdf.value.sum()
    exposures.gdf['value'] = exposures.gdf['value']*correction_factor_population
    if cantonal_average_deaths is True:
        total_population_canton = exposures.gdf[['canton', 'category', 'value']]. \
            groupby(['canton', 'category'], as_index=False).sum(numeric_only=True)
        total_population_canton = total_population_canton.rename(columns={'value': 'total_population_canton'})
        exposures.gdf = exposures.gdf.merge(total_population_canton, on=['canton', 'category'])
    else:
        exposures.gdf['total_population_canton'] = np.zeros(len(exposures.gdf))
        for category in exposures.gdf['category'].unique():
            exposures.gdf.loc[exposures.gdf['category'] == category, 'total_population_canton'] = exposures.gdf[exposures.gdf['category']==category]['value'].sum()
    if population_ratio:
        exposures.gdf['value'] = exposures.gdf['value'].divide((exposures.gdf['total_population_canton']))
    exposures = add_average_deaths(exposures, annual_deaths_file, cantonal_average_deaths)

    if_code = {'Over 75': 1, 'Under 75': 2}

    hazard =call_hazard_mortality(directory_hazard, scenario='RCP85', year=2020, nyears_hazards=2)
    categories_code = {'Over 75': 'O', 'Under 75': 'U'}
    for c in exposures.gdf['category'].unique():
        exposures_category = Exposures()
        exposures_category.gdf = exposures.gdf[exposures.gdf['category'] == c]
        exposures_category.gdf['if_heat'] = if_code[c]
        exposures_category.assign_centroids(hazard)
        exposures_category.check()
        exposures_category.write_hdf5(''.join(['../../input_data/exposures/exposures_mortality_ch_', categories_code[c], '2.h5']))

    return exposures


def call_exposures_switzerland_productivity(file_info, file_locations, shp_cantons, epsg_input=2056, epsg_output=4326,
                                         save=True, directory_hazard=None):
    population_info = pd.read_csv(file_info)  # file containing the information on the categories
    population_loc = pd.read_csv(file_locations)
    population_info = population_info.fillna(0)
    for gis_code in population_loc.columns[2:]:
        population_loc[gis_code] = population_loc[gis_code] * (population_info['Hourly salary (CHF/h)'][
                                       population_info['GIS_Data_code'] == gis_code].values[0])

    exposures = call_exposures_switzerland(population_info, population_loc, shp_cantons, epsg_input, epsg_output)
    hazard = call_hazard_productivity(directory_hazard, 'RCP85', 2060, nyears_hazard=8, uncertainty_variable='all')

    categories_code = {'inside low physical activity': 'IL', 'inside moderate physical activity': 'IM',
                       'outside moderate physical activity': 'OM', 'outside high physical activity': 'OH'}
    if_code = {'inside low physical activity': 1, 'inside moderate physical activity': 2,
                       'outside moderate physical activity': 2, 'outside high physical activity': 3}
    for c in categories_code:
        exposures_category = Exposures()
        exposures_category.gdf = exposures.gdf[exposures.gdf['category'] == c]
        exposures_category.gdf['if_heat'] = if_code[c]
        exposures_category.assign_centroids(hazard['inside'])
        exposures_category.check()
        exposures_category.write_hdf5(''.join(['../../input_data/exposures/exposures_productivity_ch_', categories_code[c], '.h5']))
    return exposures


def add_cantons(vector, shp_cantons_file): # this is used for the exposures, but is
    # quite slow (not a big problem in the monte carlo as the exposures are called only once)
    regions = gpd.read_file(shp_cantons_file)
    vector = gpd.sjoin(vector, regions[['NAME', 'geometry']], how='left', op='intersects')
    return vector.rename(columns={'NAME': 'canton'})
