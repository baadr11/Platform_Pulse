import os 
import pandas as pd 
import numpy as np 
import plotly .graph_objects as go 
import plotly .express as px 
import streamlit as st 

_DARK =dict (
paper_bgcolor ="rgba(0,0,0,0)",
plot_bgcolor ="rgba(15,23,42,0.35)",
font =dict (family ="Tajawal, Arial",size =13 ,color ="#cbd5e1"),
xaxis =dict (gridcolor ="rgba(255,255,255,0.05)",linecolor ="rgba(255,255,255,0.08)",color ="#64748b"),
yaxis =dict (gridcolor ="rgba(255,255,255,0.05)",linecolor ="rgba(255,255,255,0.08)",color ="#64748b"),
legend =dict (
orientation ="h",yanchor ="bottom",y =1.02 ,xanchor ="right",x =1 ,
bgcolor ="rgba(0,0,0,0.25)",bordercolor ="rgba(255,255,255,0.08)",borderwidth =1 ,
font =dict (color ="#94a3b8"),
),
margin =dict (l =40 ,r =40 ,t =56 ,b =40 ),
hoverlabel =dict (bgcolor ="#0d1526",bordercolor ="rgba(255,255,255,0.12)",font_color ="#e2e8f0"),
)

SECTOR_COLORS ={
"نقل":"#4f8ef7",
"توصيل":"#00c896",
"عمل_حر":"#a78bfa",
"عمل حر":"#a78bfa",
}

@st .cache_data (ttl =3600 )
def _load_sector_data (path :str )->"pd.DataFrame | None":
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
    if filters .get ("sector")and filters ["sector"]!="الكل"and "sector"in df .columns :
        sec =filters ["sector"].replace (" ","_")
        mask =df ["sector"].astype (str ).str .contains (sec ,na =False )|df ["sector"].astype (str ).str .contains (filters ["sector"],na =False )
        if mask .any ():
            df =df [mask ]
    if filters .get ("city")and filters ["city"]!="الكل"and "city"in df .columns :
        city_val =filters ["city"]
        mask =df ["city"].astype (str ).str .contains (city_val ,na =False )
        if "city_ar"in df .columns :
            mask =mask |df ["city_ar"].astype (str ).str .contains (city_val ,na =False )
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

def render_sector_breakdown (filters =None ):
    reviews_path =None 
    for path in [
    os .path .join ("data","processed","reviews_normalized.csv"),
    os .path .join ("data","processed","reviews_cleaned.csv"),
    os .path .join ("data","sample","sample_reviews.csv"),
    ]:
        if os .path .exists (path ):
            reviews_path =path 
            break 

    if reviews_path :
        try :
            df =pd .read_csv (reviews_path ,encoding ="utf-8-sig")
        except UnicodeDecodeError :
            df =pd .read_csv (reviews_path ,encoding ="utf-8")
    else :
        df =pd .DataFrame ({
        "app_name":(["Uber"]*5 +["Careem"]*5 +["HungerStation"]*5 +
        ["Jahez"]*5 +["Mrsool"]*5 +["Sary"]*3 +["Nana"]*3 ),
        "sector":(["نقل"]*10 +["توصيل"]*15 +["عمل_حر"]*6 ),
        "rating":np .random .uniform (1 ,5 ,31 ),
        "date":pd .date_range ("2025-04-01",periods =31 ,freq ="D"),
        })

    if "sector"not in df .columns :
        st .warning ("عمود القطاع غير موجود في البيانات")
        return 

    df =_apply_filters (df ,filters )

    if df .empty :
        st .info ("لا توجد بيانات مطابقة للفلاتر المحددة")
        return 

    sector_counts =df ["sector"].value_counts ().reset_index ()
    sector_counts .columns =["sector","count"]

    if "rating"in df .columns :
        sector_avg =df .groupby ("sector")["rating"].mean ().reset_index ()
        sector_avg .columns =["sector","avg_rating"]
    else :
        sector_avg =pd .DataFrame ({"sector":sector_counts ["sector"],
        "avg_rating":[0 ]*len (sector_counts )})

    stats =sector_counts .merge (sector_avg ,on ="sector",how ="left")

    cols =st .columns (max (len (stats ),1 ))
    kpi_style ="border-radius:14px; padding:20px 16px; direction:rtl; color:white; border:1px solid rgba(255,255,255,0.07); margin-bottom:4px;"
    for i ,(_ ,row )in enumerate (stats .iterrows ()):
        color =SECTOR_COLORS .get (row ["sector"],"#64748b")
        with cols [i ]:
            st .markdown (
            f'<div style="background:linear-gradient(135deg,{color }22,{color }11);'
            f'border:1px solid {color }33;{kpi_style }">'
            f'<p style="margin:0;font-size:.78rem;color:{color };font-weight:700">{row ["sector"]}</p>'
            f'<h2 style="margin:8px 0 4px;font-size:2.1rem;font-weight:800;color:#f1f5f9">'
            f'{int (row ["count"]):,}</h2>'
            f'<p style="margin:0;font-size:.75rem;color:#64748b">متوسط ⭐ {row .get ("avg_rating",0 ):.1f}</p>'
            f'</div>',unsafe_allow_html =True )

    st .markdown ("<br>",unsafe_allow_html =True )

    col1 ,col2 =st .columns (2 )
    with col1 :
        fig_bar =go .Figure ()
        for _ ,row in stats .iterrows ():
            color =SECTOR_COLORS .get (row ["sector"],"#64748b")
            fig_bar .add_trace (go .Bar (
            x =[row ["sector"]],y =[row ["count"]],name =row ["sector"],
            marker_color =color ,marker_line_color ="rgba(0,0,0,0.3)",marker_line_width =1 ,
            text =[f'{int (row ["count"]):,}'],textposition ="outside",
            textfont =dict (color ="#94a3b8",size =12 ),
            ))
        fig_bar .update_layout (
        title =dict (text ="عدد التقييمات حسب القطاع",font =dict (size =16 ,color ="#f1f5f9")),
        xaxis_title ="القطاع",yaxis_title ="عدد التقييمات",
        showlegend =False ,height =380 ,**_DARK ,
        )
        st .plotly_chart (fig_bar ,use_container_width =True )

    with col2 :
        fig_rating =go .Figure ()
        for _ ,row in stats .iterrows ():
            color =SECTOR_COLORS .get (row ["sector"],"#64748b")
            val =row .get ("avg_rating",0 )
            fig_rating .add_trace (go .Bar (
            x =[row ["sector"]],y =[val ],name =row ["sector"],
            marker_color =color ,marker_line_color ="rgba(0,0,0,0.3)",marker_line_width =1 ,
            text =[f"{val :.2f}"],textposition ="outside",
            textfont =dict (color ="#94a3b8",size =12 ),
            ))
        fig_rating .update_layout (
        title =dict (text ="متوسط التقييم حسب القطاع",font =dict (size =16 ,color ="#f1f5f9")),
        xaxis_title ="القطاع",yaxis_title ="متوسط التقييم",
        yaxis_range =[0 ,5.5 ],showlegend =False ,height =380 ,**_DARK ,
        )
        st .plotly_chart (fig_rating ,use_container_width =True )

    if "app_name"in df .columns :
        app_stats =df .groupby (["sector","app_name"]).size ().reset_index (name ="count")
        fig_app =px .treemap (
        app_stats ,path =["sector","app_name"],values ="count",
        color ="sector",color_discrete_map =SECTOR_COLORS ,
        title ="توزيع التقييمات حسب التطبيق والقطاع",
        )
        fig_app .update_traces (
        textfont =dict (family ="Tajawal, Arial",size =14 ),
        marker =dict (line =dict (color ="rgba(0,0,0,0.4)",width =2 )),
        )
        fig_app .update_layout (
        paper_bgcolor ="rgba(0,0,0,0)",
        font =dict (family ="Tajawal, Arial",size =14 ,color ="#cbd5e1"),
        title_font =dict (size =16 ,color ="#f1f5f9"),
        height =380 ,margin =dict (l =20 ,r =20 ,t =56 ,b =20 ),
        )
        st .plotly_chart (fig_app ,use_container_width =True )
