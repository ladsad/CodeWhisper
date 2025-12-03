import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os
import glob

# Add parent directory to path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.analyzer import MetricsAnalyzer

# --- Page Config ---
st.set_page_config(page_title="CodeWhisper Report", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for "Old School PDF" Look ---
st.markdown("""
<style>
    /* Main App Background - Dark Reader Grey */
    .stApp {
        background-color: #525659;
    }
    
    /* Sidebar - Darker Grey */
    [data-testid="stSidebar"] {
        background-color: #323639;
        border-right: 1px solid #000;
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
        font-family: 'Courier New', Courier, monospace;
    }

    /* Main Content Container - The "Paper" */
    .block-container {
        background-color: #fdfbf7; /* Warm Paper White */
        padding: 4rem 5rem !important;
        max-width: 900px;
        margin: 2rem auto;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
        border-radius: 1px;
        color: #2c2c2c;
        font-family: 'Times New Roman', Times, serif;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Times New Roman', Times, serif;
        color: #1a1a1a;
        font-weight: bold;
    }
    
    h1 {
        font-size: 2.5rem;
        text-align: center;
        border-bottom: 2px solid #1a1a1a;
        padding-bottom: 1rem;
        margin-bottom: 2rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    h2 {
        font-size: 1.5rem;
        border-bottom: 1px solid #ccc;
        margin-top: 2rem;
        padding-bottom: 0.5rem;
    }
    
    p, li, div {
        font-family: 'Times New Roman', Times, serif;
        font-size: 1.1rem;
        line-height: 1.6;
    }

    /* Metrics Cards - Styled like stamped boxes */
    [data-testid="stMetricValue"] {
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
        color: #8b0000; /* Dark Red Ink */
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Times New Roman', Times, serif;
        color: #555;
    }
    
    /* Tables - Print Style */
    .stDataFrame {
        font-family: 'Courier New', Courier, monospace;
        border: 1px solid #000;
    }

    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- Sidebar Controls ---
st.sidebar.title("DOCUMENT CONTROLS")
st.sidebar.markdown("---")
repo_path = st.sidebar.text_input("SOURCE PATH", value=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
analyze_btn = st.sidebar.button("GENERATE REPORT")
st.sidebar.markdown("---")
st.sidebar.info("v1.0.0 | CONFIDENTIAL")

# --- Analysis Logic ---
@st.cache_data
def run_analysis(path):
    analyzer = MetricsAnalyzer()
    results = []
    files = []
    for ext in ['*.py', '*.java']:
        files.extend(glob.glob(os.path.join(path, '**', ext), recursive=True))
    files = [f for f in files if 'venv' not in f and '__pycache__' not in f and 'node_modules' not in f]
    
    progress_bar = st.sidebar.progress(0)
    for i, file_path in enumerate(files):
        try:
            metrics = analyzer.analyze_file(file_path)
            if metrics:
                results.append(metrics)
        except Exception:
            pass
        progress_bar.progress((i + 1) / len(files))
    return results

# --- Main Document Content ---

if analyze_btn or 'analysis_results' in st.session_state:
    if analyze_btn:
        with st.spinner("Compiling Report..."):
            results = run_analysis(repo_path)
            st.session_state['analysis_results'] = results
    else:
        results = st.session_state['analysis_results']

    if not results:
        st.warning("No data found. Please verify the source path.")
    else:
        # Data Processing
        df_files = []
        for r in results:
            funcs = r.get('functions', [])
            if funcs:
                avg_complexity = sum(f['cyclomatic_complexity'] for f in funcs) / len(funcs)
                doc_count = sum(1 for f in funcs if f.get('has_docstring', False))
                coverage = (doc_count / len(funcs)) * 100
                max_complexity = max(f['cyclomatic_complexity'] for f in funcs)
            else:
                avg_complexity = 0; coverage = 0; max_complexity = 0
                
            df_files.append({
                "File": os.path.relpath(r['file_path'], repo_path),
                "LOC": r.get('loc', 0),
                "MI": r.get('maintainability_index', 0),
                "Avg Comp": avg_complexity,
                "Max Comp": max_complexity,
                "Doc %": coverage
            })
        
        df = pd.DataFrame(df_files)

        # --- Document Header ---
        st.markdown("# TECHNICAL DEBT AUDIT REPORT")
        st.markdown(f"**DATE:** {pd.Timestamp.now().strftime('%Y-%m-%d')}")
        st.markdown(f"**TARGET:** `{repo_path}`")
        st.markdown(f"**FILES SCANNED:** {len(df)}")
        st.markdown("---")

        # --- Section 1: Executive Summary (Health) ---
        st.markdown("## 1. EXECUTIVE SUMMARY")
        
        avg_mi = df['MI'].mean()
        avg_cov = df['Doc %'].mean()
        avg_comp = df['Avg Comp'].mean()
        
        # Health Calculation
        comp_score = max(0, 100 - (avg_comp * 5))
        health_score = (avg_mi * 0.5) + (avg_cov * 0.3) + (comp_score * 0.2)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("OVERALL HEALTH", f"{health_score:.1f}")
        c2.metric("MAINTAINABILITY", f"{avg_mi:.1f}")
        c3.metric("DOC COVERAGE", f"{avg_cov:.1f}%")
        c4.metric("AVG COMPLEXITY", f"{avg_comp:.1f}")
        
        st.caption("*Health Score is a weighted aggregate of Maintainability Index (50%), Documentation Coverage (30%), and Inverse Complexity (20%).*")

        # --- Section 2: Complexity Analysis ---
        st.markdown("## 2. COMPLEXITY DISTRIBUTION")
        st.markdown("The following treemap visualizes code complexity relative to file size. **Darker/Redder** areas indicate high complexity density.")
        
        fig_tree = px.treemap(
            df, 
            path=[px.Constant("ROOT"), 'File'], 
            values='LOC',
            color='Max Comp',
            color_continuous_scale='RdYlGn_r',
            title=""
        )
        fig_tree.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': "Times New Roman"},
            margin=dict(t=0, l=0, r=0, b=0)
        )
        st.plotly_chart(fig_tree, use_container_width=True)

        # --- Section 3: Documentation Status ---
        st.markdown("## 3. DOCUMENTATION STATUS")
        
        fig_bar = px.histogram(
            df, 
            x='Doc %', 
            nbins=20,
            labels={'Doc %': 'Coverage Percentage'},
            color_discrete_sequence=['#323639']
        )
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': "Times New Roman"},
            bargap=0.1
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- Section 4: Critical Findings ---
        st.markdown("## 4. CRITICAL FINDINGS (FLAGGED FILES)")
        st.markdown("Files requiring immediate attention due to low maintainability (<65), high complexity (>10), or poor documentation (<50%).")
        
        flagged = df[
            (df['MI'] < 65) | 
            (df['Max Comp'] > 10) | 
            (df['Doc %'] < 50)
        ].sort_values(by='Max Comp', ascending=False)
        
        st.dataframe(
            flagged.style.format("{:.1f}", subset=['MI', 'Avg Comp', 'Doc %']).map(
                lambda x: 'color: #8b0000; font-weight: bold' if x < 65 else '', subset=['MI']
            ).map(
                lambda x: 'color: #8b0000; font-weight: bold' if x > 10 else '', subset=['Max Comp']
            ).map(
                lambda x: 'color: #8b0000; font-weight: bold' if x < 50 else '', subset=['Doc %']
            ),
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("**END OF REPORT**")

else:
    st.markdown("""
    <div style="text-align: center; padding: 5rem;">
        <h1>NO REPORT LOADED</h1>
        <p>Please use the controls on the left to generate a new technical debt audit.</p>
    </div>
    """, unsafe_allow_html=True)

