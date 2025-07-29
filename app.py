import streamlit as st
import pandas as pd
from datetime import datetime
import os
from stock_data import StockDataFetcher
from ai_analysis import AIAnalyzer
from gemini_analysis import GeminiStockAnalyzer
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
        gemini_analyzer = GeminiStockAnalyzer()
        return data_fetcher, ai_analyzer, gemini_analyzer
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        return None, None, None

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

def display_detailed_analysis(stock_data, gemini_analysis=None):
    """Display detailed stock analysis in organized tabs"""
    # Create enhanced tab structure with detailed analysis and summary
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Financial Metrics", 
        "📈 Market Data", 
        "🏢 Company Profile",
        "🤖 Detailed Analysis",
        "📋 Summary & Insights"
    ])
    
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
    
    with tab4:
        st.subheader("🤖 Detailed AI Analysis")
        
        if gemini_analysis:
            # Display detailed analysis from Gemini
            if gemini_analysis.get('detailed_analysis'):
                st.markdown("### 📖 Comprehensive Analysis")
                st.write(gemini_analysis['detailed_analysis'])
            
            # Quarterly Financial Ratios Table
            st.markdown("---")
            st.subheader("📊 Quarterly Financial Ratios (Last 10 Quarters)")
            
            quarterly_data = stock_data.get('quarterly_data')
            if quarterly_data is not None and not quarterly_data.empty and 'Quarter' in quarterly_data.columns:
                # Create a focused table with key financial ratios
                display_columns = ['Quarter', 'EPS', 'ROA (%)', 'Net Margin (%)', 'Current Ratio', 'Debt to Equity', 'PE Ratio']
                available_columns = [col for col in display_columns if col in quarterly_data.columns]
                
                if available_columns:
                    # Format the data for better display
                    formatted_data = quarterly_data[available_columns].copy()
                    
                    # Round numerical values for better display
                    for col in formatted_data.columns:
                        if col != 'Quarter' and pd.api.types.is_numeric_dtype(formatted_data[col]):
                            formatted_data[col] = formatted_data[col].round(2)
                    
                    st.dataframe(
                        formatted_data,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Add trend analysis
                    st.markdown("### 📈 Trend Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'EPS' in quarterly_data.columns:
                            eps_data = quarterly_data['EPS'].dropna()
                            if len(eps_data) >= 2:
                                eps_trend = "Improving" if eps_data.iloc[0] > eps_data.iloc[-1] else "Declining"
                                st.metric("EPS Trend", eps_trend, f"Latest: {eps_data.iloc[0]:.2f}" if not pd.isna(eps_data.iloc[0]) else "N/A")
                        
                        if 'ROA (%)' in quarterly_data.columns:
                            roa_data = quarterly_data['ROA (%)'].dropna()
                            if len(roa_data) >= 2:
                                roa_trend = "Improving" if roa_data.iloc[0] > roa_data.iloc[-1] else "Declining"
                                st.metric("ROA Trend", roa_trend, f"Latest: {roa_data.iloc[0]:.2f}%" if not pd.isna(roa_data.iloc[0]) else "N/A")
                    
                    with col2:
                        if 'Current Ratio' in quarterly_data.columns:
                            cr_data = quarterly_data['Current Ratio'].dropna()
                            if len(cr_data) >= 2:
                                cr_trend = "Improving" if cr_data.iloc[0] > cr_data.iloc[-1] else "Declining"
                                st.metric("Liquidity Trend", cr_trend, f"Latest: {cr_data.iloc[0]:.2f}" if not pd.isna(cr_data.iloc[0]) else "N/A")
                        
                        if 'Debt to Equity' in quarterly_data.columns:
                            de_data = quarterly_data['Debt to Equity'].dropna()
                            if len(de_data) >= 2:
                                de_trend = "Improving" if de_data.iloc[0] < de_data.iloc[-1] else "Worsening"  # Lower is better for D/E
                                st.metric("Leverage Trend", de_trend, f"Latest: {de_data.iloc[0]:.2f}" if not pd.isna(de_data.iloc[0]) else "N/A")
                else:
                    st.info("Quarterly financial ratio data is being processed...")
            else:
                st.info("Quarterly financial data not available for detailed analysis.")
        else:
            st.info("Generating detailed analysis...")
    
    with tab5:
        st.subheader("📋 Investment Summary & Key Insights")
        
        if gemini_analysis:
            # Key Insights Section
            st.markdown("### 🔍 Key Insights")
            insights = gemini_analysis.get('key_insights', [])
            if insights:
                for i, insight in enumerate(insights, 1):
                    st.markdown(f"**{i}.** {insight}")
            else:
                st.info("Key insights are being generated...")
            
            st.markdown("---")
            
            # Investor Implications Section
            st.markdown("### 💼 Implications for Investors")
            implications = gemini_analysis.get('investor_implications', '')
            if implications:
                st.markdown(implications)
            else:
                st.info("Investment implications are being analyzed...")
            
            st.markdown("---")
            
            # Quick Financial Health Summary
            st.markdown("### 📊 Financial Health Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🏛️ Valuation**")
                pe_ratio = stock_data.get('pe_ratio')
                if pe_ratio:
                    if pe_ratio < 15:
                        st.success(f"P/E: {pe_ratio:.1f} (Attractive)")
                    elif pe_ratio > 25:
                        st.warning(f"P/E: {pe_ratio:.1f} (Expensive)")
                    else:
                        st.info(f"P/E: {pe_ratio:.1f} (Fair)")
                else:
                    st.info("P/E: N/A")
            
            with col2:
                st.markdown("**💪 Financial Health**")
                debt_equity = stock_data.get('debt_to_equity')
                if debt_equity:
                    if debt_equity < 0.5:
                        st.success(f"D/E: {debt_equity:.2f} (Strong)")
                    elif debt_equity > 1.0:
                        st.warning(f"D/E: {debt_equity:.2f} (High Risk)")
                    else:
                        st.info(f"D/E: {debt_equity:.2f} (Moderate)")
                else:
                    st.info("D/E: N/A")
            
            with col3:
                st.markdown("**📈 Profitability**")
                roe = stock_data.get('roe')
                if roe:
                    if roe > 15:
                        st.success(f"ROE: {roe:.1f}% (Excellent)")
                    elif roe < 10:
                        st.warning(f"ROE: {roe:.1f}% (Poor)")
                    else:
                        st.info(f"ROE: {roe:.1f}% (Good)")
                else:
                    st.info("ROE: N/A")
            
            # Analysis source info
            st.markdown("---")
            source = gemini_analysis.get('analysis_source', 'unknown')
            if source == 'gemini':
                st.success("✨ Analysis powered by Google Gemini AI")
            else:
                st.info("📊 Analysis based on financial data")
        else:
            st.info("📊 Comprehensive summary is being generated...")
            
            # Show basic metrics while waiting
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", format_currency(stock_data.get('current_price')))
            with col2:
                st.metric("Market Cap", format_currency(stock_data.get('market_cap')))
            with col3:
                st.metric("P/E Ratio", stock_data.get('pe_ratio', 'N/A'))
            with col4:
                st.metric("ROE", format_percentage(stock_data.get('roe')))

def process_stock_query(user_input, data_fetcher, ai_analyzer, gemini_analyzer):
    """Process user stock query and return comprehensive analysis"""
    try:
        # Extract stock symbol using validation function
        stock_symbol = validate_stock_symbol(user_input)
        
        if not stock_symbol:
            return None, None, "Please provide a valid stock symbol (e.g., TCS, RELIANCE, INFY)"
        
        # Fetch stock data
        with st.spinner(f"Fetching comprehensive data for {stock_symbol}..."):
            stock_data = data_fetcher.get_comprehensive_data(stock_symbol)
        
        # Generate Gemini analysis
        with st.spinner("Generating detailed AI analysis with Google Gemini..."):
            gemini_analysis = gemini_analyzer.analyze_stock_comprehensive(stock_data)
        
        # Generate basic analysis as fallback
        with st.spinner("Generating additional insights..."):
            analysis_result = ai_analyzer.analyze_stock(stock_data)
            
            # Handle both string and dict analysis results
            if isinstance(analysis_result, dict):
                basic_analysis = analysis_result.get('analysis', 'Analysis completed successfully')
            else:
                basic_analysis = analysis_result
        
        return stock_data, gemini_analysis, basic_analysis
        
    except Exception as e:
        return None, None, f"Error analyzing stock: {str(e)}"

def display_chat_message(role, content, stock_data=None, gemini_analysis=None):
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
            display_detailed_analysis(stock_data, gemini_analysis)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Initialize services
    data_fetcher, ai_analyzer, gemini_analyzer = initialize_services()
    
    if not data_fetcher or not ai_analyzer or not gemini_analyzer:
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
            message.get("stock_data"),
            message.get("gemini_analysis")
        )
    
    # User input
    user_input = st.chat_input("Ask about any Indian stock (e.g., 'Analyze TCS', 'Tell me about Reliance')")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Process the query
        stock_data, gemini_analysis, basic_analysis = process_stock_query(user_input, data_fetcher, ai_analyzer, gemini_analyzer)
        
        if stock_data and gemini_analysis:
            # Store current data in session state
            st.session_state.current_stock_data = stock_data
            st.session_state.current_analysis = basic_analysis
            st.session_state.current_gemini_analysis = gemini_analysis
            
            # Create response message based on Gemini analysis
            if gemini_analysis.get('key_insights'):
                response_content = f"**Analysis Complete for {stock_data.get('company_name', 'Unknown Company')}**\n\n"
                response_content += "Key highlights:\n"
                for insight in gemini_analysis['key_insights'][:3]:  # Show first 3 insights
                    response_content += f"• {insight}\n"
                response_content += "\nDetailed analysis available in tabs below."
            else:
                response_content = f"**Analysis Complete for {stock_data.get('company_name', 'Unknown Company')}**\n\nComprehensive financial data and analysis available in the tabs below."
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": response_content,
                "stock_data": stock_data,
                "gemini_analysis": gemini_analysis
            })
        else:
            # Add error message to history
            error_message = basic_analysis if basic_analysis else "Error processing stock analysis"
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": error_message
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