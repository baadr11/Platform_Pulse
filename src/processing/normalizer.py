import logging 
import os 
import sys 
from datetime import datetime 

import pandas as pd 
import numpy as np 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

logger =logging .getLogger (__name__ )

CITY_MAPPING ={
"الرياض":"Riyadh","رياض":"Riyadh","riyadh":"Riyadh",
"جدة":"Jeddah","جده":"Jeddah","jeddah":"Jeddah",
"مكة":"Mecca","مكة المكرمة":"Mecca","مكه":"Mecca","mecca":"Mecca",
"المدينة":"Medina","المدينة المنورة":"Medina","medina":"Medina",
"الدمام":"Dammam","دمام":"Dammam","dammam":"Dammam",
"الخبر":"Khobar","خبر":"Khobar","khobar":"Khobar",
"أبها":"Abha","ابها":"Abha","abha":"Abha",
"تبوك":"Tabuk","tabuk":"Tabuk",
"الطائف":"Taif","طائف":"Taif","taif":"Taif",
"بريدة":"Buraidah","بريده":"Buraidah","buraidah":"Buraidah",
"حائل":"Hail","حايل":"Hail","hail":"Hail",
"نجران":"Najran","najran":"Najran",
"جازان":"Jazan","جيزان":"Jazan","jazan":"Jazan",
}

CITY_AR_MAPPING ={
"Riyadh":"الرياض","Jeddah":"جدة","Mecca":"مكة المكرمة",
"Medina":"المدينة المنورة","Dammam":"الدمام","Khobar":"الخبر",
"Abha":"أبها","Tabuk":"تبوك","Taif":"الطائف",
"Buraidah":"بريدة","Hail":"حائل","Najran":"نجران","Jazan":"جازان",
}

def normalize_date (date_val )->str :
    if date_val is None or (isinstance (date_val ,float )and pd .isna (date_val )):
        return ""
    if isinstance (date_val ,str )and date_val .strip ()=="":
        return ""
    if isinstance (date_val ,datetime ):
        return date_val .strftime ("%Y-%m-%dT%H:%M:%SZ")
    date_str =str (date_val ).strip ()
    for fmt in ["%Y-%m-%d","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M:%S","%d/%m/%Y","%m/%d/%Y","%d-%m-%Y","%Y/%m/%d"]:
        try :
            return datetime .strptime (date_str ,fmt ).strftime ("%Y-%m-%dT%H:%M:%SZ")
        except ValueError :
            continue 
    try :
        return pd .to_datetime (date_str ).strftime ("%Y-%m-%dT%H:%M:%SZ")
    except Exception :
        return date_str 

def normalize_city (city_name :str )->dict :
    if not city_name or (isinstance (city_name ,float )and pd .isna (city_name )):
        return {"city_en":"","city_ar":""}
    city_str =str (city_name ).strip ().lower ()
    for key ,en_name in CITY_MAPPING .items ():
        if key .lower ()==city_str or key ==str (city_name ).strip ():
            return {"city_en":en_name ,"city_ar":CITY_AR_MAPPING .get (en_name ,"")}
    for key ,en_name in CITY_MAPPING .items ():
        if key .lower ()in city_str or city_str in key .lower ():
            return {"city_en":en_name ,"city_ar":CITY_AR_MAPPING .get (en_name ,"")}
    return {"city_en":str (city_name ).strip (),"city_ar":""}

def normalize_coordinates (lat ,lon )->dict :
    try :
        lat ,lon =float (lat ),float (lon )
    except (ValueError ,TypeError ):
        return {"latitude":None ,"longitude":None }
    if not (-90 <=lat <=90 and -180 <=lon <=180 ):
        return {"latitude":None ,"longitude":None }
    return {"latitude":round (lat ,6 ),"longitude":round (lon ,6 )}

def normalize_reviews (input_path :str =None ,output_path :str =None )->pd .DataFrame :
    if input_path is None :
        for path in [
        os .path .join ("data","processed","reviews_cleaned.csv"),
        os .path .join ("data","raw","reviews_raw.csv"),
        os .path .join ("data","sample","sample_reviews.csv"),
        ]:
            if os .path .exists (path ):
                input_path =path 
                logger .warning ("Using alternate file: %s",path )
                break 

    if output_path is None :
        output_path =os .path .join ("data","processed","reviews_normalized.csv")

    if not input_path or not os .path .exists (input_path ):
        logger .error ("Review file not found")
        return pd .DataFrame ()

    try :
        df =pd .read_csv (input_path ,encoding ="utf-8-sig")
    except UnicodeDecodeError :
        df =pd .read_csv (input_path ,encoding ="utf-8")

    if "date"in df .columns :
        df ["date"]=df ["date"].apply (normalize_date )
    if "city"in df .columns :
        city_info =df ["city"].apply (normalize_city )
        city_df =pd .DataFrame (city_info .tolist ())
        df ["city"]=city_df ["city_en"]
        if "city_ar"not in df .columns :
            df ["city_ar"]=city_df ["city_ar"]

    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    df .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Normalized %d reviews to %s",len (df ),output_path )
    return df 

def normalize_trends (input_path :str =None ,output_path :str =None )->pd .DataFrame :
    if input_path is None :
        for path in [
        os .path .join ("data","processed","trends_cleaned.csv"),
        os .path .join ("data","raw","trends_raw.csv"),
        os .path .join ("data","sample","sample_trends.csv"),
        ]:
            if os .path .exists (path ):
                input_path =path 
                break 

    if output_path is None :
        output_path =os .path .join ("data","processed","trends_normalized.csv")

    if not input_path or not os .path .exists (input_path ):
        logger .error ("Trends data file not found")
        return pd .DataFrame ()

    try :
        df =pd .read_csv (input_path ,encoding ="utf-8-sig")
    except UnicodeDecodeError :
        df =pd .read_csv (input_path ,encoding ="utf-8")

    if "date"in df .columns :
        df ["date"]=df ["date"].apply (normalize_date )
    if "interest_value"in df .columns :
        df ["interest_value"]=pd .to_numeric (df ["interest_value"],errors ="coerce")
        df ["interest_value"]=df ["interest_value"].clip (lower =0 ,upper =100 )
    if "keyword"in df .columns :
        df ["keyword"]=df ["keyword"].str .strip ()
    if "region"in df .columns :
        df ["region"]=df ["region"].str .strip ().str .upper ()

    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    df .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Normalized %d trends records to %s",len (df ),output_path )
    return df 

def normalize_spatial (input_path :str =None ,output_path :str =None )->pd .DataFrame :
    if input_path is None :
        for path in [
        os .path .join ("data","raw","spatial_raw.csv"),
        os .path .join ("data","sample","sample_spatial.csv"),
        ]:
            if os .path .exists (path ):
                input_path =path 
                break 

    if output_path is None :
        output_path =os .path .join ("data","processed","spatial_normalized.csv")

    if not input_path or not os .path .exists (input_path ):
        logger .error ("Spatial data file not found")
        return pd .DataFrame ()

    try :
        df =pd .read_csv (input_path ,encoding ="utf-8-sig")
    except UnicodeDecodeError :
        df =pd .read_csv (input_path ,encoding ="utf-8")

    if "latitude"in df .columns and "longitude"in df .columns :
        coords =df .apply (
        lambda row :normalize_coordinates (row .get ("latitude"),row .get ("longitude")),axis =1 )
        coords_df =pd .DataFrame (coords .tolist ())
        df ["latitude"]=coords_df ["latitude"]
        df ["longitude"]=coords_df ["longitude"]

    if "date"in df .columns :
        df ["date"]=df ["date"].apply (normalize_date )

    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    df .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Normalized %d spatial records to %s",len (df ),output_path )
    return df 

def normalize_all ():
    logger .info ("="*60 )
    logger .info ("Starting data normalization")
    logger .info ("="*60 )
    reviews =normalize_reviews ()
    trends =normalize_trends ()
    spatial =normalize_spatial ()
    return {"reviews":len (reviews ),"trends":len (trends ),"spatial":len (spatial )}

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    results =normalize_all ()
    print (f"\nNormalization summary: {results }")
