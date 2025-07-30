import os
import json
import os
import google
from typing import Dict, Any, List
import pandas as pd
import google.generativeai as genai
from google.generativeai import types

class GeminiStockAnalyzer:
    def __init__(self):
        """Initialize Gemini API client"""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = "gemini-2.5-flash"
    
    def analyze_stock_comprehensive(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive stock analysis using Gemini"""
        try:
            # Create detailed analysis prompt
            analysis_prompt = self._create_comprehensive_prompt(stock_data)
            
            response = genai.GenerativeModel(self.model).generate_content(
                model=self.model,
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                )
            )
            
            if response.text:
                return self._parse_comprehensive_analysis(response.text, stock_data)
            else:
                return self._generate_fallback_analysis(stock_data)
                
        except Exception as e:
            print(f"Gemini analysis failed: {e}")
            return self._generate_fallback_analysis(stock_data)
    
    def _create_comprehensive_prompt(self, stock_data: Dict[str, Any]) -> str:
        """Create detailed analysis prompt for Gemini"""
        company_name = stock_data.get('company_name', 'Unknown Company')
        current_price = stock_data.get('current_price', 0)
        sector = stock_data.get('sector', 'N/A')
        
        # Format financial metrics safely
        def safe_format(value, format_type='number'):
            if value is None or pd.isna(value):
                return 'N/A'
            try:
                if format_type == 'currency':
                    return f"₹{float(value):,.2f}"
                elif format_type == 'percentage':
                    return f"{float(value):.2f}%"
                else:
                    return f"{float(value):.2f}"
            except:
                return 'N/A'
        
        prompt = f"""
As a professional financial analyst, provide a comprehensive analysis of {company_name} stock. Here is the current financial data:

COMPANY OVERVIEW:
- Company: {company_name}
- Current Price: {safe_format(current_price, 'currency')}
- Sector: {sector}
- Industry: {stock_data.get('industry', 'N/A')}
- Market Cap: {safe_format(stock_data.get('market_cap'), 'currency')}

VALUATION METRICS:
- P/E Ratio: {safe_format(stock_data.get('pe_ratio'))}
- P/B Ratio: {safe_format(stock_data.get('pb_ratio'))}
- EPS: {safe_format(stock_data.get('eps'), 'currency')}
- Book Value: {safe_format(stock_data.get('book_value'), 'currency')}
- Price/Sales: {safe_format(stock_data.get('price_to_sales'))}

FINANCIAL HEALTH:
- ROE: {safe_format(stock_data.get('roe'), 'percentage')}
- ROA: {safe_format(stock_data.get('roa'), 'percentage')}
- Current Ratio: {safe_format(stock_data.get('current_ratio'))}
- Debt-to-Equity: {safe_format(stock_data.get('debt_to_equity'))}
- Quick Ratio: {safe_format(stock_data.get('quick_ratio'))}

GROWTH & PROFITABILITY:
- Revenue Growth: {safe_format(stock_data.get('revenue_growth'), 'percentage')}
- Earnings Growth: {safe_format(stock_data.get('earnings_growth'), 'percentage')}
- Profit Margins: {safe_format(stock_data.get('profit_margins'), 'percentage')}
- Operating Margins: {safe_format(stock_data.get('operating_margins'), 'percentage')}

MARKET PERFORMANCE:
- 52W High: {safe_format(stock_data.get('fifty_two_week_high'), 'currency')}
- 52W Low: {safe_format(stock_data.get('fifty_two_week_low'), 'currency')}
- Dividend Yield: {safe_format(stock_data.get('dividend_yield'), 'percentage')}

SHAREHOLDING:
- Promoter: {safe_format(stock_data.get('promoter_holding'), 'percentage')}
- FII: {safe_format(stock_data.get('fii_holding'), 'percentage')}
- DII: {safe_format(stock_data.get('dii_holding'), 'percentage')}

Please provide:

1. KEY INSIGHTS (5-6 bullet points analyzing the financial health, valuation, and market position):

2. INVESTOR IMPLICATIONS (3-4 sentences on what this means for potential investors, including risk assessment and investment outlook):

3. DETAILED ANALYSIS (comprehensive paragraph covering business fundamentals, competitive position, financial strengths/weaknesses, and future prospects):

Format your response clearly with these three sections.
"""
        return prompt
    
    def _parse_comprehensive_analysis(self, analysis_text: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gemini's comprehensive analysis response"""
        try:
            lines = analysis_text.split('\n')
            insights = []
            investor_implications = ""
            detailed_analysis = ""
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                    
                # Detect sections
                if any(keyword in line.upper() for keyword in ['KEY INSIGHTS', 'INSIGHTS:']):
                    current_section = 'insights'
                    continue
                elif any(keyword in line.upper() for keyword in ['INVESTOR IMPLICATIONS', 'IMPLICATIONS']):
                    current_section = 'implications'
                    continue
                elif any(keyword in line.upper() for keyword in ['DETAILED ANALYSIS', 'ANALYSIS:']):
                    current_section = 'detailed'
                    continue
                
                # Parse content based on current section
                if current_section == 'insights':
                    if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.', '6.')):
                        clean_insight = line.lstrip('•-*123456. ').strip()
                        if clean_insight:
                            insights.append(clean_insight)
                elif current_section == 'implications':
                    investor_implications += line + " "
                elif current_section == 'detailed':
                    detailed_analysis += line + " "
            
            # Clean up text
            investor_implications = investor_implications.strip()
            detailed_analysis = detailed_analysis.strip()
            
            # Ensure we have content
            if not insights:
                insights = [
                    f"Analysis of {stock_data.get('company_name', 'the company')} shows mixed financial indicators",
                    "Market position and valuation metrics require careful evaluation",
                    "Financial health indicators present both opportunities and risks"
                ]
            
            if not investor_implications:
                investor_implications = f"Investors should conduct thorough research on {stock_data.get('company_name', 'this stock')} considering current market conditions and financial metrics before making investment decisions."
            
            if not detailed_analysis:
                detailed_analysis = f"{stock_data.get('company_name', 'This company')} operates in the {stock_data.get('sector', 'market')} sector with current financial metrics indicating a mixed investment profile requiring detailed evaluation."
            
            return {
                'key_insights': insights[:6],  # Limit to 6 insights
                'investor_implications': investor_implications,
                'detailed_analysis': detailed_analysis,
                'analysis_source': 'gemini'
            }
            
        except Exception as e:
            print(f"Error parsing Gemini analysis: {e}")
            return self._generate_fallback_analysis(stock_data)
    
    def _generate_fallback_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback analysis when Gemini is unavailable"""
        company_name = stock_data.get('company_name', 'the company')
        
        insights = [
            f"Analysis shows {company_name} current market position requires evaluation",
            f"Financial metrics indicate mixed performance indicators",
            f"Valuation ratios suggest careful consideration for investment decisions",
            f"Market conditions and sector dynamics impact investment outlook"
        ]
        
        implications = f"Investors considering {company_name} should evaluate current financial metrics, market position, and sector trends. Risk assessment and portfolio diversification remain important factors for investment decisions."
        
        detailed = f"{company_name} presents a complex investment profile requiring comprehensive analysis of financial fundamentals, market conditions, and growth prospects before making investment decisions."
        
        return {
            'key_insights': insights,
            'investor_implications': implications,
            'detailed_analysis': detailed,
            'analysis_source': 'fallback'
        }