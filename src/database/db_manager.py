import logging 
import os 
from datetime import datetime 
from typing import List ,Optional ,Dict ,Any 

import pandas as pd 
from sqlalchemy import create_engine ,text 
from sqlalchemy .orm import sessionmaker ,Session 

from src .database .schema import (
Base ,AppReview ,SearchTrend ,SpatialData ,
OfficialStat ,SentimentResult ,CompositeIndex ,
DataQualityLog ,get_engine ,create_all_tables 
)

logger =logging .getLogger (__name__ )

class DatabaseManager :

    def __init__ (self ,db_path :Optional [str ]=None ):
        if db_path is None :
            db_path =os .path .join ("data","platform_pulse.db")
        self .db_path =db_path 
        self .engine =get_engine (db_path )
        create_all_tables (self .engine )
        self .SessionLocal =sessionmaker (bind =self .engine )
        logger .info ("Connected to database: %s",db_path )

    def get_session (self )->Session :
        return self .SessionLocal ()

    def insert_reviews (self ,reviews :List [Dict [str ,Any ]])->int :
        session =self .get_session ()
        count =0 
        try :
            for review in reviews :
                record =AppReview (
                app_name =review .get ("app_name",""),
                platform =review .get ("platform","google_play"),
                sector =review .get ("sector",""),
                text =review .get ("text",""),
                rating =review .get ("rating"),
                date =self ._parse_date (review .get ("date")),
                city =review .get ("city",""),
                version =review .get ("version",""),
                )
                session .add (record )
                count +=1 
            session .commit ()
            logger .info ("Inserted %d reviews",count )
        except Exception as e :
            session .rollback ()
            logger .error ("Error inserting reviews: %s",e )
        finally :
            session .close ()
        return count 

    def get_reviews (self ,app_name =None ,city =None ,start_date =None ,end_date =None )->pd .DataFrame :
        session =self .get_session ()
        try :
            query =session .query (AppReview )
            if app_name :
                query =query .filter (AppReview .app_name ==app_name )
            if city :
                query =query .filter (AppReview .city ==city )
            records =query .all ()
            data =[{
            "id":r .id ,"app_name":r .app_name ,"platform":r .platform ,
            "sector":r .sector ,"text":r .text ,"rating":r .rating ,
            "date":r .date ,"city":r .city ,"version":r .version 
            }for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading reviews: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def insert_trends (self ,trends :List [Dict [str ,Any ]])->int :
        session =self .get_session ()
        count =0 
        try :
            for trend in trends :
                record =SearchTrend (
                keyword =trend .get ("keyword",""),
                date =self ._parse_date (trend .get ("date")),
                region =trend .get ("region","SA"),
                interest_value =trend .get ("interest_value"),
                )
                session .add (record )
                count +=1 
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error inserting trends: %s",e )
        finally :
            session .close ()
        return count 

    def get_trends (self ,keyword =None ,start_date =None ,end_date =None )->pd .DataFrame :
        session =self .get_session ()
        try :
            query =session .query (SearchTrend )
            if keyword :
                query =query .filter (SearchTrend .keyword ==keyword )
            records =query .all ()
            data =[{"id":r .id ,"keyword":r .keyword ,"date":r .date ,
            "region":r .region ,"interest_value":r .interest_value }for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading trends: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def insert_spatial (self ,spatial_data :List [Dict [str ,Any ]])->int :
        session =self .get_session ()
        count =0 
        try :
            for item in spatial_data :
                record =SpatialData (
                city =item .get ("city",""),
                city_ar =item .get ("city_ar",""),
                latitude =item .get ("latitude",0 ),
                longitude =item .get ("longitude",0 ),
                activity_score =item .get ("activity_score"),
                date =self ._parse_date (item .get ("date")),
                cluster_label =item .get ("cluster_label",""),
                )
                session .add (record )
                count +=1 
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error inserting spatial data: %s",e )
        finally :
            session .close ()
        return count 

    def get_spatial (self ,city =None )->pd .DataFrame :
        session =self .get_session ()
        try :
            query =session .query (SpatialData )
            if city :
                query =query .filter (SpatialData .city ==city )
            records =query .all ()
            data =[{"id":r .id ,"city":r .city ,"city_ar":r .city_ar ,
            "latitude":r .latitude ,"longitude":r .longitude ,
            "activity_score":r .activity_score ,"date":r .date ,
            "cluster_label":r .cluster_label }for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading spatial data: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def insert_official_stats (self ,stats :List [Dict [str ,Any ]])->int :
        session =self .get_session ()
        count =0 
        try :
            for stat in stats :
                record =OfficialStat (
                metric_name =stat .get ("metric_name",""),
                value =stat .get ("value"),
                unit =stat .get ("unit",""),
                date =self ._parse_date (stat .get ("date")),
                source =stat .get ("source",""),
                notes =stat .get ("notes",""),
                )
                session .add (record )
                count +=1 
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error inserting statistics: %s",e )
        finally :
            session .close ()
        return count 

    def get_official_stats (self ,metric_name =None ,source =None )->pd .DataFrame :
        session =self .get_session ()
        try :
            query =session .query (OfficialStat )
            if metric_name :
                query =query .filter (OfficialStat .metric_name ==metric_name )
            records =query .all ()
            data =[{"id":r .id ,"metric_name":r .metric_name ,"value":r .value ,
            "unit":r .unit ,"date":r .date ,"source":r .source ,"notes":r .notes }
            for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading statistics: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def insert_sentiments (self ,sentiments :List [Dict [str ,Any ]])->int :
        session =self .get_session ()
        count =0 
        try :
            for s in sentiments :
                record =SentimentResult (
                review_id =s .get ("review_id"),
                text =s .get ("text",""),
                sentiment =s .get ("sentiment",""),
                confidence =s .get ("confidence"),
                model =s .get ("model",""),
                app_name =s .get ("app_name",""),
                sector =s .get ("sector",""),
                date =self ._parse_date (s .get ("date")),
                )
                session .add (record )
                count +=1 
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error inserting sentiment results: %s",e )
        finally :
            session .close ()
        return count 

    def get_sentiments (self ,app_name =None ,sentiment =None )->pd .DataFrame :
        session =self .get_session ()
        try :
            query =session .query (SentimentResult )
            if app_name :
                query =query .filter (SentimentResult .app_name ==app_name )
            records =query .all ()
            data =[{"id":r .id ,"text":r .text ,"sentiment":r .sentiment ,
            "confidence":r .confidence ,"model":r .model ,
            "app_name":r .app_name ,"sector":r .sector ,"date":r .date }
            for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading sentiment results: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def insert_composite_index (self ,indices :List [Dict [str ,Any ]])->int :
        session =self .get_session ()
        count =0 
        try :
            for idx in indices :
                record =CompositeIndex (
                date =self ._parse_date (idx .get ("date")),
                city =idx .get ("city","all"),
                sector =idx .get ("sector","all"),
                index_value =idx .get ("index_value"),
                reviews_component =idx .get ("reviews_component"),
                trends_component =idx .get ("trends_component"),
                spatial_component =idx .get ("spatial_component"),
                sentiment_component =idx .get ("sentiment_component"),
                confidence_lower =idx .get ("confidence_lower"),
                confidence_upper =idx .get ("confidence_upper"),
                estimated_workers =idx .get ("estimated_workers"),
                )
                session .add (record )
                count +=1 
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error inserting composite index: %s",e )
        finally :
            session .close ()
        return count 

    def get_composite_index (self ,city =None ,sector =None ,
    start_date =None ,end_date =None )->pd .DataFrame :
        session =self .get_session ()
        try :
            query =session .query (CompositeIndex )
            if city :
                query =query .filter (CompositeIndex .city ==city )
            if sector :
                query =query .filter (CompositeIndex .sector ==sector )
            query =query .order_by (CompositeIndex .date )
            records =query .all ()
            data =[{"id":r .id ,"date":r .date ,"city":r .city ,"sector":r .sector ,
            "index_value":r .index_value ,"reviews_component":r .reviews_component ,
            "trends_component":r .trends_component ,"spatial_component":r .spatial_component ,
            "sentiment_component":r .sentiment_component ,"confidence_lower":r .confidence_lower ,
            "confidence_upper":r .confidence_upper ,"estimated_workers":r .estimated_workers }
            for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading composite index: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def log_quality (self ,source :str ,records_total :int ,
    records_valid :int ,notes :str ="")->None :
        session =self .get_session ()
        try :
            records_dropped =records_total -records_valid 
            quality_score =float (records_valid /records_total *100 )if records_total >0 else 0.0 
            record =DataQualityLog (
            source =source ,
            records_total =records_total ,
            records_valid =records_valid ,
            records_dropped =records_dropped ,
            quality_score =round (quality_score ,2 ),
            notes =notes ,
            )
            session .add (record )
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error logging quality: %s",e )
        finally :
            session .close ()

    def get_quality_logs (self )->pd .DataFrame :
        session =self .get_session ()
        try :
            records =session .query (DataQualityLog ).all ()
            data =[{"id":r .id ,"source":r .source ,"date":r .date ,
            "records_total":r .records_total ,"records_valid":r .records_valid ,
            "records_dropped":r .records_dropped ,
            "quality_score":r .quality_score ,"notes":r .notes }
            for r in records ]
            return pd .DataFrame (data )
        except Exception as e :
            logger .error ("Error reading quality logs: %s",e )
            return pd .DataFrame ()
        finally :
            session .close ()

    def export_to_csv (self ,table_name :str ,output_dir :str ="data/processed")->str :
        os .makedirs (output_dir ,exist_ok =True )
        output_path =os .path .join (output_dir ,f"{table_name }.csv")
        try :
            df =pd .read_sql_table (table_name ,self .engine )
            df .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
            logger .info ("Exported %s to %s (%d records)",table_name ,output_path ,len (df ))
            return output_path 
        except Exception as e :
            logger .error ("Error exporting %s: %s",table_name ,e )
            return ""

    def export_all_tables (self ,output_dir :str ="data/processed")->List [str ]:
        tables =[
        "app_reviews","search_trends","spatial_data",
        "official_stats","sentiment_results","composite_index",
        "data_quality_log"
        ]
        paths =[]
        for table in tables :
            path =self .export_to_csv (table ,output_dir )
            if path :
                paths .append (path )
        return paths 

    def get_table_counts (self )->Dict [str ,int ]:
        session =self .get_session ()
        try :
            counts :Dict [str ,int ]={
            "app_reviews":session .query (AppReview ).count (),
            "search_trends":session .query (SearchTrend ).count (),
            "spatial_data":session .query (SpatialData ).count (),
            "official_stats":session .query (OfficialStat ).count (),
            "sentiment_results":session .query (SentimentResult ).count (),
            "composite_index":session .query (CompositeIndex ).count (),
            "data_quality_log":session .query (DataQualityLog ).count (),
            }
            return counts 
        except Exception as e :
            logger .error ("Error counting records: %s",e )
            return {}
        finally :
            session .close ()

    def clear_table (self ,table_name :str )->None :
        session =self .get_session ()
        try :
            session .execute (text (f"DELETE FROM {table_name }"))
            session .commit ()
        except Exception as e :
            session .rollback ()
            logger .error ("Error clearing table: %s",e )
        finally :
            session .close ()

    @staticmethod 
    def _parse_date (date_val ):
        if date_val is None :
            return None 
        if isinstance (date_val ,datetime ):
            return date_val 
        if isinstance (date_val ,str ):
            for fmt in ["%Y-%m-%d","%Y-%m-%dT%H:%M:%S","%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y","%m/%d/%Y"]:
                try :
                    return datetime .strptime (date_val ,fmt )
                except ValueError :
                    continue 
            try :
                return pd .to_datetime (date_val ).to_pydatetime ()
            except Exception :
                return None 
        return None 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(message)s")
    db =DatabaseManager ()
    counts =db .get_table_counts ()
    print ("\nDatabase status:")
    for table ,count in counts .items ():
        print (f"  {table }: {count } records")
