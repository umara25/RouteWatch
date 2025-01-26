import streamlit as st
import pandas as pd
import numpy as np

def home_page():
    """Home Page Content"""
    st.title("Welcome to RouteWatch!")
    st.markdown("""
    ### Plan Safer and Smarter Journeys 🚗
    RouteWatch helps you:
    - Plan optimized trips by avoiding local issues.
    - Report potholes and other road conditions.
    """)

    # Simulated data for a clean line chart
    np.random.seed(42)
    months = ["Jan", "Feb", "Mar", "Apr", "May"]
    data = {
        "Reported Potholes": np.random.randint(20, 50, len(months)),
        "Fixed Issues": np.random.randint(10, 30, len(months))
    }
    chart_data = pd.DataFrame(data, index=months)

    # Line chart
    st.subheader("Monthly Road Issue Report")
    st.line_chart(chart_data)

    # Additional description
    st.markdown("""
    **Get Involved**  
    - Navigate to "Report Issues" to mark problem areas on the map.
    - Use "Optimized Trip" to plan your route efficiently.
    """)

def report_issues_page():
    """Placeholder for Report Issues Page"""
    st.header("Report Local Issues")
    st.text("This page will display a map for reporting local issues.")

def optimized_trip_page():
    """Placeholder for Optimized Trip Page"""
    st.header("Optimized Trip")
    st.text("This page will allow users to calculate routes avoiding local issues.")

def about_page():
    """About Page"""
    st.header("Meet the Team")
    st.markdown("""
    - **Umar Ahmer**: Front End & Back End  
    - **Aayush Aryal**: Front End & Back End
    """)

def login():
    """Login Placeholder"""
    st.sidebar.markdown("## Login")
    username = st.sidebar.text_input("Username:", value="")
    password = st.sidebar.text_input("Password:", value="", type="password")

    if st.sidebar.button("Login"):
        st.sidebar.success("Welcome, user!")

# Main execution
def main():
    # Directly show the home page without navigation
    home_page()

login()
main()
