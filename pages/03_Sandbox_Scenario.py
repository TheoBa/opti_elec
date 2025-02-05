import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Page configuration
st.set_page_config(
    page_title='Sandbox Scenario',
    page_icon='🧪',
    layout="wide",
    initial_sidebar_state="collapsed"
)

def sandbox_scenario_page():
    st.title("Sandbox Scenario")
    st.markdown("Create your custom heating scenarios by defining rules.")

    # Initialize session state for rules
    if 'rules' not in st.session_state:
        st.session_state['rules'] = []

    # Input form for new rule
    with st.form("Add Rule"):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_time = st.time_input("Start Time", value=pd.to_datetime("00:00").time())
        with col2:
            end_time = st.time_input("End Time", value=pd.to_datetime("01:00").time())
        with col3:
            usage_type = st.selectbox("Usage Type", options=['cooling', 'heating', 'thermostat'])

        add_rule_btn = st.form_submit_button("Add Rule")

    # Add rule to session state
    if add_rule_btn:
        st.session_state['rules'].append({
            'start_time': start_time,
            'end_time': end_time,
            'usage_type': usage_type
        })

    # Display current rules
    st.subheader("Current Rules")
    for rule in st.session_state['rules']:
        st.write(f"{rule['start_time']} - {rule['end_time']}: {rule['usage_type']}")

    # Plot timeline
    st.subheader("Scenario Timeline")
    fig = go.Figure()

    for rule in st.session_state['rules']:
        color = {'cooling': 'blue', 'heating': 'red', 'thermostat': 'orange'}[rule['usage_type']]
        fig.add_shape(
            type="rect",
            x0=rule['start_time'].hour + rule['start_time'].minute / 60,
            x1=rule['end_time'].hour + rule['end_time'].minute / 60,
            y0=0,
            y1=1,
            fillcolor=color,
            line=dict(width=0)
        )

    fig.update_layout(
        xaxis=dict(range=[0, 24], title="Time (hours)"),
        yaxis=dict(showticklabels=False),
        height=200,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Save scenario
    st.subheader("Save Scenario")
    scenario_name = st.text_input("Scenario Name")
    if st.button("Save Scenario"):
        if scenario_name:
            # Save the scenario locally
            scenario_df = pd.DataFrame(st.session_state['rules'])
            scenario_df.to_csv(f"data/scenarios/{scenario_name}.csv", index=False)
            st.success(f"Scenario '{scenario_name}' saved successfully!")
        else:
            st.error("Please enter a scenario name.")

sandbox_scenario_page()