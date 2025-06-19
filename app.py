import streamlit as st
import tempfile
import os
from io import StringIO
from typing import Optional

try:
    import streamlit_ace
except ImportError:
    st.error("streamlit-ace not found. Code editor functionality will be disabled.")
    streamlit_ace = None

from rule_manager import RuleManager, get_language_from_extension
from utility_functions import (
    highlight_code, export_to_csv, export_to_json, get_download_link,
    display_statistics, display_results, create_filter_sidebar, filter_results
)

# Set page configuration
st.set_page_config(
    page_title="Code Review Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_LANGUAGES = {
    "Python": [".py"],
    "JavaScript": [".js", ".jsx", ".ts", ".tsx"],
    "Java": [".java"],
    "C++": [".cpp", ".hpp", ".cc", ".h"],
    "Go": [".go"]
}

# CSS styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 600;
    color: #4F8BF9;
    margin-bottom: 1rem;
}
.sub-header {
    font-size: 1.5rem;
    font-weight: 500;
    color: #4F8BF9;
    margin-bottom: 0.5rem;
}
.severity-critical {
    color: #FF0000;
    font-weight: bold;
}
.severity-high {
    color: #FF8C00;
    font-weight: bold;
}
.severity-medium {
    color: #FFC107;
    font-weight: bold;
}
.severity-low {
    color: #2196F3;
    font-weight: bold;
}
.severity-info {
    color: #4CAF50;
    font-weight: bold;
}
.explanation {
    font-style: italic;
    color: #666;
}
.code-block {
    background-color: #f0f2f6;
    padding: 10px;
    border-radius: 5px;
    font-family: monospace;
    white-space: pre-wrap;
}
.fix-suggestion {
    background-color: #e6f7ff;
    padding: 10px;
    border-radius: 5px;
    margin-top: 5px;
    border-left: 3px solid #1890ff;
}
.stat-card {
    padding: 10px;
    border-radius: 5px;
    background-color: #f9f9f9;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "results" not in st.session_state:
    st.session_state.results = []
if "code" not in st.session_state:
    st.session_state.code = ""
if "language" not in st.session_state:
    st.session_state.language = "Python"
if "filename" not in st.session_state:
    st.session_state.filename = None
if "tab_selection" not in st.session_state:
    st.session_state.tab_selection = "Input"

def main():
    # Create rule manager
    rule_manager = RuleManager()
    
    # Header
    st.markdown('<h1 class="main-header">🔍 Code Review Assistant</h1>', unsafe_allow_html=True)
    st.markdown("""
    Automated code review tool that analyzes your code for quality, security, and performance issues without requiring external API keys.
    """)
    
    # Create sidebar filters
    selected_severities, selected_categories = create_filter_sidebar()
    
    # Language selection
    st.sidebar.header("Settings")
    language = st.sidebar.selectbox(
        "Programming Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        index=0,
        key="language_selector"
    )
    
    # Main application tabs
    tabs = ["Input", "Results", "Statistics", "Help"]
    tab_selection = st.session_state.tab_selection
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Input", use_container_width=True, 
                     key="tab_input", 
                     help="Input code for analysis"):
            tab_selection = "Input"
    with col2:
        if st.button("Results", use_container_width=True, 
                     key="tab_results", 
                     help="View detailed analysis results"):
            tab_selection = "Results"
    with col3:
        if st.button("Statistics", use_container_width=True, 
                     key="tab_stats", 
                     help="View charts and statistics"):
            tab_selection = "Statistics"
    with col4:
        if st.button("Help", use_container_width=True, 
                     key="tab_help", 
                     help="Get help using this tool"):
            tab_selection = "Help"
    
    st.session_state.tab_selection = tab_selection
    
    st.markdown("---")
    
    # Input tab
    if tab_selection == "Input":
        st.markdown('<h2 class="sub-header">Code Input</h2>', unsafe_allow_html=True)
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            options=["Upload File", "Enter Code"],
            horizontal=True
        )
        
        code = ""
        filename = None
        
        if input_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload code file", 
                type=[ext[1:] for exts in SUPPORTED_LANGUAGES.values() for ext in exts]
            )
            
            if uploaded_file is not None:
                # Check file size
                if uploaded_file.size > MAX_FILE_SIZE:
                    st.error(f"File size exceeds the maximum limit of {MAX_FILE_SIZE / (1024 * 1024)}MB")
                else:
                    try:
                        # Read and display the uploaded file
                        code = uploaded_file.getvalue().decode('utf-8')
                        filename = uploaded_file.name
                        
                        # Auto-detect language from file extension
                        file_language = get_language_from_extension(filename)
                        if file_language:
                            language = file_language
                            st.success(f"Detected language: {language}")
                        
                        st.markdown('<h3>File Preview</h3>', unsafe_allow_html=True)
                        st.code(code[:1000] + ('...' if len(code) > 1000 else ''), language=language.lower())
                        
                        if len(code) > 1000:
                            st.info(f"Showing preview of first 1000 characters. Full file will be analyzed.")
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
        else:  # Enter Code
            # Use streamlit-ace if available, otherwise fall back to st.text_area
            if streamlit_ace is not None:
                code = streamlit_ace.st_ace(
                    value=st.session_state.code,
                    language=language.lower(),
                    theme="github",
                    height=400,
                    font_size=14,
                    key="ace_editor"
                )
            else:
                code = st.text_area(
                    "Enter your code",
                    height=400,
                    value=st.session_state.code,
                    key="code_input"
                )
        
        # Analyze button
        if st.button("🔍 Analyze Code", type="primary", key="analyze_button"):
            if not code:
                st.error("Please enter or upload code to analyze.")
            else:
                # Store code and language in session state
                st.session_state.code = code
                st.session_state.language = language
                st.session_state.filename = filename
                
                # Analyze the code
                with st.spinner("Analyzing code..."):
                    results = rule_manager.analyze_code(code, filename, language)
                    
                    # Store results in session state
                    st.session_state.results = results
                    
                    # Switch to results tab
                    st.session_state.tab_selection = "Results"
                    st.rerun()
    
    # Results tab
    elif tab_selection == "Results":
        st.markdown('<h2 class="sub-header">Analysis Results</h2>', unsafe_allow_html=True)
        
        results = st.session_state.results
        code = st.session_state.code
        language = st.session_state.language
        
        if not results and not code:
            st.warning("No analysis results available. Please analyze some code first.")
            st.session_state.tab_selection = "Input"
            st.rerun()
        elif not results:
            st.success("No issues found in your code!")
        else:
            # Filter results based on sidebar selections
            filtered_results = filter_results(results, selected_severities, selected_categories)
            
            # Display number of issues
            if len(filtered_results) == 0:
                st.success("No issues found after filtering!")
            else:
                st.info(f"Found {len(filtered_results)} issues in your code.")
            
            # Display detailed results
            display_results(filtered_results, code, language)
            
            # Export options
            st.markdown("---")
            st.markdown("### Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export as CSV", key="export_csv"):
                    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                        csv_path = export_to_csv(filtered_results, tmp.name)
                    
                    st.markdown(get_download_link(csv_path, "Download CSV"), unsafe_allow_html=True)
            
            with col2:
                if st.button("Export as JSON", key="export_json"):
                    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                        json_path = export_to_json(filtered_results, tmp.name)
                    
                    st.markdown(get_download_link(json_path, "Download JSON"), unsafe_allow_html=True)
    
    # Statistics tab
    elif tab_selection == "Statistics":
        st.markdown('<h2 class="sub-header">Analysis Statistics</h2>', unsafe_allow_html=True)
        
        results = st.session_state.results
        
        if not results:
            st.warning("No analysis results available. Please analyze some code first.")
            st.session_state.tab_selection = "Input"
            st.rerun()
        else:
            # Filter results based on sidebar selections
            filtered_results = filter_results(results, selected_severities, selected_categories)
            
            # Display statistics
            display_statistics(filtered_results)
    
    # Help tab
    elif tab_selection == "Help":
        st.markdown('<h2 class="sub-header">Help & Documentation</h2>', unsafe_allow_html=True)
        
        st.markdown("""
        ## How to use the Code Review Assistant

        ### Getting Started
        1. Go to the **Input** tab
        2. Choose whether to upload a file or enter code directly
        3. Select the programming language (if not automatically detected)
        4. Click "Analyze Code" to run the analysis

        ### Understanding Results
        - Issues are grouped by severity (Critical, High, Medium, Low, Info)
        - Click on an issue to see details and suggested fixes
        - Use the sidebar filters to focus on specific severities or categories

        ### Statistics
        - The Statistics tab shows charts and metrics about the issues found
        - Use these insights to focus your improvement efforts

        ### Supported Languages
        - **Python**: PEP 8 violations, security issues, and more
        - **JavaScript**: Common JS pitfalls and best practices
        - **Java**: Exception handling and resource management
        - **C++**: Memory management and RAII patterns
        - **Go**: Go-specific best practices

        ### Rule Categories
        - **Style**: Coding style and convention issues
        - **Security**: Potential vulnerabilities and security risks
        - **Performance**: Inefficient code patterns
        - **Maintainability**: Issues affecting long-term maintenance
        - **Documentation**: Missing or inadequate documentation
        - **Error Handling**: Improper exception/error handling
        """)

# Run the app
if __name__ == "__main__":
    main() 