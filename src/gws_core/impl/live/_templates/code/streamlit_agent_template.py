# This is a template for a streamlit agent.
# This generates an app with one dataframe as input. Then the user can select 2 columns to plot a scatter plot.

import plotly.express as px
import streamlit as st
from pandas import DataFrame

# Your Streamlit app code here
st.title("Dashboard example")

# show a table from file_path which is a csv file full width
if sources:
    df: DataFrame = sources[0].get_data()

    # show the dataframe
    st.dataframe(df)

    # add a select widget with the columns names with no default value
    # set the selectbox side by side
    col1, col2 = st.columns(2)

    with col1:
        x_col = st.selectbox("Select x column", options=df.columns, index=0)

    with col2:
        y_col = st.selectbox("Select y column", options=df.columns, index=1)

    if x_col and y_col:
        # Generate a scatter plot with plotly express
        fig = px.scatter(df, x=x_col, y=y_col)
        st.plotly_chart(fig)
