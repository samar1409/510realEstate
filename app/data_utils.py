# app/data_utils.py

# Keep imports and configuration variables the same as before...
import pandas as pd
import geopandas as gpd
import os
import time
import traceback # Added for detailed error logging

PARCEL_SHAPEFILE_PATH = os.path.join("data", "parcel.shp") # Use the correct name
ASSESSMENT_FILE_PATH = os.path.join("data", "kc_assessment_data.csv")
PIN_COLUMN_PARCELS = "PIN"
PIN_COLUMN_ASSESSMENT = "PIN"
ASSESSMENT_COLUMNS_TO_KEEP = [PIN_COLUMN_ASSESSMENT, 'ADDRESS', 'ASSESSED_VALUE', 'BUILDING_VALUE', 'ACREAGE', 'USE_CODE', 'CITY_CODE']
BELLEVUE_BOUNDS = (-122.24, 47.56, -122.10, 47.65)
_MERGED_DATA_CACHE = None

# --- CORRECTED load_king_county_data function ---
def load_king_county_data(force_reload=False):
    """
    Loads King County parcel Shapefile (EPSG:2926) and assessment data CSV,
    reprojects parcels to EPSG:4326, merges based on PIN, cleans geometry,
    and caches the result. (Corrected CRS Logic)
    """
    global _MERGED_DATA_CACHE
    if _MERGED_DATA_CACHE is not None and not force_reload:
        # print("Returning cached merged King County data.") # Reduce verbosity
        return _MERGED_DATA_CACHE

    start_time = time.time()
    parcels_gdf = None # Initialize to None
    assessment_df = None # Initialize to None

    # --- Load Parcels ---
    print(f"Loading parcel data from Shapefile: {PARCEL_SHAPEFILE_PATH}")
    try:
        parcels_gdf = gpd.read_file(PARCEL_SHAPEFILE_PATH)
        print(f"Loaded {len(parcels_gdf)} parcels.")

        # --- CRS Handling ---
        if parcels_gdf.crs:
            print(f"Detected Parcel CRS: {parcels_gdf.crs}")
            # Use pyproj string to compare reliably if possible, otherwise EPSG code
            # Check if it's already WGS84 (EPSG:4326)
            if parcels_gdf.crs.is_geographic and parcels_gdf.crs.to_epsg() == 4326:
                 print("Parcel CRS is already WGS84 (EPSG:4326).")
            else:
                 # Attempt reprojection to EPSG:4326
                 print(f"Reprojecting parcels from {parcels_gdf.crs.name} to EPSG:4326 (WGS84)...")
                 try:
                      parcels_gdf = parcels_gdf.to_crs(epsg=4326)
                      print("Reprojection complete.")
                 except Exception as e_crs:
                      print(f"ERROR: Failed to reproject from {parcels_gdf.crs} to EPSG:4326: {e_crs}")
                      return None # Cannot proceed without correct CRS
        else:
            print("ERROR: Parcel CRS could not be determined from Shapefile (.prj missing/invalid). Cannot proceed.")
            return None

        # --- PIN Handling ---
        if PIN_COLUMN_PARCELS not in parcels_gdf.columns:
             print(f"ERROR: PIN column '{PIN_COLUMN_PARCELS}' not found in Shapefile. Available: {parcels_gdf.columns.tolist()}")
             return None
        parcels_gdf[PIN_COLUMN_PARCELS] = parcels_gdf[PIN_COLUMN_PARCELS].astype(str)

    except FileNotFoundError:
        print(f"ERROR: Parcel Shapefile not found: '{PARCEL_SHAPEFILE_PATH}'")
        return None
    except Exception as e:
        print(f"ERROR loading or processing parcel Shapefile: {e}")
        traceback.print_exc()
        return None

    # --- Load Assessment Data ---
    print(f"Loading assessment data from CSV: {ASSESSMENT_FILE_PATH}")
    try:
        assessment_df = pd.read_csv(ASSESSMENT_FILE_PATH, low_memory=False)
        if PIN_COLUMN_ASSESSMENT not in assessment_df.columns:
            print(f"ERROR: PIN column '{PIN_COLUMN_ASSESSMENT}' not found in Assessment CSV. Available: {assessment_df.columns.tolist()}")
            return None
        assessment_df[PIN_COLUMN_ASSESSMENT] = assessment_df[PIN_COLUMN_ASSESSMENT].astype(str)
        cols_to_keep = [col for col in ASSESSMENT_COLUMNS_TO_KEEP if col in assessment_df.columns]
        assessment_df = assessment_df[cols_to_keep]
        print(f"Loaded {len(assessment_df)} assessment records.")
    except FileNotFoundError:
        print(f"ERROR: Assessment file not found: '{ASSESSMENT_FILE_PATH}'")
        return None
    except Exception as e:
        print(f"ERROR reading assessment file: {e}")
        return None

    # --- Merging ---
    print("Merging reprojected parcels and assessment data...")
    try:
        # Ensure PIN column names match
        if PIN_COLUMN_PARCELS != PIN_COLUMN_ASSESSMENT:
            parcels_gdf.rename(columns={PIN_COLUMN_PARCELS: PIN_COLUMN_ASSESSMENT}, inplace=True)

        # Select only PIN and geometry from parcels (already reprojected)
        geo_col = parcels_gdf.geometry.name
        parcels_to_merge = parcels_gdf[[PIN_COLUMN_ASSESSMENT, geo_col]]

        # Perform the merge
        merged_df = assessment_df.merge(parcels_to_merge, on=PIN_COLUMN_ASSESSMENT, how='left')
        print(f"Merged data shape (Pandas DataFrame): {merged_df.shape}")

        # --- Convert back to GeoDataFrame and Clean Geometry ---
        print("Converting merged data to GeoDataFrame...")
        # Convert using the geometry column name, ensure correct CRS is set
        merged_gdf = gpd.GeoDataFrame(merged_df, geometry=geo_col, crs="EPSG:4326")

        print(f"Shape before geometry cleaning: {merged_gdf.shape}")
        # Filter out rows with invalid or missing geometry
        initial_count = len(merged_gdf)
        merged_gdf = merged_gdf[merged_gdf.geometry.is_valid & ~merged_gdf.geometry.isna()]
        print(f"Shape after geometry cleaning: {merged_gdf.shape} ({initial_count - len(merged_gdf)} rows removed)")

        if merged_gdf.empty:
             print("WARNING: No valid geometries found after merging and cleaning.")
             _MERGED_DATA_CACHE = merged_gdf
             return _MERGED_DATA_CACHE

        # --- Final Processing ---
        merged_gdf = merged_gdf.fillna("N/A") # Fill NaNs in attributes AFTER cleaning geometry
        final_columns = ASSESSMENT_COLUMNS_TO_KEEP + [geo_col]
        final_columns = [col for col in final_columns if col in merged_gdf.columns]
        merged_gdf = merged_gdf[final_columns]

        _MERGED_DATA_CACHE = merged_gdf # Cache final result
        end_time = time.time()
        print(f"Data loading and processing complete in {end_time - start_time:.2f} seconds.")
        return _MERGED_DATA_CACHE

    except Exception as e:
        print(f"ERROR during data merging or GeoDataFrame final processing: {e}")
        traceback.print_exc()
        return None

# --- CORRECTED get_info_for_pin function ---
def get_info_for_pin(pin):
    """
    Loads merged data (uses cache) and retrieves formatted info
    (excluding geometry BUT including centroid lat/lon) for a specific PIN.
    """
    merged_gdf = load_king_county_data() # Load data (uses cache)
    if merged_gdf is None:
        # Adding print statement here for clarity if data loading failed
        print(f"get_info_for_pin: Cannot proceed because data failed to load.")
        return {"error": "Data not loaded"}
    if merged_gdf.empty:
         # Adding print statement here
         print(f"get_info_for_pin: Cannot find PIN {str(pin)} because merged data is empty.")
         return {"error": f"PIN {str(pin)} not found (data empty after load/clean)."}

    try:
        pin_str = str(pin)
        # Ensure using the correct PIN column name from assessments
        property_data = merged_gdf.loc[merged_gdf[PIN_COLUMN_ASSESSMENT] == pin_str]

        if property_data.empty:
            print(f"get_info_for_pin: PIN {pin_str} not found in merged data.")
            return {"error": f"PIN {pin_str} not found"}
        else:
            property_series = property_data.iloc[0] # Get the first match Series
            geo_col = merged_gdf.geometry.name # Get geometry column name

            # Calculate centroid (geometry should be valid EPSG:4326 here)
            latitude = None
            longitude = None
            if geo_col in property_series and property_series[geo_col] is not None and property_series[geo_col].is_valid:
                try:
                    centroid = property_series[geo_col].centroid
                    latitude = centroid.y
                    longitude = centroid.x
                except Exception as e_cent:
                     print(f"Warning: Could not calculate centroid for PIN {pin_str}: {e_cent}")
            else:
                print(f"Warning: Missing or invalid geometry for PIN {pin_str}, cannot calculate centroid.")

            # Convert attributes to dict, explicitly drop geometry column by name
            info = property_series.drop(geo_col).to_dict()

            # Add coordinates to the info dict
            info['latitude'] = latitude
            info['longitude'] = longitude

            # Format AssessedValue
            if 'ASSESSED_VALUE' in info and info['ASSESSED_VALUE'] != "N/A":
                 try: info['AssessedValueFormatted'] = f"${float(info['ASSESSED_VALUE']):,.0f}"
                 except (ValueError, TypeError): info['AssessedValueFormatted'] = info['ASSESSED_VALUE']

            # print(f"Found info (with coords) for PIN {pin_str}: {info}") # Reduce verbosity
            return info
    except Exception as e:
        print(f"ERROR retrieving info for PIN {pin_str}: {e}")
        traceback.print_exc()
        return {"error": f"Error fetching details for PIN {pin_str}"}


# --- Keep get_parcels_geojson_subset the same as the previous working version ---
def get_parcels_geojson_subset(bounds=None):
    """
    Loads merged/reprojected data, filters by bounds (lat/lon), and returns GeoJSON.
    """
    gdf = load_king_county_data() # This now returns cleaned EPSG:4326 data
    if gdf is None or not isinstance(gdf, gpd.GeoDataFrame) or gdf.empty or gdf.geometry.isnull().all():
        print("Error/Warning: Merged GeoDataFrame not available or geometry is missing/empty in get_parcels_geojson_subset.")
        return '{"type": "FeatureCollection", "features": []}'

    filtered_gdf = gdf
    if bounds:
        print(f"Filtering {len(gdf)} parcels to bounds (EPSG:4326): {bounds}")
        try:
            # Use GeoPandas spatial filter cx[] now that data is in EPSG:4326
            filtered_gdf = gdf.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]]
            print(f"Found {len(filtered_gdf)} parcels within bounds.")
            if len(filtered_gdf) == 0:
                 print("WARNING: No parcels found within the specified bounds.")
                 return '{"type": "FeatureCollection", "features": []}'
        except Exception as e:
             print(f"ERROR during spatial filtering: {e}. Proceeding without filter.")
             filtered_gdf = gdf # Fallback maybe risky, consider returning empty

    # Only proceed if filtered_gdf is not empty
    if filtered_gdf.empty:
        print("Filtered GeoDataFrame is empty, returning empty GeoJSON.")
        return '{"type": "FeatureCollection", "features": []}'

    print(f"Converting {len(filtered_gdf)} filtered parcels to GeoJSON...")
    try:
        geojson_data = filtered_gdf.to_json()
        print("GeoJSON conversion successful.")
        return geojson_data
    except Exception as e:
        print(f"ERROR converting to GeoJSON: {e}")
        traceback.print_exc()
        return '{"type": "FeatureCollection", "features": []}'
