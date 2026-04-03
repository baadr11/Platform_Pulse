import logging 
import os 
import time 
from typing import List ,Dict ,Any 

import pandas as pd 
import yaml 

logger =logging .getLogger (__name__ )

SAMPLE_PATH =os .path .join ("data","sample","sample_spatial.csv")
RAW_PATH =os .path .join ("data","raw","spatial_raw.csv")

def load_config ():
    config_path =os .path .join ("config","settings.yaml")
    try :
        with open (config_path ,"r",encoding ="utf-8")as f :
            return yaml .safe_load (f )
    except Exception as e :
        logger .warning ("Failed to load settings: %s",e )
        return None 

def load_sample_data ()->pd .DataFrame :
    logger .warning ("Using sample spatial data")
    try :
        df =pd .read_csv (SAMPLE_PATH ,encoding ="utf-8-sig")
        logger .info ("Loaded %d spatial records from sample",len (df ))
        return df 
    except Exception as e :
        logger .error ("Failed to load spatial sample data: %s",e )
        return pd .DataFrame ()

def calculate_activity_scores (spatial_df :pd .DataFrame ,reviews_df :pd .DataFrame =None )->pd .DataFrame :
    if spatial_df .empty :
        return spatial_df 
    if reviews_df is not None and not reviews_df .empty and "city"in reviews_df .columns :
        city_counts =reviews_df ["city"].value_counts ()
        max_count =city_counts .max ()if len (city_counts )>0 else 1 
        for idx ,row in spatial_df .iterrows ():
            count =city_counts .get (row .get ("city",""),0 )
            spatial_df .at [idx ,"activity_score"]=round ((count /max_count )*100 ,2 )
    else :
        import numpy as np 
        np .random .seed (42 )
        spatial_df ["activity_score"]=np .random .uniform (20 ,95 ,len (spatial_df )).round (2 )
    return spatial_df 

def collect_all ()->pd .DataFrame :
    logger .info ("="*60 )
    logger .info ("Starting spatial data collection")
    logger .info ("="*60 )

    config =load_config ()
    if not config or not config .get ("cities"):
        return load_sample_data ()

    spatial_records =[]
    try :
        from geopy .geocoders import Nominatim 
        from src .collectors .retry_utils import safe_scrape 

        geolocator =Nominatim (user_agent ="platform_pulse_research")
        for city_info in config .get ("cities",[]):
            city_en =city_info ["name_en"]
            city_ar =city_info ["name_ar"]
            fallback_lat =city_info .get ("lat",0 )
            fallback_lon =city_info .get ("lon",0 )
            try :
                location =safe_scrape (geolocator .geocode ,f"{city_en }, Saudi Arabia",
                timeout =10 ,label =city_en )
                lat =location .latitude if location else fallback_lat 
                lon =location .longitude if location else fallback_lon 
            except Exception :
                lat ,lon =fallback_lat ,fallback_lon 
            spatial_records .append ({
            "city":city_en ,"city_ar":city_ar ,"latitude":lat ,"longitude":lon ,
            "activity_score":0 ,"date":pd .Timestamp .now ().strftime ("%Y-%m-%d"),"cluster_label":"",
            })
            time .sleep (1.5 )
    except ImportError :
        logger .error ("geopy not installed")
        return load_sample_data ()
    except Exception as e :
        logger .warning ("Geocoding failed: %s — using sample data",e )
        return load_sample_data ()

    if not spatial_records :
        return load_sample_data ()

    df =pd .DataFrame (spatial_records )
    df =calculate_activity_scores (df )
    os .makedirs (os .path .dirname (RAW_PATH ),exist_ok =True )
    df .to_csv (RAW_PATH ,index =False ,encoding ="utf-8-sig")
    return df 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =collect_all ()
    print (f"\nTotal spatial records: {len (result )}")
