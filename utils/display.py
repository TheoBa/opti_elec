import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import datetime as dt
from utils.scenario import SimulationHome


def prepare_data(file_path: str) -> pd.DataFrame:
    """
    Prepare data from CSV files for visualization
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Processed DataFrame ready for plotting
    """
    df = pd.read_csv(file_path)
    df = df.rename(columns={'date': 'timestamp'})
    
    if 'state' in df.columns:
        df['state'] = df['state'].map({'on': 1, 'off': 0})  # Convert to binary
    else:
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df

def create_binary_timeline(df: pd.DataFrame, title: str) -> go.Figure:
    """
    Create a timeline visualization for binary state data
    
    Args:
        df (pd.DataFrame): DataFrame with 'timestamp' and 'state' columns
        title (str): Title for the plot
        
    Returns:
        go.Figure: Plotly figure object
    """
    # Create figure
    fig = go.Figure()
    
    # Add colored segments for state changes
    for i in range(len(df) - 1):
        color = 'green' if df.iloc[i]['state'] == 1 else 'red'
        
        # Add colored rectangle for each time period
        fig.add_trace(go.Scatter(
            x=[df.iloc[i]['timestamp'], df.iloc[i+1]['timestamp']],
            y=[1, 1],
            mode='lines',
            line=dict(color=color, width=20),
            showlegend=False
        ))
        
        # Add markers at state changes
        fig.add_trace(go.Scatter(
            x=[df.iloc[i]['timestamp']],
            y=[1],
            mode='markers',
            marker=dict(
                symbol='line-ns',
                size=15,
                color='black'
            ),
            showlegend=False
        ))
    
    # Add final marker
    fig.add_trace(go.Scatter(
        x=[df.iloc[-1]['timestamp']],
        y=[1],
        mode='markers',
        marker=dict(
            symbol='line-ns',
            size=15,
            color='black'
        ),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        showlegend=False,
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0.5, 1.5]  # Center the timeline vertically
        ),
        xaxis=dict(
            title="Time",
            showgrid=True
        ),
        hovermode='x unified',
        height=200  # Reduce height since we only need space for the timeline
    )
    
    # Add annotations for legend
    fig.add_annotation(
        text="ON",
        xref="paper", yref="paper",
        x=0.02, y=1.15,
        showarrow=False,
        font=dict(color="green", size=14),
        bgcolor="white",
        bordercolor="green",
        borderwidth=2
    )
    fig.add_annotation(
        text="OFF",
        xref="paper", yref="paper",
        x=0.12, y=1.15,
        showarrow=False,
        font=dict(color="red", size=14),
        bgcolor="white",
        bordercolor="red",
        borderwidth=2
    )
    
    return fig

def filter_date_range(df: pd.DataFrame, day_min: dt.datetime, day_max: dt.datetime) -> pd.DataFrame:
    """
    Filter DataFrame to only include rows between day_min and day_max
    
    Args:
        df (pd.DataFrame): DataFrame with 'timestamp' column
        day_min (dt.datetime): Start date (inclusive)
        day_max (dt.datetime): End date (inclusive)
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    # Convert day_min and day_max to UTC timezone-aware datetime
    day_min = pd.to_datetime(day_min).tz_localize('UTC').replace(hour=0, minute=0, second=0)
    day_max = pd.to_datetime(day_max).tz_localize('UTC').replace(hour=23, minute=59, second=59)
    
    # Ensure DataFrame timestamps are in UTC
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    
    # Filter DataFrame
    mask = (df['timestamp'] >= day_min) & (df['timestamp'] <= day_max)
    return df[mask]

def create_combined_graph(data_dir: str, day_min: dt.datetime, day_max: dt.datetime):
    """
    Create a combined graph showing all temperature data and heating state
    """
    try:
        living_room_df = filter_date_range(prepare_data(f'{data_dir}/capteur_salon_temperature.csv'), day_min, day_max)
        outside_df = filter_date_range(prepare_data(f'{data_dir}/paris_17eme_arrondissement_temperature.csv'), day_min, day_max)
        heating_df = filter_date_range(prepare_data(f'{data_dir}/radiateur_bureau_switch.csv'), day_min, day_max)
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=living_room_df['timestamp'],
                y=living_room_df['temperature'],
                name='Living Room',
                line=dict(color='orange')
            )
        )
        
        fig.add_trace(
            go.Scatter(
                x=outside_df['timestamp'],
                y=outside_df['temperature'],
                name='Outside',
                line=dict(color='gray')
            )
        )
        
        # Create square signal by duplicating points
        x_square = []
        y_square = []
        text_square = []
        
        for i in range(len(heating_df)):
            if i > 0:
                # Add vertical transition point
                x_square.append(heating_df.iloc[i]['timestamp'])
                y_square.append(y_square[-1])  # Use previous y value
                text_square.append(text_square[-1])
            
            # Add horizontal point
            x_square.append(heating_df.iloc[i]['timestamp'])
            y_square.append(heating_df.iloc[i]['state'] * 5 + 25)  # Scale and shift
            text_square.append('ON' if heating_df.iloc[i]['state'] == 1 else 'OFF')
        
        # Add heating state as a proper square signal
        fig.add_trace(
            go.Scatter(
                x=x_square,
                y=y_square,
                name='Heating',
                line=dict(color='black', width=2),
                mode='lines',
                hovertemplate='Status: %{text}<br>Time: %{x}',
                text=text_square
            )
        )
        
        # Update layout
        fig.update_layout(
            title='Combined Temperature and Heating Status',
            xaxis_title='Time',
            yaxis_title='Temperature (°C)',
            hovermode='x unified',
            height=600,
            yaxis=dict(range=[-5, 35]),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating combined graph: {str(e)}")
        return None

def display_time_series():
    """
    Display time series plots for all CSV files in the data/tests_data directory
    using Plotly and Streamlit
    """
    data_dir = 'data/db'

    with st.form("Display current data"):
        day_min = st.date_input("Start date", value=dt.datetime(2025, 1, 3))
        day_max = st.date_input("End date", value=dt.datetime.today())
        submit_btn = st.form_submit_button("Submit date range")

    if submit_btn:
        if not os.path.exists(data_dir):
            st.warning("No data/tests_data directory found")
            return

        st.subheader("Combined Temperature and Heating Status")
        combined_fig = create_combined_graph(data_dir, day_min, day_max)
        if combined_fig:
            st.plotly_chart(combined_fig, use_container_width=True)

def display_simu_vs_truth(T_ext, tau, C, daily_switch_inputs_df, daily_temp_int, daily_conso):
    simulation = SimulationHome()
    simulation.init(
        name='simu vs réalité',
        T_0=daily_temp_int.loc[0, "temperature"],
        T_ext=T_ext,
        T_target=10000, #don't care
        mean_consumption=2500,
        tau=tau,
        C=C,
        granularity=.25,
        daily_switch_inputs_df=daily_switch_inputs_df
    )
    data = simulation.pick_scenario("Real inputs")
    df = pd.DataFrame(data, columns=["time", "temperature", "switch"])
    df = df.drop_duplicates(ignore_index=True)
    uptime, conso = simulation.get_daily_consumption(df)
    st.markdown(f"Heaters uptime: {round(uptime, 2)} (h) - Conso: {round(conso, 2)} (kWh)")
    daily_temp_int["time"] = daily_temp_int["date"].dt.hour + round(daily_temp_int["date"].dt.minute / 60, 2)

    fig = simulation.plot_data(df, is_comfort_zone=False)
    fig.add_trace(
        go.Scatter(
            x=daily_temp_int['time'],
            y=daily_temp_int['temperature'],
            name="True Temp",
            line=dict(color='black'),
            yaxis="y"
        )
    )
    col1, col2 = st.columns([4, 1])
    with col1:
        st.plotly_chart(fig)
    with col2:
        st.metric(
            f"Simulated daily conso",
            value=f"{round(daily_conso.iloc[0], 2)} kWh",
            delta=round(daily_conso.iloc[0] - conso, 2),
            border=True
        )
    return