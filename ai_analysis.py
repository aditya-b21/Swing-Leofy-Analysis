import os
import requests
import json
from typing import Dict, List, Any
import pandas as pd

class AIAnalyzer:
    def __init__(self):
        # Try Together AI first, then fallback to Groq
        self.together_api_key = os.getenv("TOGETHER_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        
        self.together_endpoint = "https://api.together.xyz/inference"
        self.groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"
    
    def analyze_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered stock analysis"""
        try:
            # Prepare analysis prompt
            analysis_prompt = self._create_analysis_prompt(stock_data)
            
            # Try Together AI first
            if self.together_api_key:
                try:
                    analysis = self._call_together_ai(analysis_prompt)
                    if analysis:
                        return self._parse_analysis(analysis)
                except Exception as e:
                    print(f"Together AI failed: {e}")
            
            # Fallback to Groq
            if self.groq_api_key:
                try:
                    analysis = self._call_groq_ai(analysis_prompt)
                    if analysis:
                        return self._parse_analysis(analysis)
                except Exception as e:
                    print(f"Groq AI failed: {e}")
            
            # If both AI services fail, return basic analysis
            basic_analysis = self._generate_basic_analysis(stock_data)
            return {"analysis": basic_analysis, "source": "basic"}
            
        except Exception as e:
            print(f"Error in AI analysis: {e}")
            basic_analysis = self._generate_basic_analysis(stock_data)
            return {"analysis": basic_analysis, "source": "basic", "error": str(e)}
    
    def _create_analysis_prompt(self, stock_data: Dict[str, Any]) -> str:
        """Create analysis prompt for AI with safe formatting"""
        try:
            # Safe formatting function
            def safe_format(value, format_type=''):
                if value is None:
                    return 'N/A'
                try:
                    if format_type == 'price':
                        return f"₹{float(value):.2f}"
                    elif format_type == 'percent':
                        return f"{float(value):.2f}%"
                    elif format_type == 'currency':
                        return f"₹{int(value):,}"
                    elif format_type == 'ratio':
                        return f"{float(value):.2f}"
                    else:
                        return str(value)
                except (ValueError, TypeError):
                    return 'N/A'
            
            prompt = f"""
            Analyze the following stock data for {stock_data.get('company_name', 'Unknown')} ({stock_data.get('symbol', 'N/A')}) and provide insights:

            CURRENT METRICS:
            - Current Price: {safe_format(stock_data.get('current_price'), 'price')}
            - Market Cap: {safe_format(stock_data.get('market_cap'), 'currency')}
            - P/E Ratio: {safe_format(stock_data.get('pe_ratio'), 'ratio')}
            - ROE: {safe_format(stock_data.get('roe'), 'percent')}
            - ROCE: {safe_format(stock_data.get('roce'), 'percent')}
            - Debt-to-Equity: {safe_format(stock_data.get('debt_to_equity'), 'ratio')}
            - Dividend Yield: {safe_format(stock_data.get('dividend_yield'), 'percent')}
            - Current Ratio: {safe_format(stock_data.get('current_ratio'), 'ratio')}
            - Sector: {stock_data.get('sector', 'N/A')}
            - Industry: {stock_data.get('industry', 'N/A')}

            FINANCIAL PERFORMANCE:
            - 52W High: {safe_format(stock_data.get('fifty_two_week_high'), 'price')}
            - 52W Low: {safe_format(stock_data.get('fifty_two_week_low'), 'price')}

            SHAREHOLDING PATTERN:
            - Promoter Holding: {safe_format(stock_data.get('promoter_holding'), 'percent')}
            - FII Holding: {safe_format(stock_data.get('fii_holding'), 'percent')}
            - DII Holding: {safe_format(stock_data.get('dii_holding'), 'percent')}
            - Retail Holding: {safe_format(stock_data.get('retail_holding'), 'percent')}

            Please provide:
            1. 3-5 key insights as bullet points
            2. A comprehensive investment implication summary (2-3 sentences)

            Format your response as:
            INSIGHTS:
            • [Insight 1]
            • [Insight 2]
            • [Insight 3]
            • [Insight 4]
            • [Insight 5]

            INVESTMENT_SUMMARY:
            [Your investment analysis and recommendation]
            """
            
            return prompt
            
        except Exception as e:
            print(f"Error creating analysis prompt: {e}")
            return f"Analyze stock {stock_data.get('company_name', 'Unknown')} and provide investment insights."
    
    def _call_together_ai(self, prompt: str) -> str:
        """Call Together AI API"""
        headers = {
            "Authorization": f"Bearer {self.together_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "togethercomputer/llama-2-70b-chat",
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1.0
        }
        
        response = requests.post(self.together_endpoint, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get('output', {}).get('choices', [{}])[0].get('text', '')
    
    def _call_groq_ai(self, prompt: str) -> str:
        """Call Groq AI API"""
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "mixtral-8x7b-32768",
            "messages": [
                {"role": "system", "content": "You are a professional financial analyst providing stock analysis."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(self.groq_endpoint, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            insights = []
            investment_summary = ""
            
            lines = analysis_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if 'INSIGHTS:' in line.upper():
                    current_section = 'insights'
                elif 'INVESTMENT_SUMMARY:' in line.upper():
                    current_section = 'summary'
                elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    if current_section == 'insights':
                        insights.append(line[1:].strip())
                elif current_section == 'summary' and line:
                    investment_summary += line + " "
            
            # Clean up
            investment_summary = investment_summary.strip()
            
            # Ensure we have at least some insights
            if not insights:
                insights = ["Analysis pending - please check back for detailed insights"]
            
            if not investment_summary:
                investment_summary = "Investment analysis is being processed. Please try again for detailed recommendations."
            
            return {
                'insights': insights[:5],  # Max 5 insights
                'investment_summary': investment_summary
            }
            
        except Exception as e:
            print(f"Error parsing analysis: {e}")
            basic_analysis = self._generate_basic_analysis({})
            return {"analysis": basic_analysis, "source": "basic", "error": str(e)}
    
    def _generate_basic_analysis(self, stock_data: Dict[str, Any]) -> str:
        """Generate comprehensive basic analysis when AI services are unavailable"""
        insights = []
        
        company_name = stock_data.get('company_name', 'the company')
        current_price = stock_data.get('current_price', 0)
        
        # Generate insightful analysis based on available financial metrics
        
        # Valuation Analysis
        pe_ratio = stock_data.get('pe_ratio')
        if pe_ratio and isinstance(pe_ratio, (int, float)):
            if pe_ratio < 15:
                insights.append(f"Stock appears undervalued with P/E ratio of {pe_ratio:.1f}, below market average")
            elif pe_ratio > 30:
                insights.append(f"Stock trades at premium valuation with P/E ratio of {pe_ratio:.1f}")
            else:
                insights.append(f"Stock shows reasonable valuation with P/E ratio of {pe_ratio:.1f}")
        
        # Profitability Analysis
        roe = stock_data.get('roe')
        if roe and isinstance(roe, (int, float)):
            if roe > 15:
                insights.append(f"Excellent Return on Equity of {roe:.1f}% demonstrates strong profitability")
            elif roe < 10:
                insights.append(f"ROE of {roe:.1f}% suggests room for improvement in profitability")
            else:
                insights.append(f"Moderate ROE of {roe:.1f}% indicates stable returns")
        
        # Financial Health
        debt_to_equity = stock_data.get('debt_to_equity')
        if debt_to_equity and isinstance(debt_to_equity, (int, float)):
            if debt_to_equity < 0.3:
                insights.append(f"Conservative debt management with D/E ratio of {debt_to_equity:.2f}")
            elif debt_to_equity > 1.0:
                insights.append(f"High leverage with D/E ratio of {debt_to_equity:.2f} requires monitoring")
            else:
                insights.append(f"Balanced capital structure with D/E ratio of {debt_to_equity:.2f}")
        
        # Growth Analysis
        revenue_growth = stock_data.get('revenue_growth')
        if revenue_growth and isinstance(revenue_growth, (int, float)):
            if revenue_growth > 15:
                insights.append(f"Strong revenue growth of {revenue_growth:.1f}% indicates business expansion")
            elif revenue_growth < 0:
                insights.append(f"Negative revenue growth of {revenue_growth:.1f}% shows business challenges")
            else:
                insights.append(f"Moderate revenue growth of {revenue_growth:.1f}% suggests steady business")
        
        # Market Performance
        high_52w = stock_data.get('fifty_two_week_high')
        low_52w = stock_data.get('fifty_two_week_low')
        if current_price and high_52w and low_52w:
            perf_vs_high = ((current_price / high_52w) - 1) * 100
            if perf_vs_high > -10:
                insights.append(f"Trading near 52-week high suggests strong market sentiment")
            elif perf_vs_high < -30:
                insights.append(f"Trading significantly below 52-week high may present opportunity")
        
        # Dividend Analysis
        dividend_yield = stock_data.get('dividend_yield')
        if dividend_yield and isinstance(dividend_yield, (int, float)) and dividend_yield > 0:
            if dividend_yield > 3:
                insights.append(f"Attractive dividend yield of {dividend_yield:.1f}% provides steady income")
            else:
                insights.append(f"Dividend yield of {dividend_yield:.1f}% offers modest income")
        
        # Ensure we have insights
        if not insights:
            insights = [
                f"Currently analyzing {company_name} financial data",
                f"Stock trading at ₹{current_price:.2f}" if current_price else "Price data available",
                f"Sector: {stock_data.get('sector', 'Information not available')}",
                "Comprehensive analysis requires additional data points"
            ]
        
        # Create summary
        if len(insights) >= 3:
            investment_summary = f"Based on available metrics, {company_name} shows mixed fundamentals. "
            if any("strong" in insight.lower() or "excellent" in insight.lower() for insight in insights):
                investment_summary += "Several positive indicators suggest potential investment merit. "
            if any("concern" in insight.lower() or "negative" in insight.lower() for insight in insights):
                investment_summary += "Some areas require careful monitoring before investment decisions. "
            investment_summary += "Comprehensive analysis recommended with additional research."
        else:
            investment_summary = f"Limited data available for {company_name}. Additional research recommended for investment decisions."
        
        # Format the response
        formatted_insights = "\n".join([f"• {insight}" for insight in insights[:6]])  # Limit to 6 insights
        
        analysis = f"""**📊 STOCK ANALYSIS: {company_name.upper()}**

**Key Insights:**
{formatted_insights}

**Investment Summary:**
{investment_summary}

*Note: This analysis is based on available financial data. For investment decisions, consider consulting with a financial advisor and conducting additional research.*"""
        
        return analysis
        
        # Default insights if none generated
        if not insights:
            insights = [
                "Financial analysis requires detailed review of recent performance",
                "Consider industry trends and market conditions",
                "Evaluate long-term growth prospects and competitive position"
            ]
        
        investment_summary = "This stock requires detailed fundamental analysis. Consider consulting with a financial advisor for personalized investment advice. Past performance does not guarantee future results."
        
        return {
            'insights': insights[:5],
            'investment_summary': investment_summary
        }
