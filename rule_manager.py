from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set, Callable, Union
import ast
import re
import os

# Define severity levels
class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"

# Define rule categories
class RuleCategory(Enum):
    STYLE = "Style"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    MAINTAINABILITY = "Maintainability"
    DOCUMENTATION = "Documentation"
    ERROR_HANDLING = "Error Handling"

# Base Rule class
class Rule:
    def __init__(
        self, 
        id: str,
        name: str, 
        description: str, 
        category: RuleCategory, 
        severity: Severity,
        language: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.severity = severity
        self.language = language
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Check the code for rule violations.
        
        Args:
            code: The source code to check
            filename: Optional filename to determine language or provide context
            
        Returns:
            List of issues found. Each issue is a dictionary with at least:
            - line: Line number (or range) where the issue is located
            - message: Description of the issue
            - severity: Severity of the issue
            - fix: Optional suggestion for fixing the issue
        """
        raise NotImplementedError("Subclasses must implement check() method")
    
    def __repr__(self):
        return f"<Rule {self.id}: {self.name} ({self.severity.value})>"

# Python-specific rules
class PythonLongFunctionRule(Rule):
    def __init__(self, max_lines: int = 50):
        super().__init__(
            id="PY001",
            name="Long Function",
            description=f"Functions should not exceed {max_lines} lines",
            category=RuleCategory.MAINTAINABILITY,
            severity=Severity.MEDIUM,
            language="Python"
        )
        self.max_lines = max_lines
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > self.max_lines:
                            issues.append({
                                'rule_id': self.id,
                                'rule_name': self.name,
                                'category': self.category.value,
                                'severity': self.severity.value,
                                'line': f"{node.lineno}-{node.end_lineno}",
                                'message': f"Function '{node.name}' is {func_lines} lines long (exceeds {self.max_lines})",
                                'fix': "Consider breaking the function into smaller, more focused functions"
                            })
        except SyntaxError:
            pass  # Skip analysis if there are syntax errors
        
        return issues

class PythonMissingDocstringRule(Rule):
    def __init__(self):
        super().__init__(
            id="PY002",
            name="Missing Docstring",
            description="Public functions, classes, and methods should have docstrings",
            category=RuleCategory.DOCUMENTATION,
            severity=Severity.LOW,
            language="Python"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    # Skip if it's a private function (starts with _)
                    if node.name.startswith('_') and not node.name.startswith('__'):
                        continue
                    
                    # Check if there's a docstring
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        if isinstance(node, ast.ClassDef):
                            element_type = "Class"
                        else:
                            element_type = "Function"
                            
                        issues.append({
                            'rule_id': self.id,
                            'rule_name': self.name,
                            'category': self.category.value,
                            'severity': self.severity.value,
                            'line': node.lineno,
                            'message': f"{element_type} '{node.name}' is missing a docstring",
                            'fix': f'Add a docstring to {element_type.lower()} {node.name}'
                        })
        except SyntaxError:
            pass  # Skip analysis if there are syntax errors
            
        return issues

class PythonUnusedImportsRule(Rule):
    def __init__(self):
        super().__init__(
            id="PY003",
            name="Unused Imports",
            description="Imported modules that are not used should be removed",
            category=RuleCategory.STYLE,
            severity=Severity.LOW,
            language="Python"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Find all imports
            imports = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports[name.name] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    module = node.module
                    for name in node.names:
                        if name.asname:
                            imports[name.asname] = node.lineno
                        else:
                            imports[name.name] = node.lineno
            
            # Find all names used
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Check which imports are not used
            for name, lineno in imports.items():
                name_parts = name.split('.')
                if name_parts[0] not in used_names:
                    issues.append({
                        'rule_id': self.id,
                        'rule_name': self.name,
                        'category': self.category.value,
                        'severity': self.severity.value,
                        'line': lineno,
                        'message': f"Unused import: {name}",
                        'fix': f"Remove the import for '{name}'"
                    })
        except SyntaxError:
            pass  # Skip analysis if there are syntax errors
            
        return issues

class PythonDangerousFunctionRule(Rule):
    def __init__(self):
        super().__init__(
            id="PY004",
            name="Dangerous Function Usage",
            description="Avoid using dangerous functions like eval() or exec()",
            category=RuleCategory.SECURITY,
            severity=Severity.CRITICAL,
            language="Python"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        dangerous_funcs = {
            'eval': "Evaluates a string as Python code, which can be dangerous if the string comes from an untrusted source",
            'exec': "Executes a string as Python code, which can be dangerous if the string comes from an untrusted source",
            '__import__': "Dynamic imports can lead to code injection vulnerabilities"
        }
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in dangerous_funcs:
                        issues.append({
                            'rule_id': self.id,
                            'rule_name': self.name,
                            'category': self.category.value,
                            'severity': self.severity.value,
                            'line': node.lineno,
                            'message': f"Dangerous function usage: {func_name}()",
                            'fix': f"Avoid using {func_name}() as it {dangerous_funcs[func_name]}"
                        })
        except SyntaxError:
            pass  # Skip analysis if there are syntax errors
            
        return issues

class PythonMutableDefaultArgRule(Rule):
    def __init__(self):
        super().__init__(
            id="PY005",
            name="Mutable Default Argument",
            description="Using mutable objects as default arguments can lead to unexpected behavior",
            category=RuleCategory.MAINTAINABILITY,
            severity=Severity.MEDIUM,
            language="Python"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for arg in node.args.defaults:
                        if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                            issues.append({
                                'rule_id': self.id,
                                'rule_name': self.name,
                                'category': self.category.value,
                                'severity': self.severity.value,
                                'line': node.lineno,
                                'message': f"Function '{node.name}' uses a mutable default argument",
                                'fix': "Use None as the default and initialize the mutable object inside the function"
                            })
        except SyntaxError:
            pass  # Skip analysis if there are syntax errors
            
        return issues

# JavaScript-specific rules
class JavaScriptVarUsageRule(Rule):
    def __init__(self):
        super().__init__(
            id="JS001",
            name="Var Usage",
            description="Use let or const instead of var",
            category=RuleCategory.STYLE,
            severity=Severity.LOW,
            language="JavaScript"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        pattern = r'\bvar\s+(\w+)'
        for match in re.finditer(pattern, code):
            var_name = match.group(1)
            line_num = code[:match.start()].count('\n') + 1
            
            issues.append({
                'rule_id': self.id,
                'rule_name': self.name,
                'category': self.category.value,
                'severity': self.severity.value,
                'line': line_num,
                'message': f"Using 'var' for variable '{var_name}' declaration",
                'fix': f"Replace 'var' with 'const' if the variable is not reassigned, otherwise use 'let'"
            })
            
        return issues

class JavaScriptMissingSemicolonRule(Rule):
    def __init__(self):
        super().__init__(
            id="JS002",
            name="Missing Semicolon",
            description="Statements should end with a semicolon",
            category=RuleCategory.STYLE,
            severity=Severity.LOW,
            language="JavaScript"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        # Split code into lines
        lines = code.split('\n')
        
        # Check each line for missing semicolons at the end
        pattern = r'(^|.*?)(let|var|const)\s+[a-zA-Z0-9_$]+(\s*=\s*.+)?\s*$'
        for i, line in enumerate(lines):
            # Skip comments and lines that don't need semicolons
            if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().endswith('*/'):
                continue
                
            # Skip lines ending with semicolons, braces, or if/for/while etc.
            if line.strip().endswith(';') or line.strip().endswith('{') or line.strip().endswith('}'):
                continue
                
            # Skip lines that are likely parts of control structures
            if re.search(r'^\s*(if|for|while|switch|function|class|import|export)\b', line.strip()):
                continue
            
            # Check for variable declarations without semicolons
            if re.match(pattern, line.strip()):
                issues.append({
                    'rule_id': self.id,
                    'rule_name': self.name,
                    'category': self.category.value,
                    'severity': self.severity.value,
                    'line': i + 1,
                    'message': "Missing semicolon at the end of statement",
                    'fix': "Add a semicolon at the end of the statement"
                })
            
        return issues

class JavaScriptEqualityOperatorRule(Rule):
    def __init__(self):
        super().__init__(
            id="JS003",
            name="Equality Operator",
            description="Use === and !== instead of == and !=",
            category=RuleCategory.MAINTAINABILITY,
            severity=Severity.MEDIUM,
            language="JavaScript"
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        patterns = [
            (r'([^=!])==([^=])', '==='),
            (r'([^=!])!=([^=])', '!==')
        ]
        
        for pattern, replacement in patterns:
            for match in re.finditer(pattern, code):
                line_num = code[:match.start()].count('\n') + 1
                
                issues.append({
                    'rule_id': self.id,
                    'rule_name': self.name,
                    'category': self.category.value,
                    'severity': self.severity.value,
                    'line': line_num,
                    'message': f"Use '{replacement}' instead of '{match.group()[1:-1]}' for comparison",
                    'fix': f"Replace '{match.group()[1:-1]}' with '{replacement}'"
                })
                
        return issues

# General rules
class TodoCommentRule(Rule):
    def __init__(self):
        super().__init__(
            id="GEN001",
            name="TODO/FIXME Comment",
            description="Code contains TODO or FIXME comments that should be addressed",
            category=RuleCategory.MAINTAINABILITY,
            severity=Severity.INFO,
            language=None  # Applies to all languages
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        pattern = r'(//|#|/\*|\*)\s*(TODO|FIXME)(\(.*?\)|):?\s*(.*)'
        for match in re.finditer(pattern, code, re.IGNORECASE):
            comment_type = match.group(2).upper()
            comment_text = match.group(4)
            line_num = code[:match.start()].count('\n') + 1
            
            issues.append({
                'rule_id': self.id,
                'rule_name': self.name,
                'category': self.category.value,
                'severity': self.severity.value,
                'line': line_num,
                'message': f"{comment_type} comment: {comment_text}",
                'fix': f"Address the {comment_type} comment or convert it to an issue in your tracking system"
            })
            
        return issues

class MagicNumberRule(Rule):
    def __init__(self):
        super().__init__(
            id="GEN002",
            name="Magic Number",
            description="Avoid using magic numbers, define named constants instead",
            category=RuleCategory.MAINTAINABILITY,
            severity=Severity.LOW,
            language=None  # Applies to all languages
        )
        
    def check(self, code: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        issues = []
        
        # Determine language
        language = None
        if filename:
            language = get_language_from_extension(filename)
        
        # Skip integers 0, 1, -1 as they are commonly used
        if language == "Python":
            # Look for numbers in Python code
            pattern = r'(?<!\w)(?<!\.)\b([2-9]|[1-9][0-9]+)\b(?!\.)'
            for match in re.finditer(pattern, code):
                # Skip if in a comment
                line_start = code.rfind('\n', 0, match.start()) + 1
                line_end = code.find('\n', match.start())
                if line_end == -1:
                    line_end = len(code)
                line = code[line_start:line_end]
                
                # Skip if in a string
                if re.match(r'.*[\'"].*' + re.escape(match.group(0)) + r'.*[\'"].*', line):
                    continue
                
                # Skip if in a comment
                if '#' in line and line.index('#') < (match.start() - line_start):
                    continue
                
                line_num = code[:match.start()].count('\n') + 1
                
                issues.append({
                    'rule_id': self.id,
                    'rule_name': self.name,
                    'category': self.category.value,
                    'severity': self.severity.value,
                    'line': line_num,
                    'message': f"Magic number: {match.group(0)}",
                    'fix': f"Replace {match.group(0)} with a named constant"
                })
        
        elif language == "JavaScript":
            # Look for numbers in JavaScript code
            pattern = r'(?<!\w)(?<!\.)\b([2-9]|[1-9][0-9]+)\b(?!\.)'
            for match in re.finditer(pattern, code):
                # Skip if in a comment or string
                line_start = code.rfind('\n', 0, match.start()) + 1
                line_end = code.find('\n', match.start())
                if line_end == -1:
                    line_end = len(code)
                line = code[line_start:line_end]
                
                # Skip if in a string
                if re.match(r'.*[\'"].*' + re.escape(match.group(0)) + r'.*[\'"].*', line):
                    continue
                
                # Skip if in a comment
                if '//' in line and line.index('//') < (match.start() - line_start):
                    continue
                
                line_num = code[:match.start()].count('\n') + 1
                
                issues.append({
                    'rule_id': self.id,
                    'rule_name': self.name,
                    'category': self.category.value,
                    'severity': self.severity.value,
                    'line': line_num,
                    'message': f"Magic number: {match.group(0)}",
                    'fix': f"Replace {match.group(0)} with a named constant"
                })
            
        return issues

# Rule Manager Class
class RuleManager:
    def __init__(self):
        self.rules = []
        self._register_default_rules()
        
    def _register_default_rules(self):
        # Python rules
        self.register_rule(PythonLongFunctionRule())
        self.register_rule(PythonMissingDocstringRule())
        self.register_rule(PythonUnusedImportsRule())
        self.register_rule(PythonDangerousFunctionRule())
        self.register_rule(PythonMutableDefaultArgRule())
        
        # JavaScript rules
        self.register_rule(JavaScriptVarUsageRule())
        self.register_rule(JavaScriptMissingSemicolonRule())
        self.register_rule(JavaScriptEqualityOperatorRule())
        
        # General rules
        self.register_rule(TodoCommentRule())
        self.register_rule(MagicNumberRule())
        
    def register_rule(self, rule: Rule):
        """Register a rule with the rule manager"""
        self.rules.append(rule)
        
    def get_rules(self, language: Optional[str] = None) -> List[Rule]:
        """Get all rules or filter by language"""
        if language is None:
            return self.rules
        
        return [rule for rule in self.rules if rule.language is None or rule.language == language]
        
    def analyze_code(self, code: str, filename: Optional[str] = None, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze code using all applicable rules
        
        Args:
            code: Source code to analyze
            filename: Optional filename to determine language
            language: Explicitly specify language (overrides filename detection)
            
        Returns:
            List of issues found
        """
        if language is None and filename is not None:
            language = self._get_language_from_extension(filename)
            
        # Get applicable rules
        applicable_rules = self.get_rules(language)
        
        # Apply all rules
        all_issues = []
        for rule in applicable_rules:
            try:
                issues = rule.check(code, filename)
                all_issues.extend(issues)
            except Exception as e:
                # Skip rules that fail
                print(f"Error applying rule {rule.id}: {e}")
                
        # Sort issues by line number
        all_issues.sort(key=lambda x: self._get_line_number(x.get('line', 0)))
        
        return all_issues
    
    def _get_language_from_extension(self, filename: str) -> Optional[str]:
        """Determine programming language from file extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        # Define supported extensions
        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "JavaScript",
            ".tsx": "JavaScript",
            ".java": "Java",
            ".cpp": "C++",
            ".hpp": "C++",
            ".cc": "C++",
            ".h": "C++",
            ".go": "Go"
        }
        
        return extensions.get(ext)
    
    def _get_line_number(self, line_value) -> int:
        """Convert line value to integer for sorting"""
        if isinstance(line_value, int):
            return line_value
        
        # Handle ranges like "10-20"
        if isinstance(line_value, str) and '-' in line_value:
            return int(line_value.split('-')[0])
            
        # Try to convert to int
        try:
            return int(line_value)
        except:
            return 0

# Helper function to get language from extension
def get_language_from_extension(filename: str) -> Optional[str]:
    """Determine programming language from file extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    # Define supported extensions
    extensions = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "JavaScript",
        ".tsx": "JavaScript",
        ".java": "Java",
        ".cpp": "C++",
        ".hpp": "C++",
        ".cc": "C++",
        ".h": "C++",
        ".go": "Go"
    }
    
    return extensions.get(ext) 