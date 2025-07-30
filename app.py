import streamlit as st
import pandas as pd
from datetime import datetime
import os
from stock_data import StockDataFetcher
from ai_analysis import AIAnalyzer
from gemini_analysis import GeminiStockAnalyzer
from utils import format_currency, format_percentage, validate_stock_symbol, clean_dataframe_for_display

# Page configuration
st.set_page_config(
    page_title="InvestIQ - AI Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling with dark mode support
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
        color: var(--text-color);
    }
    .user-message {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #2196f3;
        color: #1565c0;
    }
    .assistant-message {
        background: linear-gradient(135deg, #f1f8e9 0%, #dcedc8 100%);
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
    .metric-card {
        background: var(--background-color, rgba(255, 255, 255, 0.95));
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid var(--border-color, #e0e0e0);
        margin: 0.5rem 0;
        color: var(--text-color, #333);
    }
    .error-message {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        color: #c62828;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f44336;
    }
    .success-message {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        color: #2e7d32;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .chat-message {
            color: #ffffff;
        }
        .user-message {
            background: linear-gradient(135deg, #1a237e 0%, #303f9f 100%);
            color: #e3f2fd;
        }
        .assistant-message {
            background: linear-gradient(135deg, #1b5e20 0%, #388e3c 100%);
            color: #e8f5e8;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    }
    
    /* Override Streamlit's default dark mode styles */
    [data-testid="stChatMessage"] {
        background: transparent !important;
    }
    
    [data-testid="stChatMessage"] > div {
        background: transparent !important;
        color: inherit !important;
    }
    
    /* Ensure text is visible in all containers */
    .stContainer, .element-container {
        color: var(--text-color) !important;
    }
    
    /* Fix white text on white background issues */
    .stMarkdown, .stText, p, span, div {
        color: inherit !important;
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

def display_company_header(stock_data):
    """Display professional company header like reference image"""
    company_name = stock_data.get('company_name', 'Unknown Company')
    current_price = stock_data.get('current_price', 0)
    change_percent = stock_data.get('change_percent', 0)
    symbol = stock_data.get('symbol', 'N/A')
    sector = stock_data.get('sector', 'N/A')
    industry = stock_data.get('industry', 'N/A')
    
    # Main company header with gradient background
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <h2 style="margin: 0; font-size: 28px; font-weight: 600; color: white;">{company_name}</h2>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
            <div>
                <p style="margin: 0; font-size: 16px; opacity: 0.9; color: white;">Symbol: <strong>{symbol}</strong></p>
                <p style="margin: 0; font-size: 14px; opacity: 0.8; color: white;">Industry: {industry}</p>
                <p style="margin: 0; font-size: 14px; opacity: 0.8; color: white;">Sector: {sector}</p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; font-size: 32px; font-weight: 700; color: white;">{format_currency(current_price)}</p>
                <p style="margin: 0; font-size: 16px; color: {'#4CAF50' if change_percent >= 0 else '#f44336'};">
                    {'▲' if change_percent >= 0 else '▼'} {abs(change_percent):.2f}%
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_dashboard_overview(stock_data):
    """Display professional dashboard overview with key metrics"""
    
    # Quick Financial Analysis - 6 column layout like reference
    st.markdown("### Quick Financial Analysis")
    st.markdown("*Latest Data*")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # Row 1: Core metrics
    with col1:
        roe = stock_data.get('roe', 0)
        roe_color = "#4CAF50" if roe and roe > 15 else "#FF9800" if roe and roe > 10 else "#f44336"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {roe_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">ROE (%)</div>
            <div style="color: #333; font-size: 20px; font-weight: 600;">{'%.2f' % roe if roe else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        roce = stock_data.get('roce', 0)
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2196F3;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">ROCE (%)</div>
            <div style="color: #333; font-size: 20px; font-weight: 600;">{'%.2f' % roce if roce else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        eps = stock_data.get('eps', 0)
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #9C27B0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">EPS (₹)</div>
            <div style="color: #333; font-size: 20px; font-weight: 600;">{'%.2f' % eps if eps else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        debt_equity = stock_data.get('debt_to_equity', 0)
        de_color = "#4CAF50" if debt_equity and debt_equity < 0.5 else "#FF9800" if debt_equity and debt_equity < 1.0 else "#f44336"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {de_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Debt/Equity</div>
            <div style="color: #333; font-size: 20px; font-weight: 600;">{'%.2f' % debt_equity if debt_equity else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        current_ratio = stock_data.get('current_ratio', 0)
        cr_color = "#4CAF50" if current_ratio and current_ratio > 1.5 else "#FF9800" if current_ratio and current_ratio > 1.0 else "#f44336"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {cr_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Current Ratio</div>
            <div style="color: #333; font-size: 20px; font-weight: 600;">{'%.2f' % current_ratio if current_ratio else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        net_sales_growth = stock_data.get('revenue_growth', 0)
        growth_color = "#4CAF50" if net_sales_growth and net_sales_growth > 0 else "#f44336"
        st.markdown(f"""
        <div style="
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {growth_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        ">
            <div style="color: #666; font-size: 12px; margin-bottom: 5px;">Net Sales Growth (%)</div>
            <div style="color: #333; font-size: 20px; font-weight: 600;">{'%.2f' % net_sales_growth if net_sales_growth else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)

def display_shareholding_pattern(stock_data):
    """Display shareholding pattern like reference image"""
    st.markdown("### Shareholding Pattern")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create pie chart data for shareholding
        promoter = stock_data.get('promoter_holding', 0)
        institutional = stock_data.get('institutional_holding', 0)
        public = 100 - promoter - institutional if promoter and institutional else 0
        
        # Display pie chart visualization using text (since we can't use real charts)
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        ">
            <div style="text-align: center; margin-bottom: 15px;">
                <div style="
                    width: 120px; 
                    height: 120px; 
                    border-radius: 50%; 
                    background: conic-gradient(
                        #3f51b5 0deg {}deg,
                        #4caf50 {}deg {}deg,
                        #ff9800 {}deg 360deg
                    );
                    margin: 0 auto;
                "></div>
            </div>
            <div style="font-size: 12px; color: inherit;">
                <div style="margin: 5px 0;"><span style="color: #3f51b5;">■</span> Promoter</div>
                <div style="margin: 5px 0;"><span style="color: #4caf50;">■</span> Institutional</div>
                <div style="margin: 5px 0;"><span style="color: #ff9800;">■</span> Public</div>
            </div>
        </div>
        """.format(
            promoter * 3.6,  # Convert percentage to degrees
            promoter * 3.6,
            (promoter + institutional) * 3.6,
            (promoter + institutional) * 3.6
        ), unsafe_allow_html=True)
    
    with col2:
        # Display detailed shareholding metrics
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown(f"""
            <div style="
                background: rgba(63, 81, 181, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #3f51b5;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">Promoter (%)</div>
                <div style="color: inherit; font-size: 20px; font-weight: 600;">{'%.2f' % promoter if promoter else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_b:
            st.markdown(f"""
            <div style="
                background: rgba(76, 175, 80, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #4caf50;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">FII (%)</div>
                <div style="color: inherit; font-size: 20px; font-weight: 600;">{'%.2f' % stock_data.get('fii_holding', 0) if stock_data.get('fii_holding') else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_c:
            st.markdown(f"""
            <div style="
                background: rgba(255, 152, 0, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #ff9800;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">DII (%)</div>
                <div style="color: inherit; font-size: 20px; font-weight: 600;">{'%.2f' % stock_data.get('dii_holding', 0) if stock_data.get('dii_holding') else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)

def display_ai_summary_tab(stock_data, gemini_analysis=None):
    """Display comprehensive AI Summary with all requested features"""
    st.markdown("# 🤖 AI Investment Summary & Analysis")
    
    company_name = stock_data.get('company_name', 'Unknown Company')
    current_price = stock_data.get('current_price', 0)
    
    # Create a container for the summary that can be saved as image
    summary_container = st.container()
    
    with summary_container:
        # Header section with key company info
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h2 style="margin: 0; color: white;">{company_name}</h2>
            <h3 style="margin: 5px 0; color: #f0f0f0;">Current Price: ₹{current_price:,.2f}</h3>
            <p style="margin: 0; color: #e0e0e0;">AI-Powered Investment Analysis Report</p>
        </div>
        """, unsafe_allow_html=True)
        
        if gemini_analysis:
            # 1. Implications for Investors
            st.markdown("## 💼 Investment Implications")
            implications = gemini_analysis.get('investor_implications', '')
            if implications:
                st.markdown(f"""
                <div style="
                    background: rgba(72, 187, 120, 0.1);
                    padding: 20px;
                    border-left: 4px solid #28a745;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    color: inherit;
                ">
                    <div style="color: inherit; line-height: 1.6;">{implications}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Investment implications are being analyzed...")
            
            # 2. Key Insights
            st.markdown("## 🔍 Key Investment Insights")
            insights = gemini_analysis.get('key_insights', [])
            if insights:
                for i, insight in enumerate(insights, 1):
                    st.markdown(f"""
                    <div style="
                        background: rgba(0, 123, 255, 0.1);
                        padding: 15px;
                        margin: 10px 0;
                        border-left: 4px solid #007bff;
                        border-radius: 5px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        color: inherit;
                    ">
                        <div style="color: inherit;"><strong>Insight {i}:</strong> {insight}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Key insights are being generated...")
        
        # 3. Key Metrics for the Stock
        st.markdown("## 📊 Key Financial Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pe_ratio = stock_data.get('pe_ratio', 0)
            pe_color = "#4CAF50" if pe_ratio and pe_ratio < 25 else "#FF9800" if pe_ratio and pe_ratio < 35 else "#f44336"
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {pe_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">P/E Ratio</div>
                <div style="color: inherit; font-size: 24px; font-weight: 600;">{'%.2f' % pe_ratio if pe_ratio else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            debt_equity = stock_data.get('debt_to_equity', 0)
            de_color = "#4CAF50" if debt_equity and debt_equity < 0.5 else "#FF9800" if debt_equity and debt_equity < 1.0 else "#f44336"
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {de_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">Debt/Equity</div>
                <div style="color: inherit; font-size: 24px; font-weight: 600;">{'%.2f' % debt_equity if debt_equity else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            roe = stock_data.get('roe', 0)
            roe_color = "#4CAF50" if roe and roe > 15 else "#FF9800" if roe and roe > 10 else "#f44336"
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {roe_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">ROE (%)</div>
                <div style="color: inherit; font-size: 24px; font-weight: 600;">{'%.2f' % (roe * 100) if roe else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            revenue_growth = stock_data.get('revenue_growth', 0)
            growth_color = "#4CAF50" if revenue_growth and revenue_growth > 10 else "#FF9800" if revenue_growth and revenue_growth > 0 else "#f44336"
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid {growth_color};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="color: inherit; opacity: 0.8; font-size: 12px; margin-bottom: 5px;">Revenue Growth (%)</div>
                <div style="color: inherit; font-size: 24px; font-weight: 600;">{'%.2f' % (revenue_growth * 100) if revenue_growth else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Investment Outlook
        st.markdown("## 🎯 Investment Outlook")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Short-term Outlook (3-6 months)")
            
            # Calculate short-term sentiment based on key metrics
            short_term_factors = []
            current_ratio = stock_data.get('current_ratio', 0)
            if current_ratio and current_ratio > 1.5:
                short_term_factors.append("✅ Strong liquidity position")
            elif current_ratio and current_ratio > 1.0:
                short_term_factors.append("⚠️ Adequate liquidity")
            else:
                short_term_factors.append("❌ Liquidity concerns")
            
            profit_margin = stock_data.get('profit_margins', 0)
            if profit_margin and profit_margin > 0.15:
                short_term_factors.append("✅ Strong profitability")
            elif profit_margin and profit_margin > 0.05:
                short_term_factors.append("⚠️ Moderate profitability")
            else:
                short_term_factors.append("❌ Low profitability")
            
            if pe_ratio and pe_ratio < 25:
                short_term_factors.append("✅ Reasonable valuation")
            elif pe_ratio and pe_ratio < 35:
                short_term_factors.append("⚠️ Moderate valuation")
            else:
                short_term_factors.append("❌ High valuation")
            
            for factor in short_term_factors:
                st.markdown(f"• {factor}")
        
        with col2:
            st.markdown("### 🚀 Long-term Outlook (1-3 years)")
            
            # Calculate long-term sentiment
            long_term_factors = []
            if revenue_growth and revenue_growth > 0.1:
                long_term_factors.append("✅ Strong revenue growth trend")
            elif revenue_growth and revenue_growth > 0:
                long_term_factors.append("⚠️ Moderate growth potential")
            else:
                long_term_factors.append("❌ Growth challenges")
            
            if debt_equity and debt_equity < 0.5:
                long_term_factors.append("✅ Conservative debt management")
            elif debt_equity and debt_equity < 1.0:
                long_term_factors.append("⚠️ Manageable debt levels")
            else:
                long_term_factors.append("❌ High debt burden")
            
            if roe and roe > 0.15:
                long_term_factors.append("✅ Excellent return on equity")
            elif roe and roe > 0.10:
                long_term_factors.append("⚠️ Good return on equity")
            else:
                long_term_factors.append("❌ Poor return on equity")
            
            for factor in long_term_factors:
                st.markdown(f"• {factor}")
        
        # Comprehensive Summary
        st.markdown("## 📋 Comprehensive Analysis Summary")
        
        if gemini_analysis:
            detailed_analysis = gemini_analysis.get('detailed_analysis', '')
            if detailed_analysis:
                st.markdown(f"""
                <div style="
                    background: rgba(108, 117, 125, 0.1);
                    padding: 25px;
                    border-radius: 10px;
                    margin: 20px 0;
                    border-left: 4px solid #6c757d;
                    backdrop-filter: blur(10px);
                ">
                    <h4 style="color: inherit; margin-top: 0; opacity: 0.9;">AI-Generated Investment Summary:</h4>
                    <p style="color: inherit; line-height: 1.6; margin-bottom: 0; opacity: 0.8;">{detailed_analysis}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Detailed analysis is being generated...")
        
        # Risk Assessment
        st.markdown("## ⚠️ Risk Assessment")
        
        risk_factors = []
        risk_level = "Low"
        
        if debt_equity and debt_equity > 1.0:
            risk_factors.append("High debt-to-equity ratio indicates financial leverage risk")
            risk_level = "High"
        
        if pe_ratio and pe_ratio > 35:
            risk_factors.append("High P/E ratio suggests overvaluation risk")
            risk_level = "Medium" if risk_level == "Low" else "High"
        
        if current_ratio and current_ratio < 1.0:
            risk_factors.append("Low current ratio indicates liquidity risk")
            risk_level = "High"
        
        if profit_margin and profit_margin < 0.05:
            risk_factors.append("Low profit margins indicate profitability challenges")
            risk_level = "Medium" if risk_level == "Low" else "High"
        
        if not risk_factors:
            risk_factors.append("No significant financial risks identified in current metrics")
        
        risk_color = "#4CAF50" if risk_level == "Low" else "#FF9800" if risk_level == "Medium" else "#f44336"
        
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid {risk_color};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
            backdrop-filter: blur(10px);
        ">
            <h4 style="color: {risk_color}; margin-top: 0;">Risk Level: {risk_level}</h4>
            {"".join([f"<p style='margin: 5px 0; color: inherit; opacity: 0.8;'>• {factor}</p>" for factor in risk_factors])}
        </div>
        """, unsafe_allow_html=True)
    
    # Save as Image functionality
    st.markdown("---")
    st.markdown("## 💾 Save Summary as Image")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📸 Save Summary as Image", key="save_summary_image", use_container_width=True):
            # Get variables safely
            implications_text = gemini_analysis.get('investor_implications', '') if gemini_analysis else 'Analysis in progress...'
            insights_list = gemini_analysis.get('key_insights', []) if gemini_analysis else []
            detailed_analysis_text = gemini_analysis.get('detailed_analysis', '') if gemini_analysis else 'Detailed analysis is being generated...'
            
            # Create a comprehensive text summary for download
            summary_text = f"""
AI INVESTMENT SUMMARY REPORT
{'='*50}

Company: {company_name}
Current Price: ₹{current_price:,.2f}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INVESTMENT IMPLICATIONS:
{implications_text}

KEY INSIGHTS:
"""
            
            if insights_list:
                for i, insight in enumerate(insights_list, 1):
                    summary_text += f"{i}. {insight}\n"
            else:
                summary_text += "Insights are being generated...\n"
            
            summary_text += f"""

KEY FINANCIAL METRICS:
- P/E Ratio: {'%.2f' % pe_ratio if pe_ratio else 'N/A'}
- Debt/Equity: {'%.2f' % debt_equity if debt_equity else 'N/A'}
- ROE: {'%.2f%%' % (roe * 100) if roe else 'N/A'}
- Revenue Growth: {'%.2f%%' % (revenue_growth * 100) if revenue_growth else 'N/A'}

INVESTMENT OUTLOOK:
Short-term (3-6 months): {"Positive" if len([f for f in short_term_factors if "✅" in f]) >= 2 else "Mixed" if len([f for f in short_term_factors if "✅" in f]) >= 1 else "Cautious"}
Long-term (1-3 years): {"Positive" if len([f for f in long_term_factors if "✅" in f]) >= 2 else "Mixed" if len([f for f in long_term_factors if "✅" in f]) >= 1 else "Cautious"}

COMPREHENSIVE ANALYSIS:
{detailed_analysis_text}

RISK ASSESSMENT:
Risk Level: {risk_level}
"""
            for factor in risk_factors:
                summary_text += f"• {factor}\n"
            
            summary_text += f"""

{'='*50}
Generated by InvestIQ AI Stock Analysis Platform
"""
            
            # Provide download button
            st.download_button(
                label="📋 Download Complete Summary Report",
                data=summary_text,
                file_name=f"{company_name.replace(' ', '_')}_AI_Summary_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            st.success("📊 Summary report ready for download! Click the button above to save the complete analysis.")
            st.info("💡 Tip: You can also take a screenshot of this tab to save the visual summary as an image.")

def display_detailed_analysis(stock_data, gemini_analysis=None):
    """Display detailed stock analysis in organized tabs"""
    # Create professional tab structure like reference image
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Overview", 
        "Chart", 
        "Analysis",
        "P&L",
        "Balance Sheet",
        "Cash Flow", 
        "Investors",
        "🤖 AI Summary"
    ])
    
    with tab1:
        # Company Overview tab like reference image
        st.markdown("#### Company Details")
        
        # Company info in structured format like reference
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Scrip Name:** " + (stock_data.get('symbol', 'N/A')))
            st.markdown("**Chairman:** " + (stock_data.get('chairman', 'N/A')))
            st.markdown("**Status:** Active")
        
        with col2:
            st.markdown("**Industry:** " + (stock_data.get('industry', 'N/A')))
            st.markdown("**Managing Director:** " + (stock_data.get('managing_director', 'N/A')))
            st.markdown("**Face Value (₹):** " + str(stock_data.get('face_value', 'N/A')))
        
        # Display the shareholding pattern and financial analysis that's already above
        st.markdown("---")
        
        # Key Financial Ratios
        st.subheader("Key Financial Ratios")
        
        # Create three columns for better organization  
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Valuation Ratios**")
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
            st.markdown("**Financial Health**")
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
                # Clean the dataframe to avoid Arrow conversion errors
                clean_annual = clean_dataframe_for_display(annual_data.head(3))
                st.dataframe(clean_annual, use_container_width=True, hide_index=True)
            else:
                st.info("Annual financial data not available")
        
        with col2:
            quarterly_data = stock_data.get('quarterly_data')
            if quarterly_data is not None and not quarterly_data.empty:
                st.markdown("**Quarterly Performance (Recent)**")
                # Clean the dataframe to avoid Arrow conversion errors
                clean_quarterly = clean_dataframe_for_display(quarterly_data.head(4))
                st.dataframe(clean_quarterly, use_container_width=True, hide_index=True)
            else:
                st.info("Quarterly financial data not available")
    
    with tab2:
        # Enhanced Chart tab with comprehensive price and performance metrics
        st.subheader("📈 Price Performance & Trading Charts")
        
        # Display historical data if available
        historical_data = stock_data.get('historical_data')
        if historical_data is not None and not historical_data.empty:
            # Enhanced price metrics display
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Current Price", format_currency(stock_data.get('current_price')))
            with col2:
                st.metric("52W High", format_currency(stock_data.get('fifty_two_week_high')))
            with col3:
                st.metric("52W Low", format_currency(stock_data.get('fifty_two_week_low')))
            with col4:
                st.metric("Day High", format_currency(stock_data.get('day_high')))
            with col5:
                st.metric("Day Low", format_currency(stock_data.get('day_low')))
            
            st.markdown("---")
            
            # Price Performance Analysis
            current_price = stock_data.get('current_price', 0)
            high_52w = stock_data.get('fifty_two_week_high', 1)
            low_52w = stock_data.get('fifty_two_week_low', 1)
            
            col_a, col_b, col_c, col_d = st.columns(4)
            
            if current_price and high_52w and low_52w:
                perf_vs_high = ((current_price / high_52w) - 1) * 100
                perf_vs_low = ((current_price / low_52w) - 1) * 100
                
                with col_a:
                    st.metric("vs 52W High", f"{perf_vs_high:.2f}%", 
                             delta=f"{perf_vs_high:.2f}%" if perf_vs_high >= 0 else f"{perf_vs_high:.2f}%")
                with col_b:
                    st.metric("vs 52W Low", f"{perf_vs_low:.2f}%",
                             delta=f"{perf_vs_low:.2f}%" if perf_vs_low >= 0 else f"{perf_vs_low:.2f}%")
            
            with col_c:
                st.metric("Average Volume", f"{stock_data.get('average_volume', 0):,}" if stock_data.get('average_volume') else 'N/A')
            with col_d:
                st.metric("Beta", f"{stock_data.get('beta', 'N/A')}")
            
            st.markdown("---")
            
            # Chart visualization using Streamlit's built-in chart
            st.markdown("**📊 Price Chart (Last 6 Months)**")
            
            # Get last 6 months of data for chart
            chart_data = historical_data.tail(180) if len(historical_data) > 180 else historical_data
            
            if not chart_data.empty and 'Close' in chart_data.columns:
                # Create a simple line chart
                st.line_chart(chart_data['Close'])
                
                st.markdown("**📊 Volume Chart (Last 6 Months)**")
                if 'Volume' in chart_data.columns:
                    st.bar_chart(chart_data['Volume'])
            
            st.markdown("---")
            st.markdown("**Historical Price Data (Last 30 Days)**")
            
            # Show recent historical data in table format
            recent_data = historical_data.tail(30) if len(historical_data) > 30 else historical_data
            if not recent_data.empty:
                # Format the data for better display
                display_data = recent_data[['Close', 'Volume', 'High', 'Low']].copy()
                display_data['Close'] = display_data['Close'].round(2)
                display_data['High'] = display_data['High'].round(2) 
                display_data['Low'] = display_data['Low'].round(2)
                display_data['Volume'] = display_data['Volume'].astype(int)
                
                # Add date column
                display_data['Date'] = display_data.index.strftime('%Y-%m-%d')
                display_data = display_data[['Date', 'Close', 'High', 'Low', 'Volume']]
                
                st.dataframe(display_data, use_container_width=True, hide_index=True)
        else:
            st.info("Chart data will be displayed here when available")
    
    with tab3:
        # Analysis tab with AI insights and financial analysis
        st.subheader("Detailed Financial Analysis")
        
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
        # P&L Statement tab
        st.subheader("Profit & Loss Statement")
        
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
            # Show P&L data from financial statements
            annual_data = stock_data.get('annual_data')
            if annual_data is not None and not annual_data.empty:
                st.markdown("**Annual Profit & Loss Statement**")
                st.dataframe(annual_data, use_container_width=True, hide_index=True)
            else:
                st.info("P&L statement data not available")
    
    with tab5:
        # Balance Sheet tab
        st.subheader("Balance Sheet Statement")
        
        balance_sheet_data = stock_data.get('balance_sheet_data')
        if balance_sheet_data is not None and not balance_sheet_data.empty:
            st.dataframe(balance_sheet_data, use_container_width=True, hide_index=True)
        else:
            st.info("Balance sheet data not available")
    
    with tab6:
        # Cash Flow tab
        st.subheader("Cash Flow Statement")
        
        cash_flow_data = stock_data.get('cash_flow_data')
        if cash_flow_data is not None and not cash_flow_data.empty:
            st.dataframe(cash_flow_data, use_container_width=True, hide_index=True)
        else:
            st.info("Cash flow statement data not available")
    
    with tab7:
        # Investors tab - showing detailed shareholding and AI analysis
        st.subheader("Investor Information & AI Analysis")
        
        # Display shareholding pattern
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Shareholding Pattern**")
            shareholding_data = [
                ("Promoter Holding", format_percentage(stock_data.get('promoter_holding'))),
                ("FII Holding", format_percentage(stock_data.get('fii_holding'))),
                ("DII Holding", format_percentage(stock_data.get('dii_holding'))),
                ("Public Holding", format_percentage(stock_data.get('public_holding'))),
                ("Retail Holding", format_percentage(stock_data.get('retail_holding')))
            ]
            
            for holder, percentage in shareholding_data:
                st.metric(holder, percentage)
        
        with col2:
            st.markdown("**Market Information**")
            market_info = [
                ("Market Cap", format_currency(stock_data.get('market_cap'))),
                ("Float Shares", f"{stock_data.get('float_shares', 'N/A'):,}" if stock_data.get('float_shares') else 'N/A'),
                ("Shares Outstanding", f"{stock_data.get('shares_outstanding', 'N/A'):,}" if stock_data.get('shares_outstanding') else 'N/A'),
                ("Beta", stock_data.get('beta', 'N/A'))
            ]
            
            for metric, value in market_info:
                st.metric(metric, value)
        
        # AI Analysis Section
        if gemini_analysis:
            st.markdown("---")
            st.markdown("### AI Investment Analysis")
            
            # Key Insights Section
            insights = gemini_analysis.get('key_insights', [])
            if insights:
                st.markdown("**Key Investment Insights:**")
                for i, insight in enumerate(insights, 1):
                    st.markdown(f"{i}. {insight}")
            
            # Investor Implications Section
            implications = gemini_analysis.get('investor_implications', '')
            if implications:
                st.markdown("**Investment Implications:**")
                st.markdown(implications)
            
            # Quarterly Financial Ratios Table
            st.markdown("---")
            st.markdown("**Quarterly Financial Ratios (Last 10 Quarters)**")
            
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
                else:
                    st.info("Quarterly financial ratio data is being processed...")
            else:
                st.info("Quarterly financial data not available for detailed analysis.")
        else:
            st.info("AI analysis and quarterly data being generated...")
    
    with tab8:
        # Comprehensive AI Summary tab with all requested features
        display_ai_summary_tab(stock_data, gemini_analysis)
        
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
        
        # Fetch stock data with simple loading message
        with st.spinner("📊 Fetching comprehensive financial data..."):
            stock_data = data_fetcher.get_comprehensive_data(stock_symbol)
        
        # Generate Gemini analysis with simple loading message
        with st.spinner("🤖 Generating detailed analysis..."):
            gemini_analysis = gemini_analyzer.analyze_stock_comprehensive(stock_data)
        
        # Generate basic analysis as fallback
        with st.spinner("📈 Processing insights..."):
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
            display_company_header(stock_data)
            display_dashboard_overview(stock_data)
            st.markdown("---")
            display_shareholding_pattern(stock_data)
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
        # Clear previous analysis when new stock is searched
        st.session_state.current_stock_data = None
        st.session_state.current_analysis = None
        st.session_state.current_gemini_analysis = None
        
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