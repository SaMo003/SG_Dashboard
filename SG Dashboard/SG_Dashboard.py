import streamlit as st
import requests as req
import pandas as pd
import plotly.express as px
from constant_valus import App_Names,url_alerts,url_incidents,url_data,url_changes

st.set_page_config(layout="wide")

#loading the CSS file

def load_css(fileName):
    with open(fileName) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css('SG_Dashboard_Style.css')

def fetch_data(url):
    try:
        response = req.get(url)
        response.raise_for_status()
        return response.json()
    except (req.RequestException, req.HTTPError):
        return None
    
data_data = fetch_data(url_data)
data_alerts = fetch_data(url_alerts)
data_incidents = fetch_data(url_incidents)
data_changes = fetch_data(url_changes)

df_data = pd.DataFrame(data_data) if data_data else pd.DataFrame(columns=['DataTime','App Name', 'Severity','Alert Type','Message','URL'])
df_alerts = pd.DataFrame(data_alerts) if data_alerts else pd.DataFrame(columns=['Id','App Name','Display Label','Ems Creation Date','Priority'])
df_incidents = pd.DataFrame(data_incidents) if data_incidents else pd.DataFrame(columns=['App Name','Id','Creation Date','Short Description','Priority','Status'])
df_changes = pd.DataFrame(data_changes) if data_changes else pd.DataFrame(columns=['Display Label','Scheduled Start Time','Scheduled End Time','Register for actual service','Impacted Core Business 0','Phase Id','Service Desk Group','Ticket Link','Date Occurred'])

if df_incident.empty:
    df_incident = pd.DataFrame(columns=['App Name','Id','Creation Date','Short Description','Priority','Status'])
if df_alerts.empty:
    df_alerts = pd.DataFrame(columns=['Id','App Name','Display Label','Ems Creation Date','Priority'])

def create_empty_table(columns):
    return f'<table><thead><tr>{"".join([f"<th>{col}</th>" for col in columns])}</tr></thead><tbody><tr><td colspan="{len(columns)}" style="text-align:center;">No Rows to Show</td></tr></tbody></table>'

#Function to extract first value from the list in the 'Impacted Core Business 0' column
def extract_first_value(value):
    if isinstance(value, list) and len(value) > 0:
        return value[0]
    return value

def render_table_section(title,df,table_key):
    active=st.session_state['active_fullscreen']

    if active == table_key:
        st.markdown(f"## {title}")

        if st.button("Exit Full Screen",key=f"exit_{table_key}"):
            st.session_state['active_fullscreen'] = None

        st.markdown(
            '<style>div.block-container{padding:0; margin:0; max-width:100% !important}</style>',unsafe_allow_html=True
        )

        if df.empty:
            st.markdown(
                f'<div class="dataframe-container">{create_empty_table(df.columns)}</div>', unsafe_allow_html=True,
            )
        else:
            st.Markdown(
                f'<div class="dataframe-container">{df.to_html(escape=False,index=False)}</div>',unsafe_allow_html=True
            )
        return True

    elif active is not None:
        return False

    st.Markdown(f'## {title}')
    if st.button("Full Screen",key=f"full_{table_key}"):
        st.session_state['active_fullscreen'] = table_key

    if df.empty:
        st.markdown(
            f'<div class="dataframe-container">{create_empty_table(df.columns)}</div>', unsafe_allow_html=True)
    else:
        st.Markdown(
            f'<div class="dataframe-container">{df.to_html(escape=False,index=False)}</div>',unsafe_allow_html=True )

    return False

# Rename and select columns for df_data
df_data.rename(columns={
  '@timestamp': 'DateTime',
  'app_name': 'App Name',
  'severity': 'Severity',
  'alert_type': 'Alert Type',
  'message': 'Message',
  'url': 'URL'
}, inplace=True)

# Rename and select columns for df_incident
df_incident.rename(columns={
  'app_name': 'App Name',
  'EmsCreationDate': 'Creation Date',
  'DisplayLabel': 'Short Description'
}, inplace=True)

# Rename and select columns for df_alerts
df_alerts.rename(columns={
  'app_name': 'App Name', 
  'EmsCreationDate': 'Ems Creation Date',
  'DisplayLabel': 'Display Label' }, inplace=True)



df_changes.rename(columns={
  'DisplayLabel': 'Display Label',
  'ScheduledStartTime': 'Scheduled Start Time',
  'ScheduledEndTime': 'Scheduled End Time',
  'RegisterForActualService':'Register for actual service',
  'ImpactedCoreBusiness': 'Impacted Core Business 0',
  'PhaseId': 'Phase Id', 
  'ServiceDeskGroup': 'Service Desk Group', 
  'TicketLink': 'Ticket Link', 
  'date_occurred': 'Date Occurred'}, inplace=True)

#full screen code starts
if 'active_fullscreen' not in st.session_state:
    st.session_state['active_fullscreen'] = None

if st.session_state['active_fullscreen'] is None:
    #sidebar filters
    st.sidebar.header("Board Filters")
    app_name_filter = st.header.selectbox("Select App Name", App_Names)
    date_range_filter = st.header.date_input("Select Date Range",[])

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
            df_data = df_data[(pd.to_datetime((df_data['date_occured']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df_data['date_occured']) <= pd.to_date_time(end_date))]

        if not df_alerts.empty:
            df_alerts = df_alerts[(pd.to_datetime((df_alerts['date_occured']) >= pd.to_datetime(start_date)) & (pd.to_datetime(df_alerts['date_occured']) <= pd.to_datetime(end_date))]
        
        if not df_incidents.empty:
            df_incidents = df_incidents[(pd.to_datetime((df_incidents['date_occured'] >= pd.to_datetime(start_date)) & (pd.to_datetime(df_alerts['date_occured']) <= pd.to_datetime(end_date))]

    df_data = df_data.loc[:, ['DateTime', 'App Name', 'Severity', 'Alert Type', 'Message', 'URL']]
    df_incident = df_incident.loc[:, ['App Name', 'Id', 'Creation Date', 'Short Description', 'Priority', 'Status']]
    df_alerts = df_alerts, loc[:, ['Id', 'App Name', 'Display Label', 'Ems Creation Date', 'Priority']]
    df_changes = df_changes.loc[:, ['Display Label', 'Scheduled Start Time', 'Scheduled End Time', 'Register for actual service', 'Impacted Core Business 0', 'Phase Id', 'Service Desk Group', 'Ticket Link', 'Date Occurred']]

    if "URL" in df.data.columns:
        df_data["URL"] = df_data["URL"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    if "Ticket Link" in df.data.columns:
        df_changes["Ticket Link"] = df_changes["Ticket Link"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    #Bar Chart
    app_counts = df_data["App Name"].value_counts().reset_index()
    app_counts.columns = ["App Name","Count"]
    fig = px.bar(app_counts, x="App Name", y="Counts", title="Application Alert - Count", color="App Name")

    #Layout
    left_half , right_half =st.columns([1,1])
    with left_half:
        st.markdown("## Application Alert Count")
        st.plotly_chart(fig,use_container_width=True)
        render_table_section("Application Alert -Elastic",df_data,"elastic")

    with right_half:
        render_table_section("Incidents - Ongoing Incidents",df_incidents,"incidents")
        render_table_section("Application Alerts - Unity",df_alerts,"alerts")

    #Apply the function to the 'Impacted core business 0' column
    df_changes['Impacted Core Business 0'] = df_changes['Impacted Core Business 0].apply(extract_first_value)
    core_business_filter=st.checkbox("Show rows with Impacted Core Business - GCOO/DDS")
    if core_business_filter:
        df_changes = df_changes[df_changes['Impacted Core Business 0'].str.contains("GCOO/DDS")
    render_table_section("Planned Changes on Infra",df_changes,"changes")

else:
    df_data = df_data.loc[:, ['DateTime', 'App Name', 'Severity', 'Alert Type', 'Message', 'URL']]
    df_incident = df_incident.loc[:, ['App Name', 'Id', 'Creation Date', 'Short Description', 'Priority', 'Status']]
    df_alerts = df_alerts, loc[:, ['Id', 'App Name', 'Display Label', 'Ems Creation Date', 'Priority']]
    df_changes = df_changes.loc[:, ['Display Label', 'Scheduled Start Time', 'Scheduled End Time', 'Register for actual service', 'Impacted Core Business 0', 'Phase Id', 'Service Desk Group', 'Ticket Link', 'Date Occurred']] 


    if "URL" in df.data.columns:
        df_data["URL"] = df_data["URL"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    if "Ticket Link" in df.data.columns:
        df_changes["Ticket Link"] = df_changes["Ticket Link"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

    #Bar Chart
    app_counts = df_data["App Name"].value_counts().reset_index()
    app_counts.columns = ["App Name","Count"]
    fig = px.bar(app_counts, x="App Name", y="Counts", title="Application Alert - Count", color="App Name")

    if st.session_state["active_fullscreen"]=="elastic":
        render_table_section("Application Alert -Elastic",df_data,"elastic")
    elif st.session_state["active_fullscreen"]=="incidents":
        render_table_section("Incidents - Ongoing Incidents",df_incident,"incidents")
    elif st.session_state["active_fullscreen"]=="alerts":
        render_table_section("Application Alerts - Unity",df_alerts,"alerts")
    elif st.session_state["active_fullscreen"]=="changes":
        render_table_section("Planned Changes on Infra",df_changes,"changes")


