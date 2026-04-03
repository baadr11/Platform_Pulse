import logging 
import os 
import time 
try :
    from tenacity import retry ,stop_after_attempt ,wait_exponential ,retry_if_exception_type ,before_sleep_log 
except ImportError :
    def retry (*a ,**kw ):return lambda f :f 
    def stop_after_attempt (n ):return None 
    def wait_exponential (**kw ):return None 
    def retry_if_exception_type (*a ):return None 
    def before_sleep_log (*a ):return None 
import requests 
from datetime import datetime 
from typing import List ,Dict ,Any 

import pandas as pd 
import yaml 

from src .collectors .retry_utils import safe_scrape 

logger =logging .getLogger (__name__ )

SAMPLE_PATH =os .path .join ("data","sample","sample_reviews.csv")
RAW_PATH =os .path .join ("data","raw","reviews_raw.csv")

def load_config ():
    config_path =os .path .join ("config","settings.yaml")
    try :
        with open (config_path ,"r",encoding ="utf-8")as f :
            return yaml .safe_load (f )
    except Exception as e :
        logger .warning ("Failed to load settings: %s",e )
        return None 

def collect_google_play_reviews (config )->List [Dict [str ,Any ]]:
    all_reviews =[]
    apps =config .get ("apps",{}).get ("google_play",[])
    try :
        from google_play_scraper import reviews ,Sort 
    except ImportError :
        logger .error ("google-play-scraper not installed")
        return []

    for app_info in apps :
        app_id =app_info ["id"]
        app_name =app_info ["name"]
        sector =app_info .get ("sector","")
        try :
            result_data =safe_scrape (reviews ,app_id ,lang ="ar",country ="sa",
            sort =Sort .NEWEST ,count =200 ,label =f"Google Play: {app_name }")
            result =result_data [0 ]if result_data and isinstance (result_data ,tuple )else []
            for review in result :
                all_reviews .append ({
                "app_name":app_name ,"platform":"google_play","sector":sector ,
                "text":review .get ("content",""),"rating":review .get ("score",0 ),
                "date":review .get ("at",datetime .now ()).strftime ("%Y-%m-%d")
                if isinstance (review .get ("at"),datetime )else str (review .get ("at","")),
                "city":"","version":review .get ("reviewCreatedVersion",""),
                })
            logger .info ("Collected %d reviews for %s",len (result ),app_name )
            time .sleep (2 )
        except Exception as e :
            logger .warning ("Failed to collect reviews for %s: %s",app_name ,e )
            continue 
    return all_reviews 

def collect_app_store_reviews (config )->List [Dict [str ,Any ]]:
    all_reviews =[]
    apps =config .get ("apps",{}).get ("app_store",[])
    try :
        from app_store_reviews_reader import AppStoreReviewsReader 
    except ImportError :
        logger .error ("app-store-reviews-reader not installed")
        return []

    for app_info in apps :
        app_id =str (app_info ["id"])
        app_name =app_info ["name"]
        sector =app_info .get ("sector","")
        try :
            reader =AppStoreReviewsReader (app_id =app_id ,country ="sa")
            reviews =safe_scrape (reader .fetch_reviews ,label =f"App Store: {app_name }")or []
            for review in reviews :
                all_reviews .append ({
                "app_name":app_name ,"platform":"app_store","sector":sector ,
                "text":review .get ("content",review .get ("title","")),
                "rating":review .get ("rating",0 ),"date":str (review .get ("date","")),
                "city":"","version":"",
                })
            logger .info ("Collected %d reviews for %s",len (reviews ),app_name )
            time .sleep (2 )
        except Exception as e :
            logger .warning ("Failed to collect reviews for %s: %s",app_name ,e )
            continue 
    return all_reviews 

def calculate_daily_frequency (df :pd .DataFrame )->pd .DataFrame :
    if df .empty :
        return pd .DataFrame ()
    df ["date"]=pd .to_datetime (df ["date"],errors ="coerce")
    return df .groupby ([pd .Grouper (key ="date",freq ="D"),"app_name","sector"]).size ().reset_index (name ="daily_count")

def load_sample_data ()->pd .DataFrame :
    logger .warning ("Using sample data - live collection failed")
    try :
        df =pd .read_csv (SAMPLE_PATH ,encoding ="utf-8")
        logger .info ("Loaded %d reviews from sample data",len (df ))
        return df 
    except Exception as e :
        logger .error ("Failed to load sample data: %s",e )
        return pd .DataFrame ()

def collect_all ()->pd .DataFrame :
    logger .info ("="*60 )
    logger .info ("Starting app review collection")
    logger .info ("="*60 )

    config =load_config ()
    all_reviews =[]
    use_sample =False 

    if config :
        try :
            all_reviews .extend (collect_google_play_reviews (config ))
        except Exception as e :
            logger .warning ("Google Play collection failed: %s",e )
        try :
            all_reviews .extend (collect_app_store_reviews (config ))
        except Exception as e :
            logger .warning ("App Store collection failed: %s",e )

    if not all_reviews :
        use_sample =True 
        df =load_sample_data ()
    else :
        df =pd .DataFrame (all_reviews )

    if not df .empty :
        os .makedirs (os .path .dirname (RAW_PATH ),exist_ok =True )
        df .to_csv (RAW_PATH ,index =False ,encoding ="utf-8-sig")
        source ="sample"if use_sample else "live"
        logger .info ("Saved %d reviews (%s) to %s",len (df ),source ,RAW_PATH )

    freq =calculate_daily_frequency (df )
    if not freq .empty :
        freq_path =os .path .join ("data","raw","reviews_frequency.csv")
        os .makedirs (os .path .dirname (freq_path ),exist_ok =True )
        freq .to_csv (freq_path ,index =False ,encoding ="utf-8-sig")

    return df 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =collect_all ()
    print (f"\nTotal reviews collected: {len (result )}")
