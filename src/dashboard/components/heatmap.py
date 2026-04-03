import os 
import pandas as pd 
import numpy as np 
import streamlit as st 

@st .cache_data (ttl =3600 )
def _load_spatial_data (path :str )->"pd.DataFrame | None":
    try :
        df =pd .read_csv (path ,encoding ="utf-8-sig")
        if "date"in df .columns :
            df ["date"]=pd .to_datetime (df ["date"],errors ="coerce")
        return df 
    except Exception :
        return None 

def _apply_filters (df :pd .DataFrame ,filters :dict )->pd .DataFrame :
    if not filters :
        return df 
    if filters .get ("city")and filters ["city"]!="الكل":
        city_val =filters ["city"]
        mask =pd .Series ([False ]*len (df ),index =df .index )
        for col in ["city_ar","city"]:
            if col in df .columns :
                mask =mask |df [col ].astype (str ).str .contains (city_val ,na =False )
        if mask .any ():
            df =df [mask ]
    if "date"in df .columns :
        df =df .copy ()
        df ["date"]=pd .to_datetime (df ["date"],errors ="coerce")
        if df ["date"].dt .tz is not None :
            df ["date"]=df ["date"].dt .tz_convert (None )
        if filters .get ("date_from"):
            df =df [df ["date"]>=pd .Timestamp (filters ["date_from"])]
        if filters .get ("date_to"):
            df =df [df ["date"]<=pd .Timestamp (filters ["date_to"])]
    return df 

def render_heatmap (filters =None ):
    spatial_path =None 
    for path in [
    os .path .join ("data","processed","spatial_clustered.csv"),
    os .path .join ("data","processed","spatial_normalized.csv"),
    os .path .join ("data","sample","sample_spatial.csv"),
    ]:
        if os .path .exists (path ):
            spatial_path =path 
            break 

    if spatial_path :
        try :
            df =pd .read_csv (spatial_path ,encoding ="utf-8-sig")
        except UnicodeDecodeError :
            df =pd .read_csv (spatial_path ,encoding ="utf-8")
    else :
        df =pd .DataFrame ({
        "city":["Riyadh","Jeddah","Dammam","Mecca","Medina",
        "Khobar","Abha","Tabuk","Taif","Buraidah","Hail","Najran","Jazan"],
        "city_ar":["الرياض","جدة","الدمام","مكة المكرمة","المدينة المنورة",
        "الخبر","أبها","تبوك","الطائف","بريدة","حائل","نجران","جازان"],
        "latitude":[24.7136 ,21.5433 ,26.4207 ,21.3891 ,24.5247 ,
        26.2172 ,18.2164 ,28.3998 ,21.2854 ,26.3260 ,27.5219 ,17.5656 ,16.8892 ],
        "longitude":[46.6753 ,39.1728 ,50.0888 ,39.8579 ,39.5692 ,
        50.1971 ,42.5053 ,36.5715 ,40.4149 ,43.9750 ,41.7057 ,44.2289 ,42.5511 ],
        "activity_score":[92.5 ,85.3 ,78.4 ,61.2 ,55.8 ,70.0 ,30.0 ,25.0 ,35.0 ,28.0 ,22.0 ,18.0 ,20.0 ],
        "cluster_label":["نشاط_عالي","نشاط_عالي","نشاط_عالي",
        "نشاط_متوسط","نشاط_متوسط","نشاط_متوسط",
        "نشاط_منخفض","نشاط_منخفض","نشاط_متوسط",
        "نشاط_منخفض","نشاط_منخفض","نشاط_منخفض","نشاط_منخفض"],
        })

    df =_apply_filters (df ,filters )

    if df .empty :
        st .warning ("لا توجد بيانات مكانية للمدينة المحددة")
        return 

    if "cluster_label"not in df .columns :
        df ["cluster_label"]=df ["activity_score"].apply (
        lambda x :"نشاط_عالي"if x >=60 else ("نشاط_متوسط"if x >=35 else "نشاط_منخفض")
        )

    high =len (df [df ["cluster_label"].str .contains ("عالي",na =False )])
    med =len (df [df ["cluster_label"].str .contains ("متوسط",na =False )])
    low =len (df [df ["cluster_label"].str .contains ("منخفض",na =False )])

    kpi_style ="border-radius:14px; padding:20px 16px; direction:rtl; border:1px solid rgba(255,255,255,0.07); text-align:center;"
    c1 ,c2 ,c3 =st .columns (3 )
    with c1 :
        st .markdown (
        f'<div style="background:linear-gradient(135deg,rgba(0,200,150,.12),rgba(0,200,150,.05));'
        f'border:1px solid rgba(0,200,150,.25);{kpi_style }">'
        f'<p style="margin:0;font-size:.78rem;color:#00c896;font-weight:700">نشاط عالٍ</p>'
        f'<h2 style="margin:8px 0 4px;font-size:2.4rem;font-weight:800;color:#f1f5f9">{high }</h2>'
        f'<p style="margin:0;font-size:.75rem;color:#475569">مدن</p></div>',unsafe_allow_html =True )
    with c2 :
        st .markdown (
        f'<div style="background:linear-gradient(135deg,rgba(245,158,11,.1),rgba(245,158,11,.04));'
        f'border:1px solid rgba(245,158,11,.25);{kpi_style }">'
        f'<p style="margin:0;font-size:.78rem;color:#f59e0b;font-weight:700">نشاط متوسط</p>'
        f'<h2 style="margin:8px 0 4px;font-size:2.4rem;font-weight:800;color:#f1f5f9">{med }</h2>'
        f'<p style="margin:0;font-size:.75rem;color:#475569">مدن</p></div>',unsafe_allow_html =True )
    with c3 :
        st .markdown (
        f'<div style="background:linear-gradient(135deg,rgba(255,107,107,.1),rgba(255,107,107,.04));'
        f'border:1px solid rgba(255,107,107,.25);{kpi_style }">'
        f'<p style="margin:0;font-size:.78rem;color:#ff6b6b;font-weight:700">نشاط منخفض</p>'
        f'<h2 style="margin:8px 0 4px;font-size:2.4rem;font-weight:800;color:#f1f5f9">{low }</h2>'
        f'<p style="margin:0;font-size:.75rem;color:#475569">مدن</p></div>',unsafe_allow_html =True )

    st .markdown ("<br>",unsafe_allow_html =True )

    try :
        import folium 
        from streamlit_folium import st_folium 

        m =None 
        for tile ,attr in [
        ("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        "© OpenStreetMap contributors © CARTO"),
        ("CartoDB dark_matter",None ),
        ("OpenStreetMap",None ),
        ]:
            try :
                if attr :
                    m =folium .Map (location =[23.8859 ,45.0792 ],zoom_start =6 ,tiles =tile ,attr =attr )
                else :
                    m =folium .Map (location =[23.8859 ,45.0792 ],zoom_start =6 ,tiles =tile )
                break 
            except Exception :
                continue 

        if m is None :
            m =folium .Map (location =[23.8859 ,45.0792 ],zoom_start =6 )

        def _get_color (label :str )->str :
            if "عالي"in str (label ):return "#00c896"
            if "متوسط"in str (label ):return "#f59e0b"
            return "#ff6b6b"

        for _ ,row in df .iterrows ():
            lat =row .get ("latitude",0 )
            lon =row .get ("longitude",0 )
            score =row .get ("activity_score",0 )
            label =row .get ("cluster_label","")
            city_ar =row .get ("city_ar",row .get ("city",""))
            color =_get_color (label )

            popup_html =f"""
            <div style="font-family:'Tajawal',Arial;direction:rtl;width:200px;text-align:right;
                        background:#0d1526;padding:10px;border-radius:8px;">
                <h4 style="margin:0 0 6px;color:{color };">{city_ar }</h4>
                <hr style="border-color:rgba(255,255,255,0.1);margin:6px 0;">
                <p style="margin:3px 0"><b>درجة النشاط:</b> {score :.1f}/100</p>
                <p style="margin:3px 0"><b>التصنيف:</b> {label .replace ("_"," ")}</p>
            </div>
            """
            folium .CircleMarker (
            location =[lat ,lon ],
            radius =max (6 ,score /5 ),
            popup =folium .Popup (popup_html ,max_width =240 ),
            tooltip =f"{city_ar } — {score :.0f}",
            color =color ,fill =True ,fill_color =color ,fill_opacity =0.75 ,weight =2 ,
            ).add_to (m )

        try :
            st_folium (m ,width =None ,height =520 ,use_container_width =True )
        except TypeError :
            st_folium (m ,width =700 ,height =520 )

    except ImportError :
        st .warning ("مكتبة folium غير متوفرة — يُعرض جدول البيانات بدلاً منها")

    st .markdown ("""
    <p style="font-size:1rem;font-weight:700;color:#94a3b8;letter-spacing:.06em;margin:20px 0 10px;">
        تفاصيل المدن
    </p>
    """,unsafe_allow_html =True )

    display_cols =[c for c in ["city_ar","city","activity_score","cluster_label"]if c in df .columns ]
    if display_cols :
        display_df =df [display_cols ].copy ().rename (columns ={
        "city_ar":"المدينة","city":"City",
        "activity_score":"درجة النشاط","cluster_label":"التصنيف",
        })
        st .dataframe (display_df ,use_container_width =True ,hide_index =True )
