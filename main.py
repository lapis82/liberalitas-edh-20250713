import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# Set page configuration
st.set_page_config(
    page_title="Liberalita EDH Inscriptions",
    page_icon="🏛️",
    layout="wide"
)

# Title and description
st.title("🏛️ Liberalita EDH Inscriptions")
st.markdown("Explore inscriptions containing 'liberalita' from the Epigraphic Database Heidelberg")

# Load data function
@st.cache_data
def load_data():
    """Load and preprocess the CSV data"""
    try:
        # Try to load the CSV file
        df = pd.read_csv('liberalita_edh.csv')
        
        # Handle missing location data (lines 30 and 68 - using F column as fallback)
        # Note: pandas uses 0-based indexing, so line 30 is index 29, line 68 is index 67
        if len(df) > 29 and (pd.isna(df.iloc[29]['G']) or df.iloc[29]['G'] == ''):
            df.at[29, 'G'] = df.iloc[29]['F']
        if len(df) > 67 and (pd.isna(df.iloc[67]['G']) or df.iloc[67]['G'] == ''):
            df.at[67, 'G'] = df.iloc[67]['F']
        
        return df
    except FileNotFoundError:
        st.error("CSV file 'liberalita_edh.csv' not found. Please make sure the file is in the same directory as this app.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Load the data
df = load_data()

if df is not None:
    # Sidebar for filters
    st.sidebar.header("Filters")
    
    # Basic info about the dataset
    st.sidebar.info(f"Total inscriptions: {len(df)}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📍 Location Map", "📜 Transcriptions", "📊 Statistics"])
    
    with tab1:
        st.header("Geographic Distribution of Liberalita Inscriptions")
        
        # Clean and process location data
        locations = df['G'].dropna().str.strip()
        locations = locations[locations != '']
        
        if len(locations) > 0:
            # Create a simple frequency map
            location_counts = Counter(locations)
            
            # Create a DataFrame for visualization
            location_df = pd.DataFrame(list(location_counts.items()), 
                                     columns=['Location', 'Count'])
            
            # Display location statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Location Frequency")
                st.dataframe(location_df.sort_values('Count', ascending=False))
            
            with col2:
                st.subheader("Top Locations")
                fig = px.bar(location_df.head(10), 
                           x='Count', 
                           y='Location',
                           orientation='h',
                           title="Top 10 Locations by Inscription Count")
                st.plotly_chart(fig, use_container_width=True)
            
            # Search for specific locations
            st.subheader("Search Locations")
            search_term = st.text_input("Enter location name to search:")
            if search_term:
                filtered_locations = location_df[
                    location_df['Location'].str.contains(search_term, case=False, na=False)
                ]
                if not filtered_locations.empty:
                    st.dataframe(filtered_locations)
                else:
                    st.info("No locations found matching your search.")
        else:
            st.warning("No location data available in column G.")
    
    with tab2:
        st.header("Inscription Transcriptions")
        
        # Display transcriptions with location info
        transcriptions = df[['B', 'G']].copy()
        transcriptions.columns = ['Transcription', 'Location']
        
        # Remove empty transcriptions
        transcriptions = transcriptions.dropna(subset=['Transcription'])
        transcriptions = transcriptions[transcriptions['Transcription'].str.strip() != '']
        
        if len(transcriptions) > 0:
            # Search functionality
            st.subheader("Search Transcriptions")
            search_transcription = st.text_input("Search in transcriptions:")
            
            if search_transcription:
                filtered_transcriptions = transcriptions[
                    transcriptions['Transcription'].str.contains(search_transcription, case=False, na=False)
                ]
                st.write(f"Found {len(filtered_transcriptions)} matching transcriptions:")
                transcriptions_to_show = filtered_transcriptions
            else:
                transcriptions_to_show = transcriptions
            
            # Display transcriptions
            st.subheader("All Transcriptions")
            for idx, row in transcriptions_to_show.iterrows():
                with st.expander(f"Inscription {idx + 1} - {row['Location']}"):
                    st.write("**Location:**", row['Location'])
                    st.write("**Transcription:**")
                    st.text(row['Transcription'])
                    
                    # Highlight "liberalita" in the text
                    if pd.notna(row['Transcription']):
                        highlighted = re.sub(r'(liberalita)', r'**\1**', 
                                           str(row['Transcription']), flags=re.IGNORECASE)
                        st.markdown("**Highlighted text:**")
                        st.markdown(highlighted)
        else:
            st.warning("No transcription data available in column B.")
    
    with tab3:
        st.header("Statistics and Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Dataset Overview")
            st.metric("Total Inscriptions", len(df))
            st.metric("Inscriptions with Locations", len(df['G'].dropna()))
            st.metric("Inscriptions with Transcriptions", len(df['B'].dropna()))
            st.metric("Unique Locations", len(df['G'].dropna().unique()))
        
        with col2:
            st.subheader("Data Completeness")
            completeness = {}
            for col in ['B', 'G']:
                if col in df.columns:
                    completeness[col] = (df[col].notna().sum() / len(df)) * 100
            
            if completeness:
                completeness_df = pd.DataFrame(list(completeness.items()), 
                                             columns=['Column', 'Completeness (%)'])
                completeness_df['Column'] = completeness_df['Column'].map({
                    'B': 'Transcriptions (B)',
                    'G': 'Locations (G)'
                })
                
                fig = px.bar(completeness_df, 
                           x='Column', 
                           y='Completeness (%)',
                           title="Data Completeness by Column")
                st.plotly_chart(fig, use_container_width=True)
        
        # Word analysis in transcriptions
        if 'B' in df.columns:
            st.subheader("Word Analysis in Transcriptions")
            all_text = ' '.join(df['B'].dropna().astype(str))
            
            # Simple word frequency (excluding common words)
            words = re.findall(r'\b\w+\b', all_text.lower())
            common_words = {'et', 'in', 'de', 'ad', 'ex', 'cum', 'pro', 'ab', 'per', 'sub'}
            filtered_words = [word for word in words if len(word) > 2 and word not in common_words]
            
            if filtered_words:
                word_counts = Counter(filtered_words)
                top_words = dict(word_counts.most_common(15))
                
                word_df = pd.DataFrame(list(top_words.items()), 
                                     columns=['Word', 'Frequency'])
                
                fig = px.bar(word_df, 
                           x='Frequency', 
                           y='Word',
                           orientation='h',
                           title="Most Frequent Words in Transcriptions")
                st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Please upload the 'liberalita_edh.csv' file to proceed.")
    st.info("Make sure your CSV file contains columns B (transcriptions) and G (locations).")
