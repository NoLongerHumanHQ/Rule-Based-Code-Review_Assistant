# Sample Python code with various issues for testing

import os
import sys
import json
import datetime
import math  # Unused import

# Missing docstring for this function
def calculate_total(values, factor=[], debug=False):
    """Calculate the total of values multiplied by a factor."""
    # Uses mutable default argument
    result = 0
    for i in range(0, len(values)):  # Could use enumerate
        val = values[i]
        # Magic number
        if val > 100:
            # TODO: Handle large values better
            val = 100
        result += val * factor[i % len(factor)]
    
    # Dangerous eval usage
    if debug:
        print("Debug mode:")
        formula = f"result * 2 - 10"
        result = eval(formula)
        
    return result

# Very long function (>50 lines)
def process_data(data):
    if not isinstance(data, dict):
        return None
    
    output = {}
    
    # Line 1 of many
    if "name" in data:
        output["name"] = data["name"].strip()
    else:
        output["name"] = "Unknown"
    
    # Line 2
    if "age" in data:
        try:
            output["age"] = int(data["age"])
        except:  # Bare except
            output["age"] = 0
    else:
        output["age"] = 0
        
    # Line 3
    if "email" in data:
        email = data["email"]
        if "@" in email:
            output["email"] = email
        else:
            output["email"] = ""
    else:
        output["email"] = ""
    
    # Line 4
    if "items" in data and isinstance(data["items"], list):
        output["items"] = []
        for item in data["items"]:
            if isinstance(item, dict) and "id" in item:
                output["items"].append(item)
            
    # Line 5
    if "settings" in data and isinstance(data["settings"], dict):
        output["settings"] = {}
        for key, value in data["settings"].items():
            output["settings"][key] = value
            
    # Line 6
    if "timestamp" in data:
        try:
            ts = float(data["timestamp"])
            output["date"] = datetime.datetime.fromtimestamp(ts)
        except:  # Bare except
            output["date"] = datetime.datetime.now()
    else:
        output["date"] = datetime.datetime.now()
        
    # Line 7-50 (many more similar lines)
    for i in range(7, 51):
        key = f"property_{i}"
        if key in data:
            output[key] = data[key]
        else:
            output[key] = None
            
    return output

def main():
    # Variable naming - not descriptive
    x = [10, 20, 30, 40, 50]
    y = [2, 3]
    
    # Missing semicolon in JavaScript equivalent
    z = calculate_total(x, y, True)
    print(z)
    
    # Inconsistent indentation
    sample_data = {
       "name": "Test User",
       "age": "30",
        "email": "test@example.com",
        "items": [{"id": 1}, {"id": 2}, {}],
       "settings": {"theme": "dark"}
    }
    
    result = process_data(sample_data)
    print(result)

if __name__ == "__main__":
    main() 