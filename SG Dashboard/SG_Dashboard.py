import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from constant_values import APP_NAMES, URL_ALERTS, URL_INCIDENTS, URL_DATA, URL_CHANGES

# Constants
DATE_FORMAT = "%Y-%m-%d"
DEFAULT_COLUMNS = {
    "data": ["DateTime", "App Name", "Severity", "Alert Type", "Message", "URL"],
    "incidents": ["App Name", "Id", "Creation Date", "Short Description", "Priority", "Status"],
    "alerts": ["Id", "App Name", "Display Label", "Ems Creation Date", "Priority"],
    "changes": [
        "Display Label",
        "Scheduled Start Time",
        "Scheduled End Time",
        "Register for actual service",
        "Impacted Core Business 0",
        "Phase Id",
        "Service Desk Group",
        "Ticket Link",
        "Date Occurred"
    ]
}

st.set_page_config(layout="wide")


def load_css(file_name: str) -> None:
    """Load and apply CSS styles from a file."""
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def fetch_data(url: str) -> dict:
    """Fetch JSON data from a given API endpoint."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, requests.HTTPError) as e:
        st.error(f"Error fetching data from {url}: {str(e)}")
        return None


def create_empty_table(columns: list) -> str:
    """Generate HTML for an empty table with given columns."""
    return (
        f'<table><thead><tr>{"".join([f"<th>{col}</th>" for col in columns])}</tr></thead>'
        f'<tbody><tr><td colspan="{len(columns)}" style="text-align:center;">No Rows to Show</td></tr></tbody></table>'
    )


def extract_first_value(value) -> str:
    """Extract the first value from a list if the input is a list."""
    return value[0] if isinstance(value, list) and len(value) > 0 else value


def render_table_html(dataframe: pd.DataFrame) -> None:
    """Render a DataFrame as an HTML table with proper styling."""
    if dataframe.empty:
        st.markdown(
            f'<div class="dataframe-container">{create_empty_table(dataframe.columns)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="dataframe-container">{dataframe.to_html(escape=False, index=False)}</div>',
            unsafe_allow_html=True,
        )


def render_table_section(title: str, dataframe: pd.DataFrame, table_key: str) -> bool:
    """
    Render a table section with fullscreen capability.
    Returns True if in fullscreen mode for this table, False otherwise.
    """
    active = st.session_state.get("active_fullscreen")
    
    if active == table_key:
        # Fullscreen mode
        st.markdown(f"## {title}")
        if st.button("Exit Full Screen", key=f"exit_{table_key}"):
            st.session_state["active_fullscreen"] = None
            st.rerun()

        # Hide all other elements
        st.markdown(
            """
            <style>
                div[data-testid="stSidebar"] {display: none !important;}
                .element-container:not(:has(button:contains('Exit Full Screen'))) {display: none !important;}
                div.block-container {padding: 0; margin: 0; max-width: 100% !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )

        render_table_html(dataframe)
        return True

    elif active is not None:
        # Another table is in fullscreen mode
        return False

    # Normal mode
    st.markdown(f"## {title}")
    if st.button("Full Screen", key=f"full_{table_key}"):
        st.session_state["active_fullscreen"] = table_key
        st.rerun()
    render_table_html(dataframe)
    return False


def preprocess_alert_data() -> pd.DataFrame:
    """Fetch and preprocess alert data from Elastic."""
    raw_data = fetch_data(URL_DATA)
    
    dataframe = (
        pd.DataFrame(raw_data)
        if raw_data
        else pd.DataFrame(columns=DEFAULT_COLUMNS["data"])
    )

    # Rename columns
    dataframe.rename(
        columns={
            "@timestamp": "DateTime",
            "app_name": "App Name",
            "severity": "Severity",
            "alert_type": "Alert Type",
            "message": "Message",
            "url": "URL",
        },
        inplace=True,
    )

    # Convert URLs to clickable links
    if "URL" in dataframe.columns:
        dataframe["URL"] = dataframe["URL"].apply(
            lambda x: f'<a href="{x}" target="_blank">{x}</a>' if pd.notnull(x) else ""
        )

    return dataframe


def preprocess_incident_data() -> pd.DataFrame:
    """Fetch and preprocess incident data."""
    raw_data = fetch_data(URL_INCIDENTS)
    
    dataframe = (
        pd.DataFrame(raw_data)
        if raw_data
        else pd.DataFrame(columns=DEFAULT_COLUMNS["incidents"])
    )

    dataframe.rename(
        columns={
            "app_name": "App Name",
            "EmsCreationDate": "Creation Date",
            "DisplayLabel": "Short Description",
        },
        inplace=True,
    )

    return dataframe


def preprocess_unity_alert_data() -> pd.DataFrame:
    """Fetch and preprocess Unity alert data."""
    raw_data = fetch_data(URL_ALERTS)
    
    dataframe = (
        pd.DataFrame(raw_data)
        if raw_data
        else pd.DataFrame(columns=DEFAULT_COLUMNS["alerts"])
    )

    dataframe.rename(
        columns={
            "app_name": "App Name",
            "EmsCreationDate": "Ems Creation Date",
            "DisplayLabel": "Display Label",
        },
        inplace=True,
    )

    return dataframe


def preprocess_change_data() -> pd.DataFrame:
    """Fetch and preprocess change management data."""
    raw_data = fetch_data(URL_CHANGES)
    
    dataframe = (
        pd.DataFrame(raw_data)
        if raw_data
        else pd.DataFrame(columns=DEFAULT_COLUMNS["changes"])
    )

    dataframe.rename(
        columns={
            "DisplayLabel": "Display Label",
            "ScheduledStartTime": "Scheduled Start Time",
            "ScheduledEndTime": "Scheduled End Time",
            "RegisterForActualService": "Register for actual service",
            "ImpactedCoreBusiness": "Impacted Core Business 0",
            "PhaseId": "Phase Id",
            "ServiceDeskGroup": "Service Desk Group",
            "TicketLink": "Ticket Link",
            "date_occured": "Date Occurred",
        },
        inplace=True,
    )

    # Convert ticket links to clickable URLs
    if "Ticket Link" in dataframe.columns:
        dataframe["Ticket Link"] = dataframe["Ticket Link"].apply(
            lambda x: f'<a href="{x}" target="_blank">{x}</a>' if pd.notnull(x) else ""
        )

    return dataframe


def create_alert_count_chart(dataframe: pd.DataFrame) -> px.bar:
    """Create a bar chart showing alert counts by application."""
    app_counts = dataframe["App Name"].value_counts().reset_index()
    app_counts.columns = ["App Name", "Count"]
    
    fig = px.bar(
        app_counts,
        x="App Name",
        y="Count",
        title="Application Alert Count",
        color="App Name",
    )
    
    return fig


def apply_data_filters(
    alert_data: pd.DataFrame,
    incident_data: pd.DataFrame,
    unity_alert_data: pd.DataFrame,
    app_filter: str,
    date_range: tuple
) -> tuple:
    """Apply filters to all datasets based on application and date range."""
    if app_filter != "All":
        if not alert_data.empty:
            alert_data = alert_data[alert_data["App Name"] == app_filter]
        if not unity_alert_data.empty:
            unity_alert_data = unity_alert_data[unity_alert_data["App Name"] == app_filter]
        if not incident_data.empty:
            incident_data = incident_data[incident_data["App Name"] == app_filter]

    if len(date_range) == 2:
        start_date, end_date = date_range
        date_columns = {
            "alert_data": "date_occured",
            "unity_alert_data": "date_occured",
            "incident_data": "date_occured"
        }

        for df_name, date_col in date_columns.items():
            df = locals()[df_name]
            if not df.empty and date_col in df.columns:
                mask = (
                    (pd.to_datetime(df[date_col]) >= pd.to_datetime(start_date)) & 
                    (pd.to_datetime(df[date_col]) <= pd.to_datetime(end_date)
                )
                locals()[df_name] = df[mask]

    return alert_data, incident_data, unity_alert_data


def filter_changes_by_business_impact(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Filter changes data to show only GCOO/DDS impacted items if checkbox is selected."""
    dataframe["Impacted Core Business 0"] = dataframe["Impacted Core Business 0"].apply(
        extract_first_value
    )
    
    if st.checkbox("Show rows with Impacted Core Business - GCOO/DDS"):
        dataframe = dataframe[
            dataframe["Impacted Core Business 0"].str.contains("GCOO/DDS", na=False)
        ]
    
    return dataframe


def render_main_content(
    alert_data: pd.DataFrame,
    incident_data: pd.DataFrame,
    unity_alert_data: pd.DataFrame,
    change_data: pd.DataFrame
) -> None:
    """Render the main dashboard content."""
    # Create chart
    chart = create_alert_count_chart(alert_data)

    # Layout
    left_column, right_column = st.columns([1, 1])
    
    with left_column:
        st.markdown("## Application Alert Count")
        st.plotly_chart(chart, use_container_width=True)
        render_table_section("Application Alert - Elastic", alert_data, "elastic")

    with right_column:
        render_table_section("Incidents - Ongoing Incidents", incident_data, "incidents")
        render_table_section("Application Alerts - Unity", unity_alert_data, "alerts")

    # Filter and render changes table
    change_data = filter_changes_by_business_impact(change_data)
    render_table_section("Planned Changes on Infra", change_data, "changes")


def render_fullscreen_content(
    alert_data: pd.DataFrame,
    incident_data: pd.DataFrame,
    unity_alert_data: pd.DataFrame,
    change_data: pd.DataFrame
) -> None:
    """Render content when in fullscreen mode for a specific table."""
    active_table = st.session_state["active_fullscreen"]
    
    if active_table == "elastic":
        render_table_section("Application Alert - Elastic", alert_data, "elastic")
    elif active_table == "incidents":
        render_table_section("Incidents - Ongoing Incidents", incident_data, "incidents")
    elif active_table == "alerts":
        render_table_section("Application Alerts - Unity", unity_alert_data, "alerts")
    elif active_table == "changes":
        render_table_section("Planned Changes on Infra", change_data, "changes")


def main() -> None:
    """Main application function."""
    # Load CSS and initialize session state
    load_css("dashboard_styles.css")
    
    if "active_fullscreen" not in st.session_state:
        st.session_state["active_fullscreen"] = None

    # Load and preprocess all data
    alert_data = preprocess_alert_data()
    unity_alert_data = preprocess_unity_alert_data()
    incident_data = preprocess_incident_data()
    change_data = preprocess_change_data()

    if st.session_state["active_fullscreen"] is None:
        # Normal view with sidebar filters
        st.sidebar.header("Board Filters")
        selected_app = st.sidebar.selectbox("Select App Name", APP_NAMES)
        selected_date_range = st.sidebar.date_input("Select Date Range", [])

        # Apply filters
        alert_data, incident_data, unity_alert_data = apply_data_filters(
            alert_data,
            incident_data,
            unity_alert_data,
            selected_app,
            selected_date_range
        )

        # Select only required columns
        alert_data = alert_data[DEFAULT_COLUMNS["data"]]
        incident_data = incident_data[DEFAULT_COLUMNS["incidents"]]
        unity_alert_data = unity_alert_data[DEFAULT_COLUMNS["alerts"]]
        change_data = change_data[DEFAULT_COLUMNS["changes"]]

        render_main_content(alert_data, incident_data, unity_alert_data, change_data)
    else:
        # Fullscreen view for a specific table
        render_fullscreen_content(alert_data, incident_data, unity_alert_data, change_data)


if __name__ == "__main__":
    main()