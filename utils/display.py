import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

def prepare_data(file_path: str) -> pd.DataFrame:
    """
    Prepare data from CSV files for visualization
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Processed DataFrame ready for plotting
    """
    df = pd.read_csv(file_path)
    
    # Handle binary_chauffage.csv format
    if 'entity_id' in df.columns:
        df = df[['state', 'last_changed']]
        df = df.rename(columns={'last_changed': 'timestamp'})
        df['state'] = df['state'].map({'on': 1, 'off': 0})  # Convert to binary
    
    # Handle temperature data format
    elif '°C.mean_value' in df.columns:
        df = df.rename(columns={
            'time': 'timestamp',
            '°C.mean_value': 'temperature'
        })
        df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
    
    # Convert timestamp to datetime
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

def create_combined_graph(data_dir: str):
    """
    Create a combined graph showing all temperature data and heating state
    """
    try:
        # Read all temperature data
        bedroom_df = prepare_data(f'{data_dir}/bedroom_temperature.csv')
        living_room_df = prepare_data(f'{data_dir}/living_room_temperature.csv')
        outside_df = prepare_data(f'{data_dir}/outside_temperature.csv')
        heating_df = prepare_data(f'{data_dir}/binary_chauffage.csv')
        
        # Create figure with secondary y-axis
        fig = go.Figure()
        
        # Add temperature lines
        fig.add_trace(
            go.Scatter(
                x=bedroom_df['timestamp'],
                y=bedroom_df['temperature'],
                name='Bedroom',
                line=dict(color='blue')
            )
        )
        
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
    data_dir = 'data/tests_data'
    
    if not os.path.exists(data_dir):
        st.warning("No data/tests_data directory found")
        return

    # First display the combined graph
    st.subheader("Combined Temperature and Heating Status")
    combined_fig = create_combined_graph(data_dir)
    if combined_fig:
        st.plotly_chart(combined_fig, use_container_width=True)
    
    # Then display individual graphs
    st.subheader("Individual Measurements")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        st.warning("No CSV files found in data/tests_data directory")
        return

    for csv_file in csv_files:
        try:
            # Prepare the data
            df = prepare_data(f'{data_dir}/{csv_file}')
            title = f'Time Series for {csv_file[:-4]}'
            
            # Create different visualizations based on data type
            if 'state' in df.columns:
                fig = create_binary_timeline(df, title)
            else:
                fig = px.line(
                    df,
                    x='timestamp',
                    y='temperature',
                    title=title
                )
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Temperature (°C)",
                    hovermode='x unified'
                )
            
            # Display the plot using Streamlit
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error displaying {csv_file}: {str(e)}")
