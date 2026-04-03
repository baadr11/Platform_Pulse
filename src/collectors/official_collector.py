import logging 
import os 
from typing import List ,Dict ,Any 

import pandas as pd 
import yaml 

logger =logging .getLogger (__name__ )

SAMPLE_PATH =os .path .join ("data","sample","sample_official.csv")
RAW_PATH =os .path .join ("data","raw","official_raw.csv")

def load_config ():
    config_path =os .path .join ("config","settings.yaml")
    try :
        with open (config_path ,"r",encoding ="utf-8")as f :
            return yaml .safe_load (f )
    except Exception as e :
        logger .warning ("Failed to load settings: %s",e )
        return None 

def _get_with_retry (url :str ,headers :dict ,timeout :int =15 ):
    try :
        from src .collectors .retry_utils import safe_scrape 
        import requests 
        return safe_scrape (requests .get ,url ,headers =headers ,timeout =timeout ,label =url )
    except ImportError :
        import requests 
        return requests .get (url ,headers =headers ,timeout =timeout )

def scrape_gastat ()->List [Dict [str ,Any ]]:
    data =[]
    logger .info ("Attempting GASTAT data collection")
    try :
        from bs4 import BeautifulSoup 
        urls =["https://www.stats.gov.sa/en/labor-force-survey"]
        headers ={"User-Agent":"Mozilla/5.0"}
        for url in urls :
            try :
                response =_get_with_retry (url ,headers )
                if response is None :
                    continue 
                if response .status_code ==200 :
                    soup =BeautifulSoup (response .text ,"lxml")
                    for table in soup .find_all ("table"):
                        for row in table .find_all ("tr")[1 :]:
                            cols =row .find_all ("td")
                            if len (cols )>=2 :
                                metric =cols [0 ].get_text (strip =True )
                                try :
                                    value =float (cols [1 ].get_text (strip =True ).replace (",","").replace ("%",""))
                                    data .append ({"metric_name":metric ,"value":value ,
                                    "unit":"percentage"if value <=100 else "person",
                                    "date":pd .Timestamp .now ().strftime ("%Y-%m-%d"),
                                    "source":"GASTAT","notes":f"scraped from {url }"})
                                except ValueError :
                                    continue 
            except Exception as e :
                logger .warning ("Failed to access %s: %s",url ,e )
    except ImportError :
        logger .error ("beautifulsoup4 not installed")
    return data 

def scrape_gosi ()->List [Dict [str ,Any ]]:
    return []

def load_sample_data ()->pd .DataFrame :
    logger .warning ("Using sample data — live collection failed")
    try :
        df =pd .read_csv (SAMPLE_PATH ,encoding ="utf-8")
        logger .info ("Loaded %d statistics from sample data",len (df ))
        return df 
    except Exception as e :
        logger .error ("Failed to load sample data: %s",e )
        return pd .DataFrame ()

def collect_all ()->pd .DataFrame :
    logger .info ("="*60 )
    logger .info ("Starting official data collection")
    logger .info ("="*60 )

    all_stats =[]
    try :
        all_stats .extend (scrape_gastat ())
    except Exception as e :
        logger .warning ("GASTAT collection failed: %s",e )

    try :
        all_stats .extend (scrape_gosi ())
    except Exception as e :
        logger .warning ("GOSI collection failed: %s",e )

    use_sample =not all_stats 
    df =load_sample_data ()if use_sample else pd .DataFrame (all_stats )

    if not df .empty :
        os .makedirs (os .path .dirname (RAW_PATH ),exist_ok =True )
        df .to_csv (RAW_PATH ,index =False ,encoding ="utf-8-sig")
        source ="sample"if use_sample else "live"
        logger .info ("Saved %d statistics (%s) to %s",len (df ),source ,RAW_PATH )

    return df 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =collect_all ()
    print (f"\nTotal statistics collected: {len (result )}")
