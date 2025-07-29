import streamlit as st
import pandas as pd
from datetime import datetime
import os
from stock_data import StockDataFetcher
from ai_analysis import AIAnalyzer
from utils import format_currency, format_percentage, validate_stock_symbol

# Page configuration
st.set_page_config(
    page_title="InvestIQ - AI Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    .error-message {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
    }
    .success-message {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services with caching
@st.cache_resource
def initialize_services():
    """Initialize data fetcher and AI analyzer with caching"""
    try:
        data_fetcher = StockDataFetcher()
        ai_analyzer = AIAnalyzer()
        return data_fetcher, ai_analyzer
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        return None, None

# Initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_stock_data' not in st.session_state:
        st.session_state.current_stock_data = None
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

def display_stock_overview(stock_data):
    """Display stock overview in a structured format"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Price", 
            format_currency(stock_data.get('current_price')),
            delta=f"{format_percentage(stock_data.get('change_percent'))}%"
        )
    
    with col2:
        st.metric(
            "Market Cap", 
            format_currency(stock_data.get('market_cap'))
        )
    
    with col3:
        st.metric(
            "P/E Ratio", 
            stock_data.get('pe_ratio', 'N/A')
        )
    
    with col4:
        st.metric(
            "52W High/Low", 
            f"{format_currency(stock_data.get('fifty_two_week_high'))} / {format_currency(stock_data.get('fifty_two_week_low'))}"
        )

def display_detailed_analysis(stock_data):
    """Display detailed stock analysis in organized tabs"""
    # Create cleaner tab structure
    tab1, tab2, tab3 = st.tabs(["📊 Financial Metrics", "📈 Market Data", "🏢 Company Profile"])
    
    with tab1:
        st.subheader("📊 Key Financial Ratios")
        
        # Create three columns for better organization
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**💰 Valuation Ratios**")
            valuation_metrics = [
                ("P/E Ratio", stock_data.get('pe_ratio', 'N/A')),
                ("P/B Ratio", stock_data.get('pb_ratio', 'N/A')),
                ("EPS", format_currency(stock_data.get('eps'))),
                ("Book Value", format_currency(stock_data.get('book_value'))),
                ("Price/Sales", stock_data.get('price_to_sales', 'N/A'))
            ]
            for metric, value in valuation_metrics:
                st.metric(metric, value)
        
        with col2:
            st.markdown("**💪 Financial Health**")
            health_metrics = [
                ("Current Ratio", stock_data.get('current_ratio', 'N/A')),
                ("Quick Ratio", stock_data.get('quick_ratio', 'N/A')),
                ("Debt to Equity", stock_data.get('debt_to_equity', 'N/A')),
                ("ROE", format_percentage(stock_data.get('roe'))),
                ("ROA", format_percentage(stock_data.get('roa')))
            ]
            for metric, value in health_metrics:
                st.metric(metric, value)
        
        with col3:
            st.markdown("**📈 Growth & Margins**")
            growth_metrics = [
                ("Revenue Growth", format_percentage(stock_data.get('revenue_growth'))),
                ("Earnings Growth", format_percentage(stock_data.get('earnings_growth'))),
                ("Profit Margins", format_percentage(stock_data.get('profit_margins'))),
                ("Operating Margins", format_percentage(stock_data.get('operating_margins'))),
                ("Dividend Yield", format_percentage(stock_data.get('dividend_yield')))
            ]
            for metric, value in growth_metrics:
                st.metric(metric, value)
        
        # Financial Data Tables
        st.markdown("---")
        st.subheader("📋 Financial Statements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            annual_data = stock_data.get('annual_data')
            if annual_data is not None and not annual_data.empty:
                st.markdown("**Annual Performance (Last 3 Years)**")
                st.dataframe(annual_data.head(3), use_container_width=True)
            else:
                st.info("Annual financial data not available")
        
        with col2:
            quarterly_data = stock_data.get('quarterly_data')
            if quarterly_data is not None and not quarterly_data.empty:
                st.markdown("**Quarterly Performance (Recent)**")
                st.dataframe(quarterly_data.head(4), use_container_width=True)
            else:
                st.info("Quarterly financial data not available")
    
    with tab2:
        st.subheader("📈 Market Performance & Trading Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Price Performance**")
            price_data = [
                ("52-Week High", format_currency(stock_data.get('fifty_two_week_high'))),
                ("52-Week Low", format_currency(stock_data.get('fifty_two_week_low'))),
                ("Average Volume", f"{stock_data.get('average_volume', 'N/A'):,}" if stock_data.get('average_volume') else 'N/A'),
                ("Market Cap", format_currency(stock_data.get('market_cap')))
            ]
            for metric, value in price_data:
                st.metric(metric, value)
            
            # Calculate performance vs 52W high/low
            current_price = stock_data.get('current_price', 0)
            high_52w = stock_data.get('fifty_two_week_high', 1)
            low_52w = stock_data.get('fifty_two_week_low', 1)
            
            if current_price and high_52w and low_52w:
                perf_vs_high = ((current_price / high_52w) - 1) * 100
                perf_vs_low = ((current_price / low_52w) - 1) * 100
                st.metric("Performance vs 52W High", format_percentage(perf_vs_high))
                st.metric("Performance vs 52W Low", format_percentage(perf_vs_low))
        
        with col2:
            st.markdown("**👥 Shareholding Pattern**")
            shareholding_data = [
                ("Promoter Holding", format_percentage(stock_data.get('promoter_holding'))),
                ("FII Holding", format_percentage(stock_data.get('fii_holding'))),
                ("DII Holding", format_percentage(stock_data.get('dii_holding'))),
                ("Retail Holding", format_percentage(stock_data.get('retail_holding')))
            ]
            
            for holder, percentage in shareholding_data:
                st.metric(holder, percentage)
            
            # Additional market data
            st.markdown("**📊 Additional Market Data**")
            additional_data = [
                ("Beta", stock_data.get('beta', 'N/A')),
                ("Float Shares", f"{stock_data.get('float_shares', 'N/A'):,}" if stock_data.get('float_shares') else 'N/A'),
                ("Shares Outstanding", f"{stock_data.get('shares_outstanding', 'N/A'):,}" if stock_data.get('shares_outstanding') else 'N/A')
            ]
            for metric, value in additional_data:
                st.metric(metric, value)
    
    with tab3:
        st.subheader("🏢 Company Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🏭 Basic Information**")
            company_info = [
                ("Company Name", stock_data.get('company_name', 'N/A')),
                ("Stock Symbol", stock_data.get('symbol', 'N/A')),
                ("Sector", stock_data.get('sector', 'N/A')),
                ("Industry", stock_data.get('industry', 'N/A')),
                ("Country", stock_data.get('country', 'India')),
                ("Full-time Employees", f"{stock_data.get('employees', 'N/A'):,}" if stock_data.get('employees') else 'N/A')
            ]
            
            for label, value in company_info:
                st.write(f"**{label}:** {value}")
        
        with col2:
            st.markdown("**🌐 Additional Details**")
            website = stock_data.get('website', 'N/A')
            if website != 'N/A':
                st.write(f"**Website:** [Visit Company Website]({website})")
            else:
                st.write("**Website:** N/A")
            
            last_updated = stock_data.get('last_updated', 'N/A')
            st.write(f"**Data Last Updated:** {last_updated}")
        
        # Business Summary
        business_summary = stock_data.get('business_summary', 'N/A')
        if business_summary != 'N/A' and len(business_summary) > 10:
            st.markdown("---")
            st.subheader("📝 Business Summary")
            st.write(business_summary)
        else:
            st.info("Business summary not available for this company.")

def process_stock_query(user_input, data_fetcher, ai_analyzer):
    """Process user stock query and return analysis"""
    try:
        # Extract stock symbol from user input
        stock_symbol = None
        user_input_upper = user_input.upper()
        
        # Extract stock symbol using validation function
        stock_symbol = validate_stock_symbol(user_input)
        
        if not stock_symbol:
            return None, "Please provide a valid stock symbol (e.g., TCS, RELIANCE, INFY)"
        
        # Fetch stock data
        with st.spinner(f"Fetching data for {stock_symbol}..."):
            stock_data = data_fetcher.get_comprehensive_data(stock_symbol)
        
        # Generate AI analysis
        with st.spinner("Generating AI analysis..."):
            analysis_result = ai_analyzer.analyze_stock(stock_data)
            
            # Handle both string and dict analysis results
            if isinstance(analysis_result, dict):
                analysis = analysis_result.get('analysis', 'Analysis completed successfully')
            else:
                analysis = analysis_result
        
        return stock_data, analysis
        
    except Exception as e:
        return None, f"Error analyzing stock: {str(e)}"

def display_chat_message(role, content, stock_data=None):
    """Display a chat message with proper styling"""
    if role == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message assistant-message"><strong>Assistant:</strong> {content}</div>', unsafe_allow_html=True)
        
        # If stock data is available, display detailed analysis
        if stock_data:
            st.markdown("---")
            display_stock_overview(stock_data)
            st.markdown("---")
            display_detailed_analysis(stock_data)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Initialize services
    data_fetcher, ai_analyzer = initialize_services()
    
    if not data_fetcher or not ai_analyzer:
        st.error("Failed to initialize services. Please check your configuration and try again.")
        return
    
    # App header
    st.markdown('<h1 class="main-header">📈 InvestIQ - AI Stock Analysis</h1>', unsafe_allow_html=True)
    st.markdown("Get comprehensive AI-powered analysis of Indian stocks with real-time data and intelligent insights.")
    
    # Chat interface
    st.subheader("💬 Chat with AI Analyst")
    
    # Display chat history
    for message in st.session_state.chat_history:
        display_chat_message(
            message["role"], 
            message["content"], 
            message.get("stock_data")
        )
    
    # User input
    user_input = st.chat_input("Ask about any Indian stock (e.g., 'Analyze TCS', 'Tell me about Reliance')")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Process the query
        stock_data, analysis = process_stock_query(user_input, data_fetcher, ai_analyzer)
        
        if stock_data:
            # Store current data in session state
            st.session_state.current_stock_data = stock_data
            st.session_state.current_analysis = analysis
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": analysis,
                "stock_data": stock_data
            })
        else:
            # Add error message to history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": analysis  # This contains the error message
            })
        
        # Rerun to update the display
        st.rerun()
    
    # Sidebar with instructions
    with st.sidebar:
        st.header("📋 How to Use")
        st.write("""
        1. **Ask about any Indian stock**: Type the company name or stock symbol
        2. **Get instant analysis**: Our AI provides comprehensive insights
        3. **Explore detailed data**: Check tabs for financial metrics, performance, and company info
        4. **Ask follow-up questions**: Continue the conversation for deeper analysis
        """)
        
        st.header("📈 Sample Queries")
        st.write("""
        - "Analyze TCS"
        - "Tell me about Reliance Industries"
        - "What's the performance of HDFC Bank?"
        - "Should I invest in Infosys?"
        """)
        
        st.header("ℹ️ About")
        st.write("InvestIQ provides AI-powered stock analysis using real-time data from Yahoo Finance and advanced AI models for intelligent insights.")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.current_stock_data = None
            st.session_state.current_analysis = None
            st.rerun()

if __name__ == "__main__":
    main()