import logging 
import os 
import sys 
from datetime import datetime ,timedelta 

import pandas as pd 
import numpy as np 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

logger =logging .getLogger (__name__ )

class DataValidator :

    def __init__ (self ):
        self .report ={
        "timestamp":datetime .now ().strftime ("%Y-%m-%d %H:%M:%S"),
        "sources":{},
        "overall_score":0 ,
        }

    def validate_reviews (self ,df :pd .DataFrame )->dict :
        if df .empty :
            return {"valid":0 ,"total":0 ,"score":0 ,"issues":["البيانات فارغة"]}
        total =len (df )
        issues =[]
        valid_mask =pd .Series ([True ]*total ,index =df .index )

        if "rating"in df .columns :
            rating_valid =df ["rating"].between (1 ,5 )
            invalid =(~rating_valid ).sum ()
            if invalid >0 :
                issues .append (f"تقييمات خارج النطاق (1-5): {invalid }")
                valid_mask &=rating_valid 

        if "date"in df .columns :
            dates =pd .to_datetime (df ["date"],errors ="coerce")
            one_year_ago =datetime .now ()-timedelta (days =400 )
            future =datetime .now ()+timedelta (days =1 )
            date_valid =(dates >=one_year_ago )&(dates <=future )|dates .isna ()
            invalid =(~date_valid ).sum ()
            if invalid >0 :
                issues .append (f"تواريخ خارج النطاق: {invalid }")
                valid_mask &=date_valid 

        if "text"in df .columns :
            text_valid =df ["text"].notna ()&(df ["text"].str .len ()>=3 )
            invalid =(~text_valid ).sum ()
            if invalid >0 :
                issues .append (f"نصوص فارغة أو قصيرة: {invalid }")
                valid_mask &=text_valid 

        valid_count =valid_mask .sum ()
        score =round ((valid_count /total )*100 ,1 )if total >0 else 0 
        result ={"valid":int (valid_count ),"total":total ,"score":score ,
        "issues":issues if issues else ["لا توجد مشاكل"]}
        self .report ["sources"]["reviews"]=result 
        logger .info ("Review quality: %s%% (%d/%d)",score ,valid_count ,total )
        return result 

    def validate_trends (self ,df :pd .DataFrame )->dict :
        if df .empty :
            return {"valid":0 ,"total":0 ,"score":0 ,"issues":["البيانات فارغة"]}
        total =len (df )
        issues =[]
        valid_mask =pd .Series ([True ]*total ,index =df .index )

        if "interest_value"in df .columns :
            iv =pd .to_numeric (df ["interest_value"],errors ="coerce")
            value_valid =iv .between (0 ,100 )
            invalid =(~value_valid ).sum ()
            if invalid >0 :
                issues .append (f"قيم خارج النطاق (0-100): {invalid }")
                valid_mask &=value_valid 

        valid_count =valid_mask .sum ()
        score =round ((valid_count /total )*100 ,1 )if total >0 else 0 
        result ={"valid":int (valid_count ),"total":total ,"score":score ,
        "issues":issues if issues else ["لا توجد مشاكل"]}
        self .report ["sources"]["trends"]=result 
        return result 

    def validate_spatial (self ,df :pd .DataFrame )->dict :
        if df .empty :
            return {"valid":0 ,"total":0 ,"score":0 ,"issues":["البيانات فارغة"]}
        total =len (df )
        issues =[]
        valid_mask =pd .Series ([True ]*total ,index =df .index )

        if "latitude"in df .columns :
            lat_valid =pd .to_numeric (df ["latitude"],errors ="coerce").between (15 ,33 )
            invalid =(~lat_valid ).sum ()
            if invalid >0 :
                issues .append (f"خطوط عرض خارج نطاق السعودية: {invalid }")
                valid_mask &=lat_valid 

        if "longitude"in df .columns :
            lon_valid =pd .to_numeric (df ["longitude"],errors ="coerce").between (34 ,56 )
            invalid =(~lon_valid ).sum ()
            if invalid >0 :
                issues .append (f"خطوط طول خارج نطاق السعودية: {invalid }")
                valid_mask &=lon_valid 

        if "activity_score"in df .columns :
            score_valid =pd .to_numeric (df ["activity_score"],errors ="coerce").between (0 ,100 )
            invalid =(~score_valid ).sum ()
            if invalid >0 :
                issues .append (f"درجات نشاط خارج النطاق: {invalid }")
                valid_mask &=score_valid 

        valid_count =valid_mask .sum ()
        score =round ((valid_count /total )*100 ,1 )if total >0 else 0 
        result ={"valid":int (valid_count ),"total":total ,"score":score ,
        "issues":issues if issues else ["لا توجد مشاكل"]}
        self .report ["sources"]["spatial"]=result 
        return result 

    def validate_official (self ,df :pd .DataFrame )->dict :
        if df .empty :
            return {"valid":0 ,"total":0 ,"score":0 ,"issues":["البيانات فارغة"]}
        total =len (df )
        issues =[]
        valid_mask =pd .Series ([True ]*total ,index =df .index )

        if "value"in df .columns :
            value_valid =pd .to_numeric (df ["value"],errors ="coerce").notna ()
            invalid =(~value_valid ).sum ()
            if invalid >0 :
                issues .append (f"قيم غير رقمية: {invalid }")
                valid_mask &=value_valid 

        valid_count =valid_mask .sum ()
        score =round ((valid_count /total )*100 ,1 )if total >0 else 0 
        result ={"valid":int (valid_count ),"total":total ,"score":score ,
        "issues":issues if issues else ["لا توجد مشاكل"]}
        self .report ["sources"]["official"]=result 
        return result 

    def generate_report (self )->dict :
        scores =[s .get ("score",0 )for s in self .report ["sources"].values ()]
        self .report ["overall_score"]=round (np .mean (scores ),1 )if scores else 0 
        logger .info ("Overall quality score: %s%%",self .report ["overall_score"])
        return self .report 

def validate_all ():
    logger .info ("="*60 )
    logger .info ("Starting data validation")
    logger .info ("="*60 )

    validator =DataValidator ()

    file_mappings =[
    ("reviews",[
    os .path .join ("data","processed","reviews_normalized.csv"),
    os .path .join ("data","processed","reviews_cleaned.csv"),
    os .path .join ("data","raw","reviews_raw.csv"),
    os .path .join ("data","sample","sample_reviews.csv"),
    ]),
    ("trends",[
    os .path .join ("data","processed","trends_cleaned.csv"),
    os .path .join ("data","raw","trends_raw.csv"),
    os .path .join ("data","sample","sample_trends.csv"),
    ]),
    ("spatial",[
    os .path .join ("data","processed","spatial_normalized.csv"),
    os .path .join ("data","raw","spatial_raw.csv"),
    os .path .join ("data","sample","sample_spatial.csv"),
    ]),
    ("official",[
    os .path .join ("data","raw","official_raw.csv"),
    os .path .join ("data","sample","sample_official.csv"),
    ]),
    ]

    for source ,paths in file_mappings :
        df =pd .DataFrame ()
        for path in paths :
            if os .path .exists (path ):
                try :
                    df =pd .read_csv (path ,encoding ="utf-8-sig")
                except UnicodeDecodeError :
                    df =pd .read_csv (path ,encoding ="utf-8")
                break 

        if source =="reviews":
            validator .validate_reviews (df )
        elif source =="trends":
            validator .validate_trends (df )
        elif source =="spatial":
            validator .validate_spatial (df )
        elif source =="official":
            validator .validate_official (df )

    report =validator .generate_report ()

    report_path =os .path .join ("data","processed","quality_report.csv")
    os .makedirs (os .path .dirname (report_path ),exist_ok =True )

    rows =[]
    for source ,data in report ["sources"].items ():
        rows .append ({
        "source":source ,"total":data ["total"],"valid":data ["valid"],
        "score":data ["score"],"issues":"; ".join (data .get ("issues",[])),
        })
    pd .DataFrame (rows ).to_csv (report_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Saved quality report to %s",report_path )
    return report 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    validate_all ()
