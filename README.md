# Rule-Based Code Review Assistant

A lightweight, rule-based code review assistant built with Streamlit that performs automated code review without requiring external APIs or keys.

## Features

- **Production-ready Streamlit web application**
- **Multiple programming language support**: Python, JavaScript, Java, C++, Go
- **Rule-based analysis** without external API dependencies
- **Code quality checking**: Naming conventions, complexity, duplication, documentation
- **Security analysis**: Common vulnerabilities, input validation, authentication issues
- **Performance evaluation**: Inefficient patterns, resource management, database issues
- **Language-specific rules**: PEP 8, JavaScript best practices, Java/C++/Go patterns

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
streamlit run app.py
```

Then visit the provided URL in your web browser (typically http://localhost:8501).

## Application Structure

- **app.py**: Main Streamlit application and UI components
- **rule_manager.py**: Rule engine and implementation of rule classes
- **utility_functions.py**: Utility functions for UI and result visualization

## Rule Categories

- **Style**: Coding style and convention issues
- **Security**: Potential vulnerabilities and security risks
- **Performance**: Inefficient code patterns
- **Maintainability**: Issues affecting long-term maintenance
- **Documentation**: Missing or inadequate documentation
- **Error Handling**: Improper exception/error handling

## Example Rules

### Python
- Long functions (>50 lines)
- Missing docstrings
- Unused imports
- Dangerous function usage (eval/exec)
- Mutable default arguments

### JavaScript
- Var vs let/const usage
- Missing semicolons
- Equality operators (== vs ===)
- Callback nesting depth

### General
- TODO/FIXME comments
- Magic numbers
- Consistent naming

## License

MIT 