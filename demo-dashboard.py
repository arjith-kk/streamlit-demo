import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
from PIL import Image
import base64

# ---------------------------------------
# 🔧 PAGE CONFIGURATION
# ---------------------------------------
st.set_page_config(
    page_title="Service Ticket Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------
# 🎨 BACKGROUND IMAGE SETUP
# ---------------------------------------
def set_background(image_path: str):
    """Apply a background image with a dark overlay."""
    with open(image_path, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), 
                        url('data:image/png;base64,{encoded}');
            background-size: cover;
            background-blend-mode: darken;
        }}
        </style>
    """, unsafe_allow_html=True)

set_background('images/bg.png')

# ---------------------------------------
# 🟨 HEADER SECTION
# ---------------------------------------
def header_section():
    logo_bytes = open("images/logo.png", "rb").read()
    logo_base64 = base64.b64encode(logo_bytes).decode()

    header = st.container()
    with header:
        col_btn, col_yellow, col_spacer = st.columns([1, 20, 1])
        with col_btn:
            if st.button("☰", key="hamburger_menu", help="Show/hide filters"):
                st.session_state['show_filters'] = not st.session_state.get('show_filters', False)
        with col_yellow:
            st.markdown(f"""
                <div style='height:72px; width:100%; background-color:#FFD900; display:flex; align-items:center;'>
                    <img src='data:image/png;base64,{logo_base64}' height='56' style='margin-left:0; margin-right:16px;'>
                    <span style='font-size:24px; font-weight:bold; color:#3F58A6; vertical-align:middle;'>
                        Service Ticket Dashboard
                    </span>
                </div>
            """, unsafe_allow_html=True)

header_section()
st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# ---------------------------------------
# 🧭 SESSION STATE INITIALIZATION
# ---------------------------------------
if 'show_filters' not in st.session_state:
    st.session_state['show_filters'] = False

# ---------------------------------------
# 📦 LOAD DATA
# ---------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('service_ticket_details.csv')
    df['CreatedDate'] = pd.to_datetime(df['CreatedDate'])
    df['ClosedDate'] = pd.to_datetime(df['ClosedDate'], errors='coerce')
    return df

df = load_data()

# ---------------------------------------
# 🔍 FILTERS
# ---------------------------------------
if st.session_state.get('show_filters', False):
    with st.sidebar:
        st.title("⚙️ Filters")
        min_date, max_date = df['CreatedDate'].min().date(), df['CreatedDate'].max().date()
        start_date = st.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.date_input("End date", min_value=min_date, max_value=max_date, value=max_date)

        category = st.multiselect('Category', options=df['Category'].unique(), default=df['Category'].unique())
        priority = st.multiselect('Priority', options=df['Priority'].unique(), default=df['Priority'].unique())
        status = st.multiselect('Status', options=df['Status'].unique(), default=df['Status'].unique())
        time_frame = st.selectbox("Time frame", ("Daily", "Monthly", "Quarterly", "Yearly"))
else:
    start_date = df['CreatedDate'].min().date()
    end_date = df['CreatedDate'].max().date()
    category = list(df['Category'].unique())
    priority = list(df['Priority'].unique())
    status = list(df['Status'].unique())
    time_frame = "Monthly"

# ---------------------------------------
# 🧹 FILTER DATA
# ---------------------------------------
filtered_df = df[
    (df['CreatedDate'].dt.date >= start_date) &
    (df['CreatedDate'].dt.date <= end_date) &
    (df['Category'].isin(category)) &
    (df['Priority'].isin(priority)) &
    (df['Status'].isin(status))
]

# ---------------------------------------
# 📊 METRICS CALCULATION
# ---------------------------------------
total_tickets = len(filtered_df)
active_tickets = filtered_df[filtered_df['Status'].isin(['Open', 'In Progress', 'On Hold'])].shape[0]
new_tickets = filtered_df[filtered_df['CreatedDate'] > (datetime.now() - pd.Timedelta(days=30))].shape[0]
closed_tickets = filtered_df[filtered_df['Status'] == 'Closed'].shape[0]
closure_rate = (closed_tickets / total_tickets * 100) if total_tickets > 0 else 0

# ---------------------------------------
# 🎨 CHART CONFIG
# ---------------------------------------
chart_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#fff', family='Arial', size=14),
    title_font=dict(color='#fff', family='Arial', size=18),
    legend=dict(font=dict(color='#fff')),
    xaxis=dict(title_font=dict(color='#fff'), tickfont=dict(color='#fff')),
    yaxis=dict(title_font=dict(color='#fff'), tickfont=dict(color='#fff')),
)
CHART_COLORS = ['#3F58A6', '#97934F', '#C19F62', '#FFD900']
YELLOW_SHADES = ['#FFD900', '#FFE34D', '#FFEB80', '#FFF3B3', '#FFF9CC', '#FFFDE6']

# ---------------------------------------
# 🍩 DONUT CHARTS
# ---------------------------------------
def create_donut(df, column, title):
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, 'Count']
    fig = px.pie(counts, names=column, values='Count', title=title, hole=0.5,
                 color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**chart_layout)
    return fig

category_donut = create_donut(filtered_df, 'Category', 'Tickets by Category')
priority_donut = create_donut(filtered_df, 'Priority', 'Tickets by Priority')
status_donut = create_donut(filtered_df, 'Status', 'Tickets by Status')

# ---------------------------------------
# 📈 TIME SERIES CHARTS
# ---------------------------------------
def group_time(df, freq_label):
    df_time = df.copy()
    if freq_label == "Daily":
        df_time['TimeGroup'] = df_time['CreatedDate'].dt.date
    elif freq_label == "Monthly":
        df_time['TimeGroup'] = df_time['CreatedDate'].dt.to_period('M').dt.strftime('%b %Y')
    elif freq_label == "Quarterly":
        df_time['TimeGroup'] = df_time['CreatedDate'].dt.to_period('Q').astype(str)
    else:
        df_time['TimeGroup'] = df_time['CreatedDate'].dt.year.astype(str)
    return df_time

df_time = group_time(filtered_df, time_frame)
grouped_total = df_time.groupby('TimeGroup').size().reset_index(name='Total Tickets')
grouped_active = df_time[df_time['Status'].isin(['Open', 'In Progress', 'On Hold'])].groupby('TimeGroup').size().reset_index(name='Active Tickets')
grouped_closed = df_time[df_time['Status'] == 'Closed'].groupby('TimeGroup').size().reset_index(name='Closed Tickets')

def create_line_chart(df, y_col, title):
    fig = px.line(df, x='TimeGroup', y=y_col, title=title, markers=True, color_discrete_sequence=YELLOW_SHADES)
    fig.update_layout(**chart_layout)
    return fig

total_line_fig = create_line_chart(grouped_total, 'Total Tickets', f'Total Tickets ({time_frame})')
active_line_fig = create_line_chart(grouped_active, 'Active Tickets', f'Active Tickets ({time_frame})')
closed_line_fig = create_line_chart(grouped_closed, 'Closed Tickets', f'Closed Tickets ({time_frame})')

# ---------------------------------------
# 🧾 DASHBOARD LAYOUT
# ---------------------------------------
# Summary cards
row1_left, row1_center, row1_right = st.columns([1, 20, 1])
with row1_center:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Total Tickets', total_tickets)
    col2.metric('Active Tickets', active_tickets)
    col3.metric('New Tickets (30d)', new_tickets)
    col4.metric('Closure Rate (%)', f'{closure_rate:.1f}')

st.markdown('---')

# Donut charts
row2_left, row2_center, row2_right = st.columns([1, 20, 1])
with row2_center:
    colA, colB, colC = st.columns(3)
    colA.plotly_chart(category_donut, use_container_width=True)
    colB.plotly_chart(status_donut, use_container_width=True)
    colC.plotly_chart(priority_donut, use_container_width=True)

st.markdown('---')

# Line charts
row3_left, row3_center, row3_right = st.columns([1, 20, 1])
with row3_center:
    colD, colE, colF = st.columns(3)
    colD.plotly_chart(total_line_fig, use_container_width=True)
    colE.plotly_chart(active_line_fig, use_container_width=True)
    colF.plotly_chart(closed_line_fig, use_container_width=True)

# ---------------------------------------
# 🖋️ GLOBAL CSS (DARK THEME TEXT)
# ---------------------------------------
st.markdown("""
    <style>
    html, body, [class^='css'], .stApp, .stSidebarContent, .stMetric {
        color: #fff !important;
        font-family: Arial, sans-serif !important;
    }
    .stButton>button { color: #fff !important; }
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {
        color: #fff !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)
