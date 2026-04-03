import logging 
import os 
from datetime import datetime 

from sqlalchemy import (
Column ,Integer ,String ,Float ,DateTime ,Text ,Index ,
create_engine 
)
from sqlalchemy .orm import DeclarativeBase 

logger =logging .getLogger (__name__ )

class Base (DeclarativeBase ):
    pass 

class AppReview (Base ):
    __tablename__ ="app_reviews"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    app_name =Column (String (100 ),nullable =False )
    platform =Column (String (20 ),nullable =False )
    sector =Column (String (50 ),nullable =True )
    text =Column (Text ,nullable =True )
    rating =Column (Float ,nullable =True )
    date =Column (DateTime ,nullable =True )
    city =Column (String (100 ),nullable =True )
    version =Column (String (50 ),nullable =True )
    created_at =Column (DateTime ,default =datetime .utcnow )
    __table_args__ =(
    Index ("ix_app_reviews_date","date"),
    Index ("ix_app_reviews_app_name","app_name"),
    Index ("ix_app_reviews_city","city"),
    )

class SearchTrend (Base ):
    __tablename__ ="search_trends"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    keyword =Column (String (200 ),nullable =False )
    date =Column (DateTime ,nullable =False )
    region =Column (String (100 ),nullable =True )
    interest_value =Column (Float ,nullable =True )
    created_at =Column (DateTime ,default =datetime .utcnow )
    __table_args__ =(
    Index ("ix_search_trends_date","date"),
    Index ("ix_search_trends_keyword","keyword"),
    )

class SpatialData (Base ):
    __tablename__ ="spatial_data"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    city =Column (String (100 ),nullable =False )
    city_ar =Column (String (100 ),nullable =True )
    latitude =Column (Float ,nullable =False )
    longitude =Column (Float ,nullable =False )
    activity_score =Column (Float ,nullable =True )
    date =Column (DateTime ,nullable =True )
    cluster_label =Column (String (50 ),nullable =True )
    created_at =Column (DateTime ,default =datetime .utcnow )
    __table_args__ =(
    Index ("ix_spatial_data_city","city"),
    Index ("ix_spatial_data_date","date"),
    )

class OfficialStat (Base ):
    __tablename__ ="official_stats"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    metric_name =Column (String (200 ),nullable =False )
    value =Column (Float ,nullable =True )
    unit =Column (String (50 ),nullable =True )
    date =Column (DateTime ,nullable =True )
    source =Column (String (100 ),nullable =True )
    notes =Column (Text ,nullable =True )
    created_at =Column (DateTime ,default =datetime .utcnow )
    __table_args__ =(
    Index ("ix_official_stats_date","date"),
    Index ("ix_official_stats_metric","metric_name"),
    )

class SentimentResult (Base ):
    __tablename__ ="sentiment_results"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    review_id =Column (Integer ,nullable =True )
    text =Column (Text ,nullable =True )
    sentiment =Column (String (20 ),nullable =True )
    confidence =Column (Float ,nullable =True )
    model =Column (String (100 ),nullable =True )
    app_name =Column (String (100 ),nullable =True )
    sector =Column (String (50 ),nullable =True )
    date =Column (DateTime ,nullable =True )
    created_at =Column (DateTime ,default =datetime .utcnow )
    __table_args__ =(
    Index ("ix_sentiment_results_date","date"),
    )

class CompositeIndex (Base ):
    __tablename__ ="composite_index"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    date =Column (DateTime ,nullable =False )
    city =Column (String (100 ),nullable =True )
    sector =Column (String (50 ),nullable =True )
    index_value =Column (Float ,nullable =True )
    reviews_component =Column (Float ,nullable =True )
    trends_component =Column (Float ,nullable =True )
    spatial_component =Column (Float ,nullable =True )
    sentiment_component =Column (Float ,nullable =True )
    confidence_lower =Column (Float ,nullable =True )
    confidence_upper =Column (Float ,nullable =True )
    estimated_workers =Column (Integer ,nullable =True )
    created_at =Column (DateTime ,default =datetime .utcnow )
    __table_args__ =(
    Index ("ix_composite_index_date","date"),
    Index ("ix_composite_index_city","city"),
    )

class DataQualityLog (Base ):
    __tablename__ ="data_quality_log"
    id =Column (Integer ,primary_key =True ,autoincrement =True )
    source =Column (String (100 ),nullable =False )
    date =Column (DateTime ,default =datetime .utcnow )
    records_total =Column (Integer ,nullable =True )
    records_valid =Column (Integer ,nullable =True )
    records_dropped =Column (Integer ,nullable =True )
    quality_score =Column (Float ,nullable =True )
    notes =Column (Text ,nullable =True )

def create_all_tables (engine ):
    Base .metadata .create_all (engine )
    logger .info ("All database tables created")

def get_engine (db_path =None ,echo =False ):
    if db_path is None :
        db_path =os .path .join ("data","platform_pulse.db")
    db_dir =os .path .dirname (db_path )
    if db_dir :
        os .makedirs (db_dir ,exist_ok =True )
    engine =create_engine (f"sqlite:///{db_path }",echo =echo )
    return engine 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(message)s")
    engine =get_engine ()
    create_all_tables (engine )
    print ("Database created successfully")
