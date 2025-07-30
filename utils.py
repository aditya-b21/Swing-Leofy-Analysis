import re
import pandas as pd
from typing import Optional

def validate_stock_symbol(user_input: str) -> Optional[str]:
    """Extract and validate stock symbol from user input"""
    if not user_input:
        return None
    
    # Clean input
    cleaned_input = user_input.strip()
    
    # Common patterns to extract stock symbol
    patterns = [
        r'analyze\s+stock:\s*([A-Za-z]+)',  # "analyze stock: INFY"
        r'analyze\s+([A-Za-z]+)',  # "analyze INFY"
        r'stock:\s*([A-Za-z]+)',  # "stock: INFY"
        r'^([A-Za-z]+)$',  # Just "INFY"
        r'([A-Za-z]+)\s+stock',  # "INFY stock"
        r'([A-Za-z]+)\s+analysis',  # "INFY analysis"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cleaned_input, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper().strip()
            # Validate symbol (basic validation)
            if len(symbol) >= 2 and symbol.isalpha():
                return symbol
    
    # If no pattern matches, check if the entire input could be a symbol
    if cleaned_input.replace(' ', '').isalpha() and len(cleaned_input.replace(' ', '')) <= 10:
        return cleaned_input.replace(' ', '').upper()
    
    return None

def format_currency(amount):
    """Format currency values for display with enhanced validation"""
    if amount is None or pd.isna(amount):
        return "N/A"
    
    try:
        amount = float(amount)
        
        # Handle negative values
        if amount < 0:
            return f"-₹{abs(amount):.2f}"
            
        # Handle very large amounts (> 1 crore)
        if amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.2f} L"
        elif amount >= 1000:
            return f"₹{amount/1000:.2f} K"
        elif amount >= 1:
            return f"₹{amount:.2f}"
        else:
            # For very small amounts
            return f"₹{amount:.4f}"
    except (ValueError, TypeError, OverflowError):
        return "N/A"

def format_percentage(value):
    """Format percentage values for display with enhanced validation"""
    if value is None or pd.isna(value):
        return "N/A"
    
    try:
        percentage = float(value)
        
        # Handle very small percentages
        if abs(percentage) < 0.01 and percentage != 0:
            return f"{percentage:.4f}%"
        else:
            return f"{percentage:.2f}%"
    except (ValueError, TypeError, OverflowError):
        return "N/A"

def format_ratio(value):
    """Format ratio values for display"""
    if value is None or pd.isna(value):
        return "N/A"
    
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "N/A"

def clean_dataframe_for_display(df):
    """Clean DataFrame for better display in Streamlit and avoid Arrow conversion errors"""
    if df is None or df.empty:
        return pd.DataFrame({"Message": ["No data available"]})
    
    # Create a copy to avoid modifying original
    display_df = df.copy()
    
    # Convert problematic columns to strings first to avoid Arrow conversion issues
    for col in display_df.columns:
        if col != 'Quarter' and col != 'Year':  # Keep date columns as-is
            # Convert mixed type columns to string representation
            display_df[col] = display_df[col].astype(str)
            # Replace 'nan', 'None', 'NaN' strings with "N/A"
            display_df[col] = display_df[col].replace(['nan', 'None', 'NaN', '<NA>', 'null'], "N/A")
    
    # Format numeric columns appropriately (after converting to string)
    for col in display_df.columns:
        if col not in ['Quarter', 'Year', 'Message']:
            try:
                # Try to convert back to numeric for formatting
                numeric_series = pd.to_numeric(display_df[col], errors='coerce')
                if not pd.isna(numeric_series).all():  # If column has some numeric values
                    if 'revenue' in col.lower() or 'income' in col.lower() or 'assets' in col.lower() or 'debt' in col.lower():
                        formatted_values = []
                        for x in numeric_series:
                            if pd.notna(x):
                                formatted_values.append(format_currency(x))
                            else:
                                formatted_values.append("N/A")
                        display_df[col] = formatted_values
                    elif 'eps' in col.lower():
                        formatted_values = []
                        for x in numeric_series:
                            if pd.notna(x):
                                formatted_values.append(f"₹{x:.2f}")
                            else:
                                formatted_values.append("N/A")
                        display_df[col] = formatted_values
                    elif '%' in col or 'ratio' in col.lower() or 'margin' in col.lower():
                        formatted_values = []
                        for x in numeric_series:
                            if pd.notna(x):
                                formatted_values.append(format_ratio(x))
                            else:
                                formatted_values.append("N/A")
                        display_df[col] = formatted_values
                    else:
                        formatted_values = []
                        for x in numeric_series:
                            if pd.notna(x):
                                formatted_values.append(f"{x:.2f}")
                            else:
                                formatted_values.append("N/A")
                        display_df[col] = formatted_values
            except Exception:
                # If formatting fails, keep as "N/A" where appropriate
                display_df[col] = display_df[col].replace(['nan', 'None', 'NaN'], "N/A")
    
    return display_df

def get_stock_suggestions():
    """Get common Indian stock suggestions"""
    return [
        "TCS", "INFY", "RELIANCE", "HDFCBANK", "ITC", "SBIN", "BHARTIARTL", 
        "ICICIBANK", "LT", "HCLTECH", "WIPRO", "ONGC", "NTPC", "MARUTI", 
        "BAJFINANCE", "SUNPHARMA", "NESTLEIND", "HINDUNILVR", "ULTRACEMCO", "ADANIPORTS"
    ]

def validate_financial_data(data):
    """Validate financial data for completeness"""
    required_fields = ['symbol', 'company_name', 'current_price']
    
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    return True, "Data validation passed"
