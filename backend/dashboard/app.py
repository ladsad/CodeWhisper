import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import glob

# Add parent directory to path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.analyzer import MetricsAnalyzer

st.set_page_config(page_title="CodeWhisper Dashboard", layout="wide")

st.title("CodeWhisper: Tech Debt Dashboard")

# Sidebar for configuration
st.sidebar.header("Configuration")
repo_path = st.sidebar.text_input("Repository Path", value=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
analyze_btn = st.sidebar.button("Run Analysis")

@st.cache_data
def run_analysis(path):
    analyzer = MetricsAnalyzer()
    results = []
    
    # Scan for .py and .java files
    files = []
    for ext in ['*.py', '*.java']:
        files.extend(glob.glob(os.path.join(path, '**', ext), recursive=True))
    
    # Filter out venv and cache
    files = [f for f in files if 'venv' not in f and '__pycache__' not in f and 'node_modules' not in f]
    
    progress_bar = st.progress(0)
    for i, file_path in enumerate(files):
        try:
            metrics = analyzer.analyze_file(file_path)
            if metrics:
                results.append(metrics)
        except Exception as e:
            st.error(f"Error analyzing {file_path}: {e}")
        progress_bar.progress((i + 1) / len(files))
    
    return results

if analyze_btn or 'analysis_results' in st.session_state:
    if analyze_btn:
        with st.spinner("Analyzing repository..."):
            results = run_analysis(repo_path)
            st.session_state['analysis_results'] = results
    else:
        results = st.session_state['analysis_results']

    if not results:
        st.warning("No results found. Please check the repository path.")
    else:
        # Process data for visualization
        df_files = []
        all_functions = []
        
        for r in results:
            file_data = {
                "File": os.path.relpath(r['file_path'], repo_path),
                "LOC": r.get('loc', 0),
                "Maintainability Index": r.get('maintainability_index', 0),
                "Language": r.get('language', 'unknown')
            }
            
            # Aggregate function metrics
            funcs = r.get('functions', [])
            if funcs:
                avg_complexity = sum(f['cyclomatic_complexity'] for f in funcs) / len(funcs)
                doc_count = sum(1 for f in funcs if f.get('has_docstring', False))
                coverage = (doc_count / len(funcs)) * 100
                max_complexity = max(f['cyclomatic_complexity'] for f in funcs)
            else:
                avg_complexity = 0
                coverage = 0
                max_complexity = 0
                
            file_data['Avg Complexity'] = avg_complexity
            file_data['Max Complexity'] = max_complexity
            file_data['Doc Coverage'] = coverage
            file_data['Function Count'] = len(funcs)
            
            df_files.append(file_data)
            
            for f in funcs:
                f['File'] = os.path.relpath(r['file_path'], repo_path)
                all_functions.append(f)
        
        df = pd.DataFrame(df_files)
        
        # --- 1. Repository Health Card ---
        st.header("1. Repository Health")
        
        # Weighted Score: 50% MI, 30% Doc Coverage, 20% (100 - Complexity*5)
        avg_mi = df['Maintainability Index'].mean()
        avg_coverage = df['Doc Coverage'].mean()
        avg_complexity = df['Avg Complexity'].mean()
        
        # Normalize complexity (assuming > 20 is bad)
        comp_score = max(0, 100 - (avg_complexity * 5))
        
        health_score = (avg_mi * 0.5) + (avg_coverage * 0.3) + (comp_score * 0.2)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Health Score", f"{health_score:.1f}/100")
        col2.metric("Avg Maintainability", f"{avg_mi:.1f}")
        col3.metric("Doc Coverage", f"{avg_coverage:.1f}%")
        col4.metric("Avg Complexity", f"{avg_complexity:.1f}")
        
        # --- 2. Complexity Heatmap ---
        st.header("2. Complexity Heatmap")
        
        # Treemap is good for file hierarchy and size/complexity
        fig_tree = px.treemap(
            df, 
            path=[px.Constant("Repo"), 'File'], 
            values='LOC',
            color='Max Complexity',
            color_continuous_scale='RdYlGn_r', # Red is high complexity
            hover_data=['Doc Coverage', 'Maintainability Index'],
            title="Code Complexity by File Size (Color = Max Complexity)"
        )
        st.plotly_chart(fig_tree, use_container_width=True)
        
        # --- 3. Documentation Coverage ---
        st.header("3. Documentation Coverage")
        
        fig_bar = px.histogram(
            df, 
            x='Doc Coverage', 
            nbins=20, 
            title="Distribution of Documentation Coverage per File",
            labels={'Doc Coverage': 'Documentation Coverage (%)'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # --- 4. Flagged Files ---
        st.header("4. Flagged Files (Tech Debt)")
        
        # Flagging criteria: MI < 65 (Radon default for 'B/C'), Complexity > 10, Coverage < 50%
        flagged = df[
            (df['Maintainability Index'] < 65) | 
            (df['Max Complexity'] > 10) | 
            (df['Doc Coverage'] < 50)
        ].sort_values(by='Max Complexity', ascending=False)
        
        st.dataframe(
            flagged.style.applymap(
                lambda x: 'color: red' if x < 65 else '', subset=['Maintainability Index']
            ).applymap(
                lambda x: 'color: red' if x > 10 else '', subset=['Max Complexity']
            ).applymap(
                lambda x: 'color: red' if x < 50 else '', subset=['Doc Coverage']
            ),
            use_container_width=True
        )

else:
    st.info("Click 'Run Analysis' to start.")
