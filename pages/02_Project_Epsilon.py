import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import datetime as dt
from utils.base import HomeModule
from utils.display import display_time_series, display_simu_vs_truth
from utils.scenario import SimulationHome, SCENARIOS

# Page configuration
st.set_page_config(
    page_title='Project Epsilon',
    page_icon='📊',
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize HomeModule
@st.cache_resource
def init_home_module():
    maison_caussa = HomeModule()
    maison_caussa.init(
        name="maison_caussa",
        temperature_interieur_id="sensor.capteur_salon_temperature",
        temperature_exterieur_id="sensor.paris_17eme_arrondissement_temperature",
        switch_id="input_boolean.radiateur_bureau_switch",
        days_delta=10,
        mean_consumption=2500,
    )
    maison_caussa.load_df()
    return maison_caussa

maison_caussa = init_home_module()

# Section 1: Live Metrics
st.title("Project Epsilon Dashboard")
with st.container():
    st.subheader("📊 Live Metrics")
    
    # Get latest update times and ensure timezone consistency
    latest_temp_int = pd.to_datetime(maison_caussa.temperature_int_df['date'].max()).tz_localize(None)
    latest_temp_ext = pd.to_datetime(maison_caussa.temperature_ext_df['date'].max()).tz_localize(None)
    now = pd.Timestamp.now().tz_localize(None)
    
    # Calculate delays
    temp_int_delay = now - latest_temp_int
    temp_ext_delay = now - latest_temp_ext
    
    # Format delays for display
    def format_delay(delay):
        if delay.total_seconds() < 60:
            return "< 1 min ago"
        elif delay.total_seconds() < 3600:
            return f"{int(delay.total_seconds() / 60)} min ago"
        else:
            return f"{int(delay.total_seconds() / 3600)} hours ago"
    
    # Create three columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_temp_int = float(maison_caussa.temperature_int_df.iloc[-1]["temperature"])
        current_temp_ext = float(maison_caussa.temperature_ext_df.iloc[-1]["temperature"])
        st.metric(
            label="Interior Temperature",
            value=f"{current_temp_int:.1f}°C",
            delta=f"{current_temp_int - current_temp_ext:.1f}°C vs Outside"
        )
        st.caption(f"Last updated: {format_delay(temp_int_delay)}")
    
    # Get consumption data for different periods
    consumption_df = maison_caussa.get_daily_consumption()
    today = dt.date.today()
    consumption_df['day'] = pd.to_datetime(consumption_df['day']).dt.date  # Convert to datetime.date
    
    with col2:
        last_day_consumption = consumption_df[consumption_df['day'] == str(today)]['conso (in kWh)'].sum()
        last_week_consumption = consumption_df[consumption_df['day'] >= (today - dt.timedelta(days=7))]['conso (in kWh)'].sum()
        st.metric(
            label="Daily Heating Consumption",
            value=f"{last_day_consumption:.1f} kWh",
            delta=f"{last_week_consumption:.1f} kWh this week"
        )
        latest_consumption = pd.to_datetime(consumption_df['day'].max()).tz_localize(None)
        consumption_delay = now - latest_consumption
        st.caption(f"Last updated: {format_delay(consumption_delay)}")
    
    with col3:
        last_month_consumption = consumption_df[consumption_df['day'] >= today - dt.timedelta(days=30)]['conso (in kWh)'].sum()
        st.metric(
            label="Monthly Heating Consumption",
            value=f"{last_month_consumption:.1f} kWh",
            delta=None
        )

# Section 2: Historical Data
with st.container():
    st.subheader("📈 Historical Data")
    
    tab1, tab2 = st.tabs(["Time series", "Usage Heatmap"])
    
    with tab1:
        display_time_series()
    
    with tab2:
        # Create hourly heatmap of average heater usage
        hourly_usage = (
            # Create continuous timeline with minute-level granularity
            pd.DataFrame({'date': pd.date_range(
                start=maison_caussa.switch_df['date'].min(),
                end=maison_caussa.switch_df['date'].max(),
                freq='1min'
            )})
            # Merge with switch events, keeping all switch events and timeline points
            .merge(
                maison_caussa.switch_df[['date', 'state']],
                on='date',
                how='outer'
            )
            # Sort to ensure correct forward fill
            .sort_values('date')
            # Forward fill the state and convert to numeric
            .assign(
                state=lambda df: df['state'].fillna(method='ffill').map({'on': 1, 'off': 0}),
                hour=lambda df: df['date'].dt.hour,
                day=lambda df: df['date'].dt.date
            )
            # Calculate average usage by hour
            .groupby(['day', 'hour'])['state']
            .mean()
            .reset_index()
            .groupby('hour')['state']
            .mean()
        )
        
        # Get the maximum usage for normalization
        max_usage = hourly_usage.max()
        if max_usage > 0:  # Avoid division by zero
            normalized_usage = hourly_usage / max_usage
        else:
            normalized_usage = hourly_usage
        
        # Create a more visually appealing timeline using plotly
        fig = go.Figure()
        
        # Add rectangles for each hour
        for hour in range(24):
            # Calculate color: mix of white (255,255,255) and red (255,0,0) based on normalized usage
            intensity = normalized_usage[hour]
            green_blue = int(255 * (1 - intensity))
            
            fig.add_shape(
                type="rect",
                x0=hour,
                x1=hour + 0.9,  # Leave small gap between rectangles
                y0=0,
                y1=1,
                fillcolor=f"rgb(255, {green_blue}, {green_blue})",  # White to red transition
                line=dict(width=1, color="white"),
            )
            
            # Add hour labels
            fig.add_annotation(
                x=hour + 0.45,
                y=-0.3,
                text=f"{hour:02d}h",
                showarrow=False,
                font=dict(size=10)
            )
        
        fig.update_layout(
            title=f'Average Daily Heating Pattern (Max usage: {max_usage:.1%})',
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.5, 24.5]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-0.5, 1.5]
            ),
            height=150,
            margin=dict(l=20, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a legend explanation
        st.markdown(f"""
        <style>
        .legend-container {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .color-box {{
            width: 20px;
            height: 20px;
            border: 1px solid gray;
        }}
        </style>
        <div class="legend-container">
            <div class="color-box" style="background-color: rgb(255, 255, 255);"></div>
            <span>No usage</span>
            <div class="color-box" style="background-color: rgb(255, 0, 0);"></div>
            <span>Max usage ({max_usage:.1%})</span>
        </div>
        """, unsafe_allow_html=True)

# Section 3: Scenarios
with st.container():
    st.subheader("🔮 Simulation Scenarios")
    
    with st.form("Simulation's parameter's"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            T_target = st.number_input("Target temperature for your home", min_value=5, max_value=30, value=20)
        
        with col2:
            T_ext = st.number_input("Outside temperature (mean)", min_value=-30, max_value=40, value=5)
        
        with col3:
            scenario = st.selectbox("Pick a scenario", options=list(SCENARIOS.keys()))
        
        launch_btn = st.form_submit_button("Launch simulation")
    
    if launch_btn:
        maison_caussa.compute_tau()
        maison_caussa.compute_C()
        simu = SimulationHome()
        simu.init(
            name='scenario1',
            T_0=T_target,
            T_ext=T_ext,
            T_target=T_target,
            mean_consumption=2500,
            tau=maison_caussa.tau,
            C=maison_caussa.C,
            granularity=.1
        )
        data = simu.pick_scenario(scenario)
        df = pd.DataFrame(data, columns=["time", "temperature", "switch"])
        df = df.drop_duplicates(ignore_index=True)
        uptime, conso = simu.get_daily_consumption(df)
        st.markdown(f"Heaters uptime: {round(uptime, 2)} (h) - Conso: {round(conso, 2)} (kWh)")
        fig = simu.plot_data(df)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.plotly_chart(fig)
        

# Section 4: Alerts & Recommendations
with st.container():
    st.subheader("⚠️ Alerts & Recommendations")
    st.info("This section is under development and will contain alerts and recommendations based on your usage patterns.")

# Section 5: Reports
with st.container():
    st.subheader("📑 Reports")
    st.info("This section is under development and will allow you to export customized reports from the dashboard.") 