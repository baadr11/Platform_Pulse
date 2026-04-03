import os 
import time 
import pandas as pd 
import numpy as np 
import streamlit as st 


def _secrets_or_env (key :str ,default =""):
    try :
        return st .secrets .get (key ,os .getenv (key ,default ))
    except Exception :
        return os .getenv (key ,default )


def _data_is_stale (path :str ,max_age_hours :int =6 )->bool :
    if not os .path .exists (path ):
        return True 
    age =time .time ()-os .path .getmtime (path )
    return age >max_age_hours *3600 


def collect_trends_live ()->pd .DataFrame :
    composite_path =os .path .join ("data","processed","composite_index.csv")
    if not _data_is_stale (composite_path ,max_age_hours =6 ):
        return pd .DataFrame ()
    try :
        from pytrends .request import TrendReq 
        pytrends =TrendReq (hl ="ar",tz =180 )
        keywords =["وظائف توصيل","تسجيل كريم كابتن","سائق أوبر","العمل في مرسول","delivery job riyadh"]
        all_rows =[]
        for i in range (0 ,len (keywords ),5 ):
            batch =keywords [i :i +5 ]
            try :
                pytrends .build_payload (batch ,cat =0 ,timeframe ="today 12-m",geo ="SA")
                data =pytrends .interest_over_time ()
                if not data .empty :
                    data =data .drop (columns =["isPartial"],errors ="ignore")
                    for kw in batch :
                        if kw in data .columns :
                            for date ,val in data [kw ].items ():
                                all_rows .append ({"keyword":kw ,"date":date .strftime ("%Y-%m-%d"),
                                "region":"SA","interest_value":float (val )})
                time .sleep (2 )
            except Exception :
                continue 
        if all_rows :
            df =pd .DataFrame (all_rows )
            os .makedirs ("data/raw",exist_ok =True )
            df .to_csv ("data/raw/trends_raw.csv",index =False ,encoding ="utf-8-sig")
            return df 
    except Exception :
        pass 
    return pd .DataFrame ()


def collect_reviews_live ()->pd .DataFrame :
    reviews_path =os .path .join ("data","raw","reviews_raw.csv")
    if not _data_is_stale (reviews_path ,max_age_hours =6 ):
        try :
            return pd .read_csv (reviews_path ,encoding ="utf-8-sig")
        except Exception :
            pass 
    try :
        from google_play_scraper import reviews ,Sort 
        apps =[
        ("com.ubercab","Uber","نقل"),
        ("com.careem.acma","Careem","نقل"),
        ("com.hungerstation.android","HungerStation","توصيل"),
        ("com.Jahez.android","Jahez","توصيل"),
        ("com.mrsool.android","Mrsool","توصيل"),
        ]
        all_rows =[]
        for app_id ,name ,sector in apps :
            try :
                result ,_ =reviews (app_id ,lang ="ar",country ="sa",
                sort =Sort .NEWEST ,count =100 )
                for r in result :
                    from datetime import datetime 
                    date_val =r .get ("at",datetime .now ())
                    all_rows .append ({
                    "app_name":name ,"platform":"google_play","sector":sector ,
                    "text":r .get ("content",""),"rating":r .get ("score",0 ),
                    "date":date_val .strftime ("%Y-%m-%d")if isinstance (date_val ,datetime )else str (date_val ),
                    "city":"","version":r .get ("reviewCreatedVersion",""),
                    })
                time .sleep (1.5 )
            except Exception :
                continue 
        if all_rows :
            df =pd .DataFrame (all_rows )
            os .makedirs ("data/raw",exist_ok =True )
            df .to_csv ("data/raw/reviews_raw.csv",index =False ,encoding ="utf-8-sig")
            return df 
    except Exception :
        pass 
    return pd .DataFrame ()


def run_pipeline_after_collection ():
    try :
        from src .processing .cleaner import clean_reviews ,clean_trends 
        from src .processing .normalizer import normalize_reviews ,normalize_trends 
        from src .models .composite_index import compute_composite_index ,compute_gap_analysis 
        clean_reviews ()
        clean_trends ()
        normalize_reviews ()
        normalize_trends ()
        compute_composite_index ()
        compute_gap_analysis ()
        return True 
    except Exception :
        return False 


@st .cache_data (ttl =21600 ,show_spinner =False )
def run_live_collection_cached ():
    os .makedirs ("data/raw",exist_ok =True )
    os .makedirs ("data/processed",exist_ok =True )
    os .makedirs ("data/sample",exist_ok =True )

    composite_path =os .path .join ("data","processed","composite_index.csv")

    if not _data_is_stale (composite_path ,max_age_hours =6 ):
        return {"status":"fresh","source":"live"}

    got_trends =not collect_trends_live ().empty 
    got_reviews =not collect_reviews_live ().empty 
    got_social =not collect_social_live ().empty 

    if got_trends or got_reviews or got_social :
        success =run_pipeline_after_collection ()
        if success and os .path .exists (composite_path ):
            return {"status":"collected","source":"live",
            "trends":got_trends ,"reviews":got_reviews }

    from src .models .composite_index import compute_composite_index ,compute_gap_analysis 
    try :
        compute_composite_index ()
        compute_gap_analysis ()
    except Exception :
        pass 

    return {"status":"sample","source":"sample"}


def collect_social_live ()->pd .DataFrame :
    social_path =os .path .join ("data","raw","social_raw.csv")
    if not _data_is_stale (social_path ,max_age_hours =3 ):
        try :
            return pd .read_csv (social_path ,encoding ="utf-8-sig")
        except Exception :
            pass 
    try :
        import sys 
        sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))
        from src .collectors .social_collector import collect_all 
        import asyncio 
        import nest_asyncio 
        nest_asyncio .apply ()
        loop =asyncio .new_event_loop ()
        df =loop .run_until_complete (collect_all ())
        loop .close ()
        if df is not None and not df .empty :
            return df 
    except Exception :
        pass 
    return pd .DataFrame ()
