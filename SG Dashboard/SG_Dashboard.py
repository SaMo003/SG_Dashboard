import streamlit as st
import requests as req
import pandas as pd
import plotly.express as px
from constant_values import App_Names,url_alerts,url_incidents,url_data,url_changes

st.set_page_config(layout="wide")

#loading the CSS file
def load_css(fileName):
    with open(fileName) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

#Fetching Data from APIs
def fetch_data(url):
    try:
        response = req.get(url)
        response.raise_for_status()
        return response.json()
    except (req.RequestException, req.HTTPError):
        return None
    
#Create table spanning the column names to display "No Rows to Show" when table has no data
def create_empty_table(columns):
    return f'<table><thead><tr>{"".join([f"<th>{col}</th>" for col in columns])}</tr></thead><tbody><tr><td colspan="{len(columns)}" style="text-align:center;">No Rows to Show</td></tr></tbody></table>'

#Function to extract first value from the list in the 'Impacted Core Business 0' column from the df_changes table
def extract_first_value(value):
    if isinstance(value, list) and len(value) > 0:
        return value[0]
    return value   

#Renders Tables
# def render_table_html(df):
#     if df.empty:
#         st.markdown(
#             f'<div class="dataframe-container">{create_empty_table(df.columns)}</div>', unsafe_allow_html=True,
#         )
#     else:
#         st.markdown(
#             f'<div class="dataframe-container">{df.to_html(escape=False,index=False)}</div>',unsafe_allow_html=True
#         )

def render_table_html(df, fullscreen=False):
    if df.empty:
        container_class = "no-data-fullscreen" if fullscreen else "dataframe-container"
        st.markdown(
            f'<div class="{container_class}">{create_empty_table(df.columns)}</div>', 
            unsafe_allow_html=True,
        )
    else:
        container_class = "fullscreen-table-container" if fullscreen else "dataframe-container"
        table_html = df.to_html(escape=False, index=False)
        
        # Calculate approximate required height (50px per row + 100px for headers)
        row_count = len(df)
        dynamic_height = min(50 * row_count + 100, 1000)  # Cap at 1000px
        
        style = f"max-height: {dynamic_height}px;" if row_count <= 15 else ""
        
        st.markdown(
            f'<div class="{container_class}" style="{style}">{table_html}</div>',
            unsafe_allow_html=True
)  
        
def render_table_section(title,df,table_key):
    active=st.session_state['active_fullscreen']

    if active == table_key:
        st.markdown(f"## {title}")

        if st.button("Exit Full Screen",key=f"exit_{table_key}"):
            st.session_state['active_fullscreen'] = None
            st.rerun()
        st.markdown("""
        <style>
            div[data-testid="stSidebar"]{display: none !important;}
            .element-container:not(:has(button:contains('Exit Full Screen'))){display:none !important;}
            div.block-container{padding:0; margin:0; max-width:100% !important}
            html, body, #root, .block-container {height: 100% !important;}
        </style>
        """,unsafe_allow_html=True)
        
        render_table_html(df)
        return True

    elif active is not None:
        return False

    st.markdown(f'## {title}')
    if st.button("Full Screen",key=f"full_{table_key}"):
        st.session_state['active_fullscreen'] = table_key
        st.rerun()
    render_table_html(df)

    return False

#Table preprocessing
def df_data_preprocess(url_data):
    #Fetch data (fetches json data)
    data_data = fetch_data(url_data)

    #Convert to data frame
    df_data = pd.DataFrame(data_data) if data_data else pd.DataFrame(columns=['DataTime','App Name', 'Severity','Alert Type','Message','URL'])

    # Rename and select columns for df_data
    df_data.rename(columns={
    '@timestamp': 'DateTime',
    'app_name': 'App Name',
    'severity': 'Severity',
    'alert_type': 'Alert Type',
    'message': 'Message',
    'url': 'URL'
    }, inplace=True)

    #Convert data in URL column to clickable links
    if "URL" in df_data.columns:
        df_data["URL"] = df_data["URL"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
   
    return df_data

def df_incidents_preprocess(url_incidents):
    #Fetch data (fetches json data)
    data_incidents = fetch_data(url_incidents)

    #Convert to data frame
    df_incidents = pd.DataFrame(data_incidents) if data_incidents else pd.DataFrame(columns=['App Name','Id','Creation Date','Short Description','Priority','Status'])

    # Rename and select columns for df_incidents
    df_incidents.rename(columns={
    'app_name': 'App Name',
    'EmsCreationDate': 'Creation Date',
    'DisplayLabel': 'Short Description'
    }, inplace=True)

    return df_incidents

def df_alerts_preprocess(url_alerts):
    #Fetch data (fetches json data)
    data_alerts = fetch_data(url_alerts)

    #Convert to data frame
    df_alerts = pd.DataFrame(data_alerts) if data_alerts else pd.DataFrame(columns=['Id','App Name','Display Label','Ems Creation Date','Priority'])

    # Rename and select columns for df_alerts
    df_alerts.rename(columns={
    'app_name': 'App Name', 
    'EmsCreationDate': 'Ems Creation Date',
    'DisplayLabel': 'Display Label' }, inplace=True)

    return df_alerts

def df_changes_preprocess(url_changes):
    #Fetch data (fetches json data)
    data_changes = fetch_data(url_changes)

    #Convert to data frame
    df_changes = pd.DataFrame(data_changes) if data_changes else pd.DataFrame(columns=['Display Label','Scheduled Start Time','Scheduled End Time','Register for actual service','Impacted Core Business 0','Phase Id','Service Desk Group','Ticket Link','Date Occurred'])

    # Rename and select columns for df_changes
    df_changes.rename(columns={
    'DisplayLabel': 'Display Label',
    'ScheduledStartTime': 'Scheduled Start Time',
    'ScheduledEndTime': 'Scheduled End Time',
    'RegisterForActualService':'Register for actual service',
    'ImpactedCoreBusiness': 'Impacted Core Business 0',
    'PhaseId': 'Phase Id', 
    'ServiceDeskGroup': 'Service Desk Group', 
    'TicketLink': 'Ticket Link', 
    'date_occured': 'Date Occurred'}, inplace=True)

    #Convert data in "Ticket Link" column to clickable links
    if "Ticket Link" in df_changes.columns:
        df_changes["Ticket Link"] = df_changes["Ticket Link"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    return df_changes

#Application Alert Count Graph
def bar_graph(df_data):
    #Bar Chart
    app_counts = df_data["App Name"].value_counts().reset_index()
    app_counts.columns = ["App Name","Count"]
    fig = px.bar(app_counts, x="App Name", y="Count", title="Application Alert - Count", color="App Name")

    return fig

#Side bar App name and date filters
def apply_filters(df_data,df_incidents,df_alerts,app_name_filter,date_range_filter):
        #Apply Filter
    if app_name_filter != "All":
        if not df_data.empty:
            df_data = df_data[df_data['App Name'] == app_name_filter]
        if not df_alerts.empty:
            df_alerts = df_alerts[df_alerts['App Name'] == app_name_filter]
        if not df_incidents.empty:
            df_incidents = df_incidents[df_incidents['App Name'] == app_name_filter]
    
    if len(date_range_filter)!= 0:
        start_date,end_date = date_range_filter
        if not df_data.empty:
            df_data = df_data[(pd.to_datetime(df_data['date_occured']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df_data['date_occured']) <= pd.to_datetime(end_date))]

        if not df_alerts.empty:
            df_alerts = df_alerts[(pd.to_datetime(df_alerts['date_occured']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df_alerts['date_occured']) <= pd.to_datetime(end_date))]
        
        if not df_incidents.empty:
            df_incidents = df_incidents[(pd.to_datetime(df_incidents['date_occured']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df_incidents['date_occured']) <= pd.to_datetime(end_date))]

    return df_data,df_incidents,df_alerts

#Select only the required columns in the required order
def reorder_columns(df_data,df_incidents,df_alerts,df_changes):
    df_data = df_data.loc[:, ['DateTime', 'App Name', 'Severity', 'Alert Type', 'Message', 'URL']]
    df_incidents = df_incidents.loc[:, ['App Name', 'Id', 'Creation Date', 'Short Description', 'Priority', 'Status']]
    df_alerts = df_alerts.loc[:, ['Id', 'App Name', 'Display Label', 'Ems Creation Date', 'Priority']]
    df_changes = df_changes.loc[:, ['Display Label', 'Scheduled Start Time', 'Scheduled End Time', 'Register for actual service', 'Impacted Core Business 0', 'Phase Id', 'Service Desk Group', 'Ticket Link', 'Date Occurred']]

    return df_data,df_incidents,df_alerts,df_changes

#df_changes table filter to display records including GCOO/DDS
def df_changes_filter(df_changes):
    #Apply the function to the 'Impacted core business 0' column
    df_changes['Impacted Core Business 0'] = df_changes['Impacted Core Business 0'].apply(extract_first_value)
    core_business_filter=st.checkbox("Show rows with Impacted Core Business - GCOO/DDS")
    if core_business_filter:
        df_changes = df_changes[df_changes['Impacted Core Business 0'].str.contains("GCOO/DDS")]

    return df_changes    

def main():
    
    load_css('dashboard_styles.css')

    df_data=df_data_preprocess(url_data)
    df_alerts=df_alerts_preprocess(url_alerts)
    df_incidents=df_incidents_preprocess(url_incidents)
    df_changes=df_changes_preprocess(url_changes)

    #full screen code start
    if 'active_fullscreen' not in st.session_state:
        st.session_state['active_fullscreen'] = None

    if st.session_state['active_fullscreen'] is None:
        #sidebar filters
        st.sidebar.header("Board Filters")
        app_name_filter = st.sidebar.selectbox("Select App Name", App_Names)
        date_range_filter = st.sidebar.date_input("Select Date Range",[])

        #Applying filters
        df_data,df_incidents,df_alerts = apply_filters(df_data,df_incidents,df_alerts,app_name_filter,date_range_filter)

        #Reordering the columns
        df_data,df_incidents,df_alerts,df_changes = reorder_columns(df_data,df_incidents,df_alerts,df_changes)

    if st.session_state['active_fullscreen'] is None:
        #Graph
        fig=bar_graph(fig)

        #Layout
        left_half , right_half =st.columns([1,1])
        with left_half:
            st.markdown("## Application Alert Count")
            st.plotly_chart(fig,use_container_width=True)
            render_table_section("Application Alert -Elastic",df_data,"elastic")

        with right_half:
            render_table_section("Incidents - Ongoing Incidents",df_incidents,"incidents")
            render_table_section("Application Alerts - Unity",df_alerts,"alerts")

        df_changes=df_changes_filter(df_changes)
        render_table_section("Planned Changes on Infra",df_changes,"changes")

    else:
        #Reordering the columns
        df_data,df_incidents,df_alerts,df_changes = reorder_columns(df_data,df_incidents,df_alerts,df_changes)

        #Graph
        fig=bar_graph(fig)

        if st.session_state["active_fullscreen"]=="elastic":
            render_table_section("Application Alert -Elastic",df_data,"elastic")
        elif st.session_state["active_fullscreen"]=="incidents":
            render_table_section("Incidents - Ongoing Incidents",df_incidents,"incidents")
        elif st.session_state["active_fullscreen"]=="alerts":
            render_table_section("Application Alerts - Unity",df_alerts,"alerts")
        elif st.session_state["active_fullscreen"]=="changes":
            render_table_section("Planned Changes on Infra",df_changes,"changes")

if __name__=="__main__":
    main()