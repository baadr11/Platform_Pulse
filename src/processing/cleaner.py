import logging 
import os 
import sys 
import re 

import pandas as pd 
import numpy as np 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

logger =logging .getLogger (__name__ )

def remove_duplicates_fuzzy (df :pd .DataFrame ,text_column :str ="text",threshold :int =85 )->pd .DataFrame :
    if df .empty or text_column not in df .columns :
        return df 
    try :
        from fuzzywuzzy import fuzz 
    except ImportError :
        logger .warning ("fuzzywuzzy not available - using simple dedup")
        return df .drop_duplicates (subset =[text_column ])

    original_count =len (df )
    df =df .copy ().dropna (subset =[text_column ]).reset_index (drop =True )
    to_drop =set ()
    texts =df [text_column ].tolist ()
    for i in range (len (texts )):
        if i in to_drop :
            continue 
        for j in range (i +1 ,min (i +50 ,len (texts ))):
            if j in to_drop :
                continue 
            try :
                if fuzz .ratio (str (texts [i ])[:200 ],str (texts [j ])[:200 ])>=threshold :
                    to_drop .add (j )
            except Exception :
                continue 
    df =df .drop (index =list (to_drop ))
    removed =original_count -len (df )
    if removed >0 :
        logger .info ("Removed %d duplicate records",removed )
    return df .reset_index (drop =True )

def remove_empty_short (df :pd .DataFrame ,text_column :str ="text",min_length :int =5 )->pd .DataFrame :
    if df .empty or text_column not in df .columns :
        return df 
    original_count =len (df )
    df =df .copy ().dropna (subset =[text_column ])
    df =df [df [text_column ].str .strip ().str .len ()>=min_length ]
    removed =original_count -len (df )
    if removed >0 :
        logger .info ("Removed %d empty or short texts (< %d chars)",removed ,min_length )
    return df .reset_index (drop =True )

def remove_noise (df :pd .DataFrame ,text_column :str ="text")->pd .DataFrame :
    if df .empty or text_column not in df .columns :
        return df 
    df =df .copy ()

    def clean_text (text ):
        if not isinstance (text ,str ):
            return str (text )
        text =re .sub (r'(.)\1{4,}',r'\1\1',text )
        text =re .sub (r'[^\w\s\u0600-\u06FF\u0750-\u077F.,!?؟،؛\-\'\"()]+',' ',text )
        text =re .sub (r'\s+',' ',text ).strip ()
        return text 

    df [text_column ]=df [text_column ].apply (clean_text )
    return df 

def validate_ratings (df :pd .DataFrame ,rating_column :str ="rating",
min_val :float =1 ,max_val :float =5 )->pd .DataFrame :
    if df .empty or rating_column not in df .columns :
        return df 
    original_count =len (df )
    df =df .copy ()
    df [rating_column ]=pd .to_numeric (df [rating_column ],errors ="coerce")
    df =df .dropna (subset =[rating_column ])
    df =df [(df [rating_column ]>=min_val )&(df [rating_column ]<=max_val )]
    removed =original_count -len (df )
    if removed >0 :
        logger .info ("Removed %d ratings out of range (%s-%s)",removed ,min_val ,max_val )
    return df .reset_index (drop =True )

def clean_reviews (input_path :str =None ,output_path :str =None )->pd .DataFrame :
    if input_path is None :
        input_path =os .path .join ("data","raw","reviews_raw.csv")
    if output_path is None :
        output_path =os .path .join ("data","processed","reviews_cleaned.csv")

    if not os .path .exists (input_path ):
        sample_path =os .path .join ("data","sample","sample_reviews.csv")
        if os .path .exists (sample_path ):
            logger .warning ("Using sample data")
            input_path =sample_path 
        else :
            logger .error ("Input file not found: %s",input_path )
            return pd .DataFrame ()

    try :
        df =pd .read_csv (input_path ,encoding ="utf-8-sig")
    except UnicodeDecodeError :
        df =pd .read_csv (input_path ,encoding ="utf-8")

    original_count =len (df )
    df =remove_empty_short (df ,"text",min_length =5 )
    df =remove_noise (df ,"text")
    df =validate_ratings (df ,"rating")
    df =remove_duplicates_fuzzy (df ,"text",threshold =85 )

    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    df .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Review cleaning: %d → %d",original_count ,len (df ))
    return df 

def clean_trends (input_path :str =None ,output_path :str =None )->pd .DataFrame :
    if input_path is None :
        input_path =os .path .join ("data","raw","trends_raw.csv")
    if output_path is None :
        output_path =os .path .join ("data","processed","trends_cleaned.csv")

    if not os .path .exists (input_path ):
        sample_path =os .path .join ("data","sample","sample_trends.csv")
        if os .path .exists (sample_path ):
            logger .warning ("Using sample data")
            input_path =sample_path 
        else :
            logger .error ("Input file not found: %s",input_path )
            return pd .DataFrame ()

    try :
        df =pd .read_csv (input_path ,encoding ="utf-8-sig")
    except UnicodeDecodeError :
        df =pd .read_csv (input_path ,encoding ="utf-8")

    original_count =len (df )
    if "interest_value"in df .columns :
        df ["interest_value"]=pd .to_numeric (df ["interest_value"],errors ="coerce")
        df =df .dropna (subset =["interest_value"])
        df =df [(df ["interest_value"]>=0 )&(df ["interest_value"]<=100 )]
    df =df .drop_duplicates ()

    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    df .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Trends cleaning: %d → %d",original_count ,len (df ))
    return df 

def clean_all ():
    logger .info ("="*60 )
    logger .info ("Starting data cleaning")
    logger .info ("="*60 )
    reviews =clean_reviews ()
    trends =clean_trends ()
    return {"reviews":len (reviews ),"trends":len (trends )}

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    results =clean_all ()
    print (f"\nCleaning summary: {results }")
