import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Set page config
st.set_page_config(
    page_title="Sri Lanka Informal Sector Wages Dashboard",
    page_icon="💰",
    layout="wide"
)

# Load and preprocess data
@st.cache_data
def load_data():
    # Load the CSV file - using forward slashes works on Windows too
    df = pd.read_csv('average_daily_wages_of_informal_sector_.csv')
    
    # Clean and reshape the data
    df_clean = df.copy()
    
    # Handle missing values and dashes
    for col in df_clean.columns[1:]:  # Skip first column
        df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace('-', ''), errors='coerce')
    
    # Melt the dataframe to long format
    df_melted = df_clean.melt(
        id_vars=['Province and Sector'],
        var_name='Year',
        value_name='Daily_Wage'
    )
    
    # Extract province, sector, and job info
    df_melted['Province'] = ''
    df_melted['Sector'] = ''
    df_melted['Job_Category'] = ''
    df_melted['Gender'] = 'Male'  # Default
    
    current_province = ''
    current_sector = ''
    current_job = ''
    
    for i, row in df_melted.iterrows():
        sector_info = str(row['Province and Sector']).strip()
        
        # Skip empty or NaN rows
        if sector_info == 'nan' or sector_info == '':
            continue
            
        # Identify provinces
        if 'Province' in sector_info or sector_info == 'All Island (d )':
            current_province = sector_info.replace('Province', '').strip()
            if sector_info == 'All Island (d )':
                current_province = 'All Island'
            continue
            
        # Identify sectors
        if 'Sector' in sector_info:
            current_sector = sector_info.replace('Sector', '').strip()
            continue
            
        # Identify job categories
        if sector_info in ['Tea', 'Rubber', 'Coconut', 'Paddy', 'Carpentry', 'Masonry']:
            current_job = sector_info
            continue
            
        # Extract gender and job details
        if sector_info in ['Male', 'Femal']:
            gender = 'Female' if sector_info == 'Femal' else 'Male'
            df_melted.at[i, 'Gender'] = gender
            df_melted.at[i, 'Job_Category'] = current_job
        else:
            # Handle specific job titles
            if 'Male' in sector_info:
                df_melted.at[i, 'Gender'] = 'Male'
                df_melted.at[i, 'Job_Category'] = sector_info.replace('- Male', '').strip()
            elif 'Female' in sector_info:
                df_melted.at[i, 'Gender'] = 'Female' 
                df_melted.at[i, 'Job_Category'] = sector_info.replace('- Female', '').strip()
            else:
                df_melted.at[i, 'Job_Category'] = sector_info
        
        df_melted.at[i, 'Province'] = current_province
        df_melted.at[i, 'Sector'] = current_sector
    
    # Remove rows with empty province or invalid wages
    df_final = df_melted[
        (df_melted['Province'] != '') & 
        (df_melted['Daily_Wage'].notna()) & 
        (df_melted['Daily_Wage'] > 0)
    ].copy()
    
    df_final['Year'] = df_final['Year'].astype(int)
    
    return df_final

# Main dashboard
def main():
    st.title("💰 Sri Lanka Informal Sector Daily Wages Dashboard")
    st.markdown("---")
    
    # Load data
    try:
        df = load_data()
    except FileNotFoundError:
        st.error("❌ Could not find the CSV file. Please ensure 'average_daily_wages_of_informal_sector_.csv' is in the 'desktop/data_sets/' folder.")
        return
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return
    
    # Sidebar filters
    st.sidebar.header("🔧 Filters")
    
    # Province filter
    provinces = ['All'] + sorted(df['Province'].unique().tolist())
    selected_province = st.sidebar.selectbox("Select Province:", provinces)
    
    # Sector filter
    sectors = ['All'] + sorted(df['Sector'].unique().tolist())
    selected_sector = st.sidebar.selectbox("Select Sector:", sectors)
    
    # Year range filter
    min_year, max_year = int(df['Year'].min()), int(df['Year'].max())
    year_range = st.sidebar.slider("Select Year Range:", min_year, max_year, (min_year, max_year))
    
    # Gender filter
    genders = ['All', 'Male', 'Female']
    selected_gender = st.sidebar.selectbox("Select Gender:", genders)
    
    # Filter data
    filtered_df = df[
        (df['Year'] >= year_range[0]) & 
        (df['Year'] <= year_range[1])
    ]
    
    if selected_province != 'All':
        filtered_df = filtered_df[filtered_df['Province'] == selected_province]
    
    if selected_sector != 'All':
        filtered_df = filtered_df[filtered_df['Sector'] == selected_sector]
        
    if selected_gender != 'All':
        filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_wage = filtered_df['Daily_Wage'].mean()
        st.metric("Average Daily Wage", f"Rs. {avg_wage:.0f}" if not pd.isna(avg_wage) else "N/A")
    
    with col2:
        max_wage = filtered_df['Daily_Wage'].max()
        st.metric("Highest Daily Wage", f"Rs. {max_wage:.0f}" if not pd.isna(max_wage) else "N/A")
    
    with col3:
        min_wage = filtered_df['Daily_Wage'].min()
        st.metric("Lowest Daily Wage", f"Rs. {min_wage:.0f}" if not pd.isna(min_wage) else "N/A")
    
    with col4:
        total_records = len(filtered_df)
        st.metric("Total Records", f"{total_records:,}")
    
    st.markdown("---")
    
    # Charts
    if len(filtered_df) > 0:
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends Over Time", "🗺️ Provincial Comparison", "⚖️ Gender Gap Analysis", "📊 Sector Analysis"])
        
        with tab1:
            st.subheader("Daily Wages Trends Over Time")
            
            # Group by year and calculate average
            yearly_avg = filtered_df.groupby(['Year', 'Province', 'Sector'])['Daily_Wage'].mean().reset_index()
            
            fig_trend = px.line(
                yearly_avg, 
                x='Year', 
                y='Daily_Wage',
                color='Province' if selected_province == 'All' else 'Sector',
                title="Average Daily Wages Trend",
                labels={'Daily_Wage': 'Daily Wage (Rs.)', 'Year': 'Year'},
                markers=True
            )
            fig_trend.update_layout(height=500)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with tab2:
            st.subheader("Provincial Wage Comparison")
            
            # Average wage by province
            province_avg = filtered_df.groupby('Province')['Daily_Wage'].mean().sort_values(ascending=False)
            
            fig_province = px.bar(
                x=province_avg.index,
                y=province_avg.values,
                title="Average Daily Wages by Province",
                labels={'x': 'Province', 'y': 'Average Daily Wage (Rs.)'},
                color=province_avg.values,
                color_continuous_scale='viridis'
            )
            fig_province.update_layout(height=500)
            st.plotly_chart(fig_province, use_container_width=True)
        
        with tab3:
            st.subheader("Gender Wage Gap Analysis")
            
            # Gender comparison
            gender_comparison = filtered_df.groupby(['Gender', 'Year'])['Daily_Wage'].mean().reset_index()
            
            fig_gender = px.line(
                gender_comparison,
                x='Year',
                y='Daily_Wage',
                color='Gender',
                title="Daily Wages by Gender Over Time",
                labels={'Daily_Wage': 'Daily Wage (Rs.)', 'Year': 'Year'},
                markers=True
            )
            fig_gender.update_layout(height=400)
            st.plotly_chart(fig_gender, use_container_width=True)
            
            # Gender gap metrics
            male_avg = filtered_df[filtered_df['Gender'] == 'Male']['Daily_Wage'].mean()
            female_avg = filtered_df[filtered_df['Gender'] == 'Female']['Daily_Wage'].mean()
            
            if not pd.isna(male_avg) and not pd.isna(female_avg):
                gap_percentage = ((male_avg - female_avg) / female_avg) * 100
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Male Average", f"Rs. {male_avg:.0f}")
                with col2:
                    st.metric("Female Average", f"Rs. {female_avg:.0f}")
                with col3:
                    st.metric("Gender Gap", f"{gap_percentage:.1f}%")
        
        with tab4:
            st.subheader("Sector-wise Analysis")
            
            # Sector comparison
            sector_avg = filtered_df.groupby(['Sector', 'Job_Category'])['Daily_Wage'].mean().reset_index()
            
            fig_sector = px.box(
                filtered_df,
                x='Sector',
                y='Daily_Wage',
                title="Daily Wage Distribution by Sector",
                labels={'Daily_Wage': 'Daily Wage (Rs.)'}
            )
            fig_sector.update_layout(height=500)
            st.plotly_chart(fig_sector, use_container_width=True)
            
            # Top paying jobs
            st.subheader("Top Paying Job Categories")
            top_jobs = filtered_df.groupby('Job_Category')['Daily_Wage'].mean().sort_values(ascending=False).head(10)
            
            fig_jobs = px.bar(
                x=top_jobs.values,
                y=top_jobs.index,
                orientation='h',
                title="Top 10 Highest Paying Job Categories",
                labels={'x': 'Average Daily Wage (Rs.)', 'y': 'Job Category'},
                color=top_jobs.values,
                color_continuous_scale='plasma'
            )
            fig_jobs.update_layout(height=600)
            st.plotly_chart(fig_jobs, use_container_width=True)
    
    else:
        st.warning("⚠️ No data available for the selected filters. Please adjust your selection.")
    
    # Data preview
    with st.expander("📋 View Raw Data"):
        st.dataframe(filtered_df.head(100))
        st.info(f"Showing first 100 rows out of {len(filtered_df)} total rows")

if __name__ == "__main__":
    main()