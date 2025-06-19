import base64
import csv
import json
import os
import tempfile
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
import streamlit as st

def get_line_from_code(code: str, line_number: int) -> str:
    """Extract a specific line from the code"""
    lines = code.split('\n')
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]
    return ""

def get_code_snippet(code: str, line_number: int, context: int = 2) -> Tuple[int, str]:
    """
    Extract a code snippet with context lines around the specified line
    
    Args:
        code: The source code
        line_number: The line number to focus on
        context: Number of lines before and after to include
        
    Returns:
        Tuple of (start_line, snippet)
    """
    lines = code.split('\n')
    start = max(0, line_number - context - 1)
    end = min(len(lines), line_number + context)
    
    snippet = '\n'.join(lines[start:end])
    return start + 1, snippet

def highlight_code(code: str, language: str) -> str:
    """Highlight code using Pygments"""
    try:
        lexer = get_lexer_for_language(language)
        if not lexer:
            lexer = guess_lexer(code)
        
        formatter = HtmlFormatter(style="colorful", linenos=True, cssclass="source")
        highlighted = pygments.highlight(code, lexer, formatter)
        
        # Include the CSS
        css = formatter.get_style_defs('.source')
        return f"<style>{css}</style>{highlighted}"
    except Exception:
        return f"<pre>{code}</pre>"

def get_lexer_for_language(language: str):
    """Get Pygments lexer for a given language"""
    language_lexer_map = {
        "Python": "python",
        "JavaScript": "javascript",
        "Java": "java",
        "C++": "cpp",
        "Go": "go"
    }
    
    lexer_name = language_lexer_map.get(language)
    if not lexer_name:
        return None
    
    try:
        return get_lexer_by_name(lexer_name)
    except pygments.util.ClassNotFound:
        return None

def export_to_csv(results: List[Dict[str, Any]], filename: str = "code_review_results.csv"):
    """Export results to CSV file"""
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['Rule ID', 'Rule Name', 'Category', 'Severity', 'Line', 'Message', 'Fix Suggestion']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'Rule ID': result.get('rule_id', ''),
                'Rule Name': result.get('rule_name', ''),
                'Category': result.get('category', ''),
                'Severity': result.get('severity', ''),
                'Line': result.get('line', ''),
                'Message': result.get('message', ''),
                'Fix Suggestion': result.get('fix', '')
            })
    
    return filename

def export_to_json(results: List[Dict[str, Any]], filename: str = "code_review_results.json"):
    """Export results to JSON file"""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=2)
    
    return filename

def get_download_link(file_path: str, link_text: str) -> str:
    """Generate a download link for a file"""
    with open(file_path, 'rb') as file:
        data = file.read()
        b64_data = base64.b64encode(data).decode()
        filename = os.path.basename(file_path)
        mime_type = "text/csv" if file_path.endswith('.csv') else "application/json"
        
    href = f'<a href="data:{mime_type};base64,{b64_data}" download="{filename}">{link_text}</a>'
    return href

def display_statistics(results: List[Dict[str, Any]]):
    """Display statistics about the analysis results"""
    if not results:
        st.info("No issues found!")
        return
    
    # Create dataframes for charts
    severity_counts = {}
    category_counts = {}
    
    for result in results:
        severity = result.get('severity', 'Unknown')
        category = result.get('category', 'Unknown')
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
    
    # Create and display severity chart
    severity_df = pd.DataFrame({
        'Severity': list(severity_counts.keys()),
        'Count': list(severity_counts.values())
    })
    
    # Sort severity levels
    severity_order = ['Critical', 'High', 'Medium', 'Low', 'Info']
    severity_df['Severity'] = pd.Categorical(severity_df['Severity'], categories=severity_order, ordered=True)
    severity_df = severity_df.sort_values('Severity')
    
    # Define colors for severity levels
    severity_colors = {
        'Critical': '#FF0000',  # Red
        'High': '#FF8C00',      # Dark Orange
        'Medium': '#FFC107',    # Amber
        'Low': '#2196F3',       # Blue
        'Info': '#4CAF50'       # Green
    }
    
    # Create bar chart for severity
    fig_severity = px.bar(
        severity_df, 
        x='Severity', 
        y='Count',
        title='Issues by Severity',
        color='Severity',
        color_discrete_map=severity_colors
    )
    
    st.plotly_chart(fig_severity)
    
    # Create and display category chart
    category_df = pd.DataFrame({
        'Category': list(category_counts.keys()),
        'Count': list(category_counts.values())
    })
    
    fig_category = px.pie(
        category_df,
        values='Count',
        names='Category',
        title='Issues by Category'
    )
    
    st.plotly_chart(fig_category)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <h3>Total Issues</h3>
            <h2>{}</h2>
        </div>
        """.format(len(results)), unsafe_allow_html=True)
        
    with col2:
        critical_high = severity_counts.get('Critical', 0) + severity_counts.get('High', 0)
        st.markdown("""
        <div class="stat-card">
            <h3>Critical/High Issues</h3>
            <h2>{}</h2>
        </div>
        """.format(critical_high), unsafe_allow_html=True)
        
    with col3:
        most_common_category = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else "None"
        st.markdown("""
        <div class="stat-card">
            <h3>Most Common Category</h3>
            <h2>{}</h2>
        </div>
        """.format(most_common_category), unsafe_allow_html=True)

def display_results(results: List[Dict[str, Any]], code: str, language: str):
    """Display detailed analysis results"""
    if not results:
        st.info("No issues found!")
        return
    
    # Group results by severity
    results_by_severity = {}
    for result in results:
        severity = result.get('severity', 'Unknown')
        if severity not in results_by_severity:
            results_by_severity[severity] = []
        results_by_severity[severity].append(result)
    
    # Sort severities in order of importance
    severity_order = ['Critical', 'High', 'Medium', 'Low', 'Info']
    
    # Display results for each severity
    for severity in severity_order:
        if severity in results_by_severity:
            severity_class = f"severity-{severity.lower()}"
            
            st.markdown(f"""
            <h3 class="{severity_class}">{severity} Issues ({len(results_by_severity[severity])})</h3>
            """, unsafe_allow_html=True)
            
            for result in results_by_severity[severity]:
                with st.expander(f"{result.get('rule_name', 'Issue')} - Line {result.get('line', 'Unknown')}"):
                    st.markdown(f"**{result.get('message', '')}**")
                    st.markdown(f"**Rule ID:** {result.get('rule_id', '')}")
                    st.markdown(f"**Category:** {result.get('category', '')}")
                    
                    # Get code snippet
                    try:
                        line_num = result.get('line', 0)
                        if isinstance(line_num, str) and '-' in line_num:
                            line_num = int(line_num.split('-')[0])
                        else:
                            line_num = int(line_num)
                            
                        start_line, snippet = get_code_snippet(code, line_num, context=2)
                        st.markdown("**Code:**")
                        st.code(snippet, language=language.lower())
                    except:
                        pass
                    
                    # Display fix suggestion if available
                    if result.get('fix'):
                        st.markdown("""
                        <div class="fix-suggestion">
                            <strong>Suggested Fix:</strong><br>
                            {0}
                        </div>
                        """.format(result.get('fix')), unsafe_allow_html=True)

def create_filter_sidebar():
    """Create filter options in the sidebar"""
    st.sidebar.header("Filter Options")
    
    # Severity filters
    st.sidebar.subheader("Severity")
    severity_options = {
        'Critical': True,
        'High': True,
        'Medium': True,
        'Low': True,
        'Info': True
    }
    
    selected_severities = {}
    for severity, default in severity_options.items():
        selected_severities[severity] = st.sidebar.checkbox(severity, value=default)
    
    # Category filters
    st.sidebar.subheader("Categories")
    category_options = {
        'Style': True,
        'Security': True,
        'Performance': True,
        'Maintainability': True,
        'Documentation': True,
        'Error Handling': True
    }
    
    selected_categories = {}
    for category, default in category_options.items():
        selected_categories[category] = st.sidebar.checkbox(category, value=default)
    
    return selected_severities, selected_categories

def filter_results(results: List[Dict[str, Any]], selected_severities: Dict[str, bool], selected_categories: Dict[str, bool]) -> List[Dict[str, Any]]:
    """Filter results based on selected severities and categories"""
    filtered = []
    
    for result in results:
        severity = result.get('severity', 'Unknown')
        category = result.get('category', 'Unknown')
        
        if (severity in selected_severities and selected_severities[severity] and 
            category in selected_categories and selected_categories[category]):
            filtered.append(result)
    
    return filtered 