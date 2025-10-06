import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
from PIL import Image
import base64

# Set background image using custom CSS
def set_bg(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url('data:image/jpg;base64,{encoded}');
            background-size: cover;
            background-blend-mode: darken;
        }}
        </style>
    """, unsafe_allow_html=True)

set_bg('images/bg.jpg')

# Layout: Hamburger button outside yellow bar, yellow bar contains logo and title
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
                <span style='font-size:24px; font-weight:bold; color:#3F58A6; vertical-align:middle;'>Service Ticket Dashboard</span>
            </div>
        """, unsafe_allow_html=True)
    with col_spacer:
        st.markdown("")

# Add spacing after the yellow bar
st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

# Initialize session state for filter visibility
if 'show_filters' not in st.session_state:
    st.session_state['show_filters'] = False

# Load data
df = pd.read_csv('service_ticket_details.csv')

df['CreatedDate'] = pd.to_datetime(df['CreatedDate'])
df['ClosedDate'] = pd.to_datetime(df['ClosedDate'], errors='coerce')

# Sidebar filters (activated by logo click)
if st.session_state.get('show_filters', False):
    with st.sidebar:
        st.title("Service Ticket Dashboard")
        st.header("⚙️ Filters")
        min_date, max_date = df['CreatedDate'].min().date(), df['CreatedDate'].max().date()
        start_date = st.date_input("Start date", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.date_input("End date", min_value=min_date, max_value=max_date, value=max_date)
        all_categories = list(df['Category'].unique())
        all_priorities = list(df['Priority'].unique())
        all_statuses = list(df['Status'].unique())
        category = st.multiselect('Category', options=all_categories, default=all_categories)
        priority = st.multiselect('Priority', options=all_priorities, default=all_priorities)
        status = st.multiselect('Status', options=all_statuses, default=all_statuses)
        time_frame = st.selectbox("Time frame", ("Daily", "Monthly", "Quarterly", "Yearly"))
else:
    # Default filter values
    start_date = df['CreatedDate'].min().date()
    end_date = df['CreatedDate'].max().date()
    category = list(df['Category'].unique())
    priority = list(df['Priority'].unique())
    status = list(df['Status'].unique())
    time_frame = "Monthly"

# Filter data
filtered_df = df[
    (df['CreatedDate'].dt.date >= start_date) &
    (df['CreatedDate'].dt.date <= end_date) &
    (df['Category'].isin(category)) &
    (df['Priority'].isin(priority)) &
    (df['Status'].isin(status))
]

# Metrics for summary cards
total_tickets = len(filtered_df)
active_tickets = filtered_df[filtered_df['Status'].isin(['Open', 'In Progress', 'On Hold'])].shape[0]
new_tickets = filtered_df[filtered_df['CreatedDate'] > (datetime.now() - pd.Timedelta(days=30))].shape[0]
closed_tickets = filtered_df[filtered_df['Status'] == 'Closed'].shape[0]
closure_rate = closed_tickets / total_tickets * 100 if total_tickets > 0 else 0

# Chart style config and color palette (define before any chart)
chart_layout = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#fff', family='Arial', size=14), # white
    title_font=dict(color='#fff', family='Arial', size=18),
    legend=dict(font=dict(color='#fff')),
    xaxis=dict(title_font=dict(color='#fff'), tickfont=dict(color='#fff')),
    yaxis=dict(title_font=dict(color='#fff'), tickfont=dict(color='#fff')),
)
CHART_COLORS = ['#3F58A6', '#97934F', '#C19F62', '#FFD900']

# Define yellow shades for bar and line charts
YELLOW_SHADES = [
    '#FFD900',  # base
    '#FFE34D',
    '#FFEB80',
    '#FFF3B3',
    '#FFF9CC',
    '#FFFDE6',
]

# Donut charts (middle row)
cat_counts = filtered_df['Category'].value_counts().reset_index()
cat_counts.columns = ['Category', 'Count']
category_donut = px.pie(cat_counts, names='Category', values='Count', title='Tickets by Category', hole=0.5, color_discrete_sequence=CHART_COLORS)
category_donut.update_layout(**chart_layout)

priority_counts = filtered_df['Priority'].value_counts().reset_index()
priority_counts.columns = ['Priority', 'Count']
priority_donut = px.pie(priority_counts, names='Priority', values='Count', title='Tickets by Priority', hole=0.5, color_discrete_sequence=CHART_COLORS)
priority_donut.update_layout(**chart_layout)

status_counts = filtered_df['Status'].value_counts().reset_index()
status_counts.columns = ['Status', 'Count']
status_donut = px.pie(status_counts, names='Status', values='Count', title='Tickets by Status', hole=0.5, color_discrete_sequence=CHART_COLORS)
status_donut.update_layout(**chart_layout)

# Line charts (bottom row): Total, Active, and Closed tickets over selected time frame
if time_frame == "Daily":
    df_time = filtered_df.copy()
    df_time['TimeGroup'] = df_time['CreatedDate'].dt.date
elif time_frame == "Monthly":
    df_time = filtered_df.copy()
    df_time['TimeGroup'] = df_time['CreatedDate'].dt.to_period('M').dt.strftime('%b %Y')
elif time_frame == "Quarterly":
    df_time = filtered_df.copy()
    df_time['TimeGroup'] = df_time['CreatedDate'].dt.to_period('Q').astype(str)
else:  # Yearly
    df_time = filtered_df.copy()
    df_time['TimeGroup'] = df_time['CreatedDate'].dt.year.astype(str)

grouped_total = df_time.groupby('TimeGroup').size().reset_index(name='Total Tickets')
grouped_active = df_time[df_time['Status'].isin(['Open', 'In Progress', 'On Hold'])].groupby('TimeGroup').size().reset_index(name='Active Tickets')
grouped_closed = df_time[df_time['Status'] == 'Closed'].groupby('TimeGroup').size().reset_index(name='Closed Tickets')

total_line_fig = px.line(
    grouped_total, x='TimeGroup', y='Total Tickets', title=f'Total Tickets ({time_frame})',
    line_shape='linear', markers=True, color_discrete_sequence=YELLOW_SHADES
)
total_line_fig.update_layout(**chart_layout)

active_line_fig = px.line(
    grouped_active, x='TimeGroup', y='Active Tickets', title=f'Active Tickets ({time_frame})',
    line_shape='linear', markers=True, color_discrete_sequence=YELLOW_SHADES
)
active_line_fig.update_layout(**chart_layout)

closed_line_fig = px.line(
    grouped_closed, x='TimeGroup', y='Closed Tickets', title=f'Closed Tickets ({time_frame})',
    line_shape='linear', markers=True, color_discrete_sequence=YELLOW_SHADES
)
closed_line_fig.update_layout(**chart_layout)

# Layout
st.set_page_config(layout='wide', page_title='Service Ticket Dashboard')

# Summary cards (top)
row1_left, row1_center, row1_right = st.columns([1, 20, 1])
with row1_center:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Total Tickets', total_tickets)
    col2.metric('Active Tickets', active_tickets)
    col3.metric('New Tickets (30d)', new_tickets)
    col4.metric('Closure Rate (%)', f'{closure_rate:.1f}')

st.markdown('---')

# Donut charts (middle row)
row2_left, row2_center, row2_right = st.columns([1, 20, 1])
with row2_center:
    colA, colB, colC = st.columns(3)
    colA.plotly_chart(category_donut, use_container_width=True)
    colB.plotly_chart(status_donut, use_container_width=True)
    colC.plotly_chart(priority_donut, use_container_width=True)

st.markdown('---')

# Line charts (bottom row): Total, Active, and Closed tickets over selected time frame
row3_left, row3_center, row3_right = st.columns([1, 20, 1])
with row3_center:
    colD, colE, colF = st.columns(3)
    colD.plotly_chart(total_line_fig, use_container_width=True)
    colE.plotly_chart(active_line_fig, use_container_width=True)
    colF.plotly_chart(closed_line_fig, use_container_width=True)

# Set dark font color globally using custom CSS
st.markdown("""
    <style>
    html, body, [class^='css'], .stApp, .stSidebarContent, .stMetric, .stTitle, .stHeader, .stSubheader, .stCaption, .stMarkdown, .stDataFrame {
        color: #fff !important;
        font-family: Arial, sans-serif !important;
    }
    .stButton>button {
        color: #fff !important;
    }
    /* Metric card value and label color */
    div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {
        color: #fff !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)
