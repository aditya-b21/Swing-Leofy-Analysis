import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import os

class StockDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        # Add headers to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_indian_symbol(self, symbol):
        """Convert symbol to Indian stock market format"""
        symbol = symbol.upper().strip()
        
        # If already has .NS or .BO, return as is
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol
        
        # Common Indian stock symbols
        indian_symbols = {
            'TCS': 'TCS.NS',
            'INFY': 'INFY.NS',
            'INFOSYS': 'INFY.NS',
            'RELIANCE': 'RELIANCE.NS',
            'HDFCBANK': 'HDFCBANK.NS',
            'HDFC': 'HDFCBANK.NS',
            'ITC': 'ITC.NS',
            'SBIN': 'SBIN.NS',
            'SBI': 'SBIN.NS',
            'BHARTIARTL': 'BHARTIARTL.NS',
            'AIRTEL': 'BHARTIARTL.NS',
            'ICICIBANK': 'ICICIBANK.NS',
            'ICICI': 'ICICIBANK.NS',
            'LT': 'LT.NS',
            'LARSEN': 'LT.NS',
            'HCLTECH': 'HCLTECH.NS',
            'HCL': 'HCLTECH.NS',
            'WIPRO': 'WIPRO.NS',
            'ONGC': 'ONGC.NS',
            'NTPC': 'NTPC.NS',
            'POWERGRID': 'POWERGRID.NS',
            'COALINDIA': 'COALINDIA.NS',
            'MARUTI': 'MARUTI.NS',
            'BAJFINANCE': 'BAJFINANCE.NS',
            'BAJAJ': 'BAJFINANCE.NS',
            'SUNPHARMA': 'SUNPHARMA.NS',
            'DRREDDY': 'DRREDDY.NS',
            'NESTLEIND': 'NESTLEIND.NS',
            'NESTLE': 'NESTLEIND.NS',
            'HINDUNILVR': 'HINDUNILVR.NS',
            'HUL': 'HINDUNILVR.NS',
            'ULTRACEMCO': 'ULTRACEMCO.NS',
            'ADANIPORTS': 'ADANIPORTS.NS',
            'ADANI': 'ADANIPORTS.NS'
        }
        
        if symbol in indian_symbols:
            return indian_symbols[symbol]
        
        # Try with .NS first (NSE), then .BO (BSE)
        return f"{symbol}.NS"
    
    def get_comprehensive_data(self, symbol):
        """Fetch comprehensive and accurate stock data"""
        try:
            # Convert to proper Indian symbol format
            formatted_symbol = self.get_indian_symbol(symbol)
            print(f"Fetching comprehensive data for: {formatted_symbol}")
            
            # Get stock info using yfinance
            stock = yf.Ticker(formatted_symbol)
            
            # Comprehensive data retrieval with fallback
            try:
                info = stock.info
                if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info and 'previousClose' not in info):
                    # Try with .BO if .NS failed
                    if formatted_symbol.endswith('.NS'):
                        formatted_symbol = formatted_symbol.replace('.NS', '.BO')
                        stock = yf.Ticker(formatted_symbol)
                        info = stock.info
                    
                    if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info and 'previousClose' not in info):
                        raise ValueError(f"Stock symbol '{symbol}' not found or no price data available.")
                        
            except Exception as e:
                raise ValueError(f"Unable to fetch data for '{symbol}'. Please verify the stock symbol.")
            
            print("✓ Basic stock info retrieved successfully")
            
            # Get more comprehensive historical data (3 years for better analysis)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 3)  # 3 years for comprehensive analysis
            
            hist_data = None
            try:
                hist_data = stock.history(start=start_date, end=end_date, timeout=15)
                if hist_data.empty:
                    # Fallback to 1 year if 3 years fails
                    start_date = end_date - timedelta(days=365)
                    hist_data = stock.history(start=start_date, end=end_date, timeout=10)
            except Exception as e:
                print(f"Historical data fetch failed: {e}")
                hist_data = pd.DataFrame()  # Empty dataframe if fails
            
            print("✓ Historical data retrieved")
            
            # Get comprehensive financial data
            annual_data = self._get_annual_financials(stock)
            quarterly_data = self._get_quarterly_financials_detailed(stock)
            
            # Get detailed financial statements with enhanced error handling
            try:
                balance_sheet_data = stock.balance_sheet if hasattr(stock, 'balance_sheet') else pd.DataFrame()
                if not balance_sheet_data.empty:
                    balance_sheet_data = balance_sheet_data.fillna('N/A')
                    # Transpose for better display
                    balance_sheet_data = balance_sheet_data.T
                    balance_sheet_data.index = [idx.strftime('%Y') if hasattr(idx, 'strftime') else str(idx) for idx in balance_sheet_data.index]
            except Exception as e:
                print(f"Balance sheet error: {e}")
                balance_sheet_data = pd.DataFrame()
                
            try:
                income_statement_data = stock.financials if hasattr(stock, 'financials') else pd.DataFrame()  
                if not income_statement_data.empty:
                    income_statement_data = income_statement_data.fillna('N/A')
                    # Transpose for better display
                    income_statement_data = income_statement_data.T
                    income_statement_data.index = [idx.strftime('%Y') if hasattr(idx, 'strftime') else str(idx) for idx in income_statement_data.index]
            except Exception as e:
                print(f"Income statement error: {e}")
                income_statement_data = pd.DataFrame()
                
            try:
                cash_flow_data = stock.cashflow if hasattr(stock, 'cashflow') else pd.DataFrame()
                if not cash_flow_data.empty:
                    cash_flow_data = cash_flow_data.fillna('N/A')
                    # Transpose for better display
                    cash_flow_data = cash_flow_data.T
                    cash_flow_data.index = [idx.strftime('%Y') if hasattr(idx, 'strftime') else str(idx) for idx in cash_flow_data.index]
            except Exception as e:
                print(f"Cash flow error: {e}")
                cash_flow_data = pd.DataFrame()
            
            # Get additional financial metrics
            additional_metrics = self._get_additional_metrics(stock, info)
            
            print("✓ Financial data processed")
            
            # Compile comprehensive data with enhanced accuracy
            current_price = (info.get('currentPrice') or 
                           info.get('regularMarketPrice') or 
                           info.get('previousClose') or 0)
            
            stock_data = {
                'symbol': formatted_symbol,
                'company_name': info.get('longName', info.get('shortName', symbol)),
                'current_price': current_price,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', info.get('forwardPE', None)),
                'pb_ratio': info.get('priceToBook', None),
                'roe': self._calculate_roe(info),
                'roce': self._calculate_roce(info),
                'debt_to_equity': info.get('debtToEquity', None),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None,
                'current_ratio': info.get('currentRatio', None),
                'quick_ratio': info.get('quickRatio', None),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', None),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', None),
                'book_value': info.get('bookValue', None),
                'price_to_sales': info.get('priceToSalesTrailing12Months', None),
                'profit_margins': info.get('profitMargins', None) * 100 if info.get('profitMargins') else None,
                'operating_margins': info.get('operatingMargins', None) * 100 if info.get('operatingMargins') else None,
                'revenue_growth': info.get('revenueGrowth', None) * 100 if info.get('revenueGrowth') else None,
                'earnings_growth': info.get('earningsGrowth', None) * 100 if info.get('earningsGrowth') else None,
                'eps': info.get('eps', info.get('trailingEps', None)),
                'net_sales_growth': info.get('revenueGrowth', None) * 100 if info.get('revenueGrowth') else None,
                'promoter_holding': self._get_promoter_holding(info),
                'fii_holding': self._get_fii_holding(info),
                'dii_holding': self._get_dii_holding(info),
                'qib_holding': self._get_qib_holding(info),
                'retail_holding': self._get_retail_holding(info),
                'annual_data': annual_data,
                'quarterly_data': quarterly_data,
                'balance_sheet_data': balance_sheet_data,
                'income_statement_data': income_statement_data,  
                'cash_flow_data': cash_flow_data,
                'historical_data': hist_data,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'India'),
                'employees': info.get('fullTimeEmployees', None),
                'website': info.get('website', None),
                'business_summary': info.get('longBusinessSummary', 'N/A'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add additional calculated metrics
            stock_data.update(additional_metrics)
            
            print(f"Data compilation complete for {stock_data['company_name']}")
            return stock_data
            
        except Exception as e:
            print(f"Error in get_comprehensive_data: {str(e)}")
            raise Exception(f"Error fetching data for {symbol}: {str(e)}")
    
    def _get_annual_financials(self, stock):
        """Get annual financial data with timeout protection"""
        try:
            # Get financial statements with timeout handling
            financials = None
            balance_sheet = None
            
            try:
                financials = stock.financials
            except Exception as e:
                print(f"Annual financials fetch failed: {e}")
                return pd.DataFrame({'Message': ['Annual financial data not available']})
            
            if financials is None or financials.empty:
                return pd.DataFrame({'Message': ['No annual financial data found']})
            
            # Try to get balance sheet (optional)
            try:
                balance_sheet = stock.balance_sheet
            except Exception:
                balance_sheet = pd.DataFrame()  # Empty if fails
            
            # Prepare annual data
            annual_data = []
            
            for year in financials.columns[:5]:  # Limit to 5 years for speed
                year_str = year.strftime('%Y') if hasattr(year, 'strftime') else str(year)
                
                annual_record = {
                    'Year': year_str,
                    'Total Revenue': financials.loc['Total Revenue', year] if 'Total Revenue' in financials.index else None,
                    'Net Income': financials.loc['Net Income', year] if 'Net Income' in financials.index else None,
                    'EPS': self._calculate_eps(financials, year),
                    'Total Assets': balance_sheet.loc['Total Assets', year] if not balance_sheet.empty and 'Total Assets' in balance_sheet.index else None,
                    'Total Debt': balance_sheet.loc['Total Debt', year] if not balance_sheet.empty and 'Total Debt' in balance_sheet.index else None
                }
                annual_data.append(annual_record)
            
            result_df = pd.DataFrame(annual_data)
            return result_df if not result_df.empty else pd.DataFrame({'Message': ['Financial data processing failed']})
            
        except Exception as e:
            print(f"Error getting annual financials: {e}")
            return pd.DataFrame({'Message': [f'Error: {str(e)}']})
    
    def _get_quarterly_financials_detailed(self, stock):
        """Get detailed quarterly financial data for last 10 quarters"""
        try:
            # Get quarterly financials and balance sheet
            quarterly_financials = None
            quarterly_balance_sheet = None
            
            try:
                quarterly_financials = stock.quarterly_financials
                quarterly_balance_sheet = stock.quarterly_balance_sheet
                
                # Validate data availability
                if quarterly_financials is None or quarterly_financials.empty:
                    quarterly_financials = pd.DataFrame()
                if quarterly_balance_sheet is None or quarterly_balance_sheet.empty:
                    quarterly_balance_sheet = pd.DataFrame()
                    
            except Exception as e:
                print(f"Quarterly financials fetch failed: {e}")
                quarterly_financials = pd.DataFrame()
                quarterly_balance_sheet = pd.DataFrame()
            
            # Even if quarterly_financials is empty, create some basic data from stock info
            info = stock.info if hasattr(stock, 'info') else {}
            quarterly_data = []
            
            if quarterly_financials.empty:
                # Create a basic quarterly data structure with available info
                basic_data = {
                    'Quarter': 'Latest',
                    'EPS': info.get('eps', None),
                    'ROA (%)': None,
                    'Net Margin (%)': info.get('profitMargins', None) * 100 if info.get('profitMargins') else None,
                    'Current Ratio': info.get('currentRatio', None),
                    'Debt to Equity': info.get('debtToEquity', None),
                    'PE Ratio': info.get('forwardPE', None),
                    'Revenue': info.get('totalRevenue', None),
                    'Net Income': info.get('netIncomeToCommon', None)
                }
                quarterly_data.append(basic_data)
                return pd.DataFrame(quarterly_data)
            
            # Prepare detailed quarterly data for last 10 quarters
            
            # Limit to 10 quarters as requested
            quarters_to_process = min(10, len(quarterly_financials.columns))
            
            for i, quarter in enumerate(quarterly_financials.columns[:quarters_to_process]):
                quarter_str = quarter.strftime('%Y-Q%m') if hasattr(quarter, 'strftime') else str(quarter)
                
                # Calculate EPS
                net_income = self._safe_get_value(quarterly_financials, 'Net Income', quarter)
                shares_outstanding = info.get('sharesOutstanding', info.get('impliedSharesOutstanding'))
                eps = None
                if net_income and shares_outstanding:
                    eps = net_income / shares_outstanding
                
                # Calculate ROA
                total_assets = self._safe_get_value(quarterly_balance_sheet, 'Total Assets', quarter) if quarterly_balance_sheet is not None else None
                roa = None
                if net_income and total_assets:
                    roa = (net_income / total_assets) * 100
                
                # Calculate margins
                total_revenue = self._safe_get_value(quarterly_financials, 'Total Revenue', quarter)
                margin = None
                if net_income and total_revenue:
                    margin = (net_income / total_revenue) * 100
                
                # Get current ratio components
                current_assets = self._safe_get_value(quarterly_balance_sheet, 'Current Assets', quarter) if quarterly_balance_sheet is not None else None
                current_liabilities = self._safe_get_value(quarterly_balance_sheet, 'Current Liabilities', quarter) if quarterly_balance_sheet is not None else None
                current_ratio = None
                if current_assets and current_liabilities:
                    current_ratio = current_assets / current_liabilities
                
                # Get debt to equity
                total_debt = self._safe_get_value(quarterly_balance_sheet, 'Total Debt', quarter) if quarterly_balance_sheet is not None else None
                stockholders_equity = self._safe_get_value(quarterly_balance_sheet, 'Stockholders Equity', quarter) if quarterly_balance_sheet is not None else None
                debt_to_equity = None
                if total_debt and stockholders_equity:
                    debt_to_equity = total_debt / stockholders_equity
                
                # PE Ratio (using current stock price and quarterly EPS)
                current_price = info.get('currentPrice', info.get('regularMarketPrice'))
                pe_ratio = None
                if current_price and eps and eps > 0:
                    pe_ratio = current_price / eps
                
                quarterly_record = {
                    'Quarter': quarter_str,
                    'EPS': eps,
                    'ROA (%)': roa,
                    'Net Margin (%)': margin,
                    'Current Ratio': current_ratio,
                    'Debt to Equity': debt_to_equity,
                    'PE Ratio': pe_ratio,
                    'Revenue': total_revenue,
                    'Net Income': net_income
                }
                quarterly_data.append(quarterly_record)
            
            result_df = pd.DataFrame(quarterly_data)
            return result_df if not result_df.empty else pd.DataFrame({'Message': ['Quarterly data processing failed']})
            
        except Exception as e:
            print(f"Error getting detailed quarterly financials: {e}")
            return pd.DataFrame({'Message': [f'Error: {str(e)}']})
    
    def _safe_get_value(self, dataframe, key, column):
        """Safely get value from dataframe"""
        try:
            if dataframe is None or dataframe.empty:
                return None
            if key in dataframe.index and column in dataframe.columns:
                value = dataframe.loc[key, column]
                return value if pd.notna(value) else None
            return None
        except Exception:
            return None
    
    def _get_quarterly_financials(self, stock):
        """Get quarterly financial data with timeout protection"""
        try:
            # Get quarterly financials with timeout handling
            try:
                quarterly_financials = stock.quarterly_financials
            except Exception as e:
                print(f"Quarterly financials fetch failed: {e}")
                return pd.DataFrame({'Message': ['Quarterly financial data not available']})
            
            if quarterly_financials is None or quarterly_financials.empty:
                return pd.DataFrame({'Message': ['No quarterly financial data found']})
            
            # Prepare quarterly data
            quarterly_data = []
            
            for quarter in quarterly_financials.columns[:8]:  # Limit to 8 quarters for speed
                quarter_str = quarter.strftime('%Y-Q%m') if hasattr(quarter, 'strftime') else str(quarter)
                
                quarterly_record = {
                    'Quarter': quarter_str,
                    'Total Revenue': quarterly_financials.loc['Total Revenue', quarter] if 'Total Revenue' in quarterly_financials.index else None,
                    'Net Income': quarterly_financials.loc['Net Income', quarter] if 'Net Income' in quarterly_financials.index else None,
                    'EPS': self._calculate_eps(quarterly_financials, quarter)
                }
                quarterly_data.append(quarterly_record)
            
            result_df = pd.DataFrame(quarterly_data)
            return result_df if not result_df.empty else pd.DataFrame({'Message': ['Quarterly data processing failed']})
            
        except Exception as e:
            print(f"Error getting quarterly financials: {e}")
            return pd.DataFrame({'Message': [f'Error: {str(e)}']})
    
    def _calculate_eps(self, financials, period):
        """Calculate EPS from financial data"""
        try:
            net_income = financials.loc['Net Income', period] if 'Net Income' in financials.index else None
            shares_outstanding = financials.loc['Basic Average Shares', period] if 'Basic Average Shares' in financials.index else None
            
            if net_income is not None and shares_outstanding is not None and shares_outstanding != 0:
                return net_income / shares_outstanding
            return None
        except Exception:
            return None
    
    def _calculate_roe(self, info):
        """Calculate Return on Equity"""
        try:
            return info.get('returnOnEquity', None) * 100 if info.get('returnOnEquity') else None
        except Exception:
            return None
    
    def _calculate_roce(self, info):
        """Calculate Return on Capital Employed"""
        try:
            return info.get('returnOnAssets', None) * 100 if info.get('returnOnAssets') else None
        except Exception:
            return None
    
    def _get_promoter_holding(self, info):
        """Extract promoter holding percentage"""
        try:
            # This data might not be directly available in yfinance
            # You would need additional data sources for accurate shareholding patterns
            return info.get('heldPercentInstitutions', None) * 100 if info.get('heldPercentInstitutions') else None
        except Exception:
            return None
    
    def _get_fii_holding(self, info):
        """Extract FII holding percentage"""
        try:
            return info.get('heldPercentInstitutions', None) * 100 if info.get('heldPercentInstitutions') else None
        except Exception:
            return None
    
    def _get_dii_holding(self, info):
        """Extract DII holding percentage"""
        try:
            # Placeholder - would need specialized data source
            return None
        except Exception:
            return None
    
    def _get_qib_holding(self, info):
        """Extract QIB holding percentage"""
        try:
            # Placeholder - would need specialized data source
            return None
        except Exception:
            return None
    
    def _get_retail_holding(self, info):
        """Extract retail holding percentage"""
        try:
            held_by_institutions = info.get('heldPercentInstitutions', 0)
            held_by_insiders = info.get('heldPercentInsiders', 0)
            retail_holding = 100 - (held_by_institutions * 100) - (held_by_insiders * 100)
            return max(0, retail_holding)
        except Exception:
            return None
    
    def _get_additional_metrics(self, stock, info):
        """Get additional financial metrics and calculations"""
        try:
            additional_data = {}
            
            # Calculate price performance metrics
            hist_data = stock.history(period="1y")
            if not hist_data.empty:
                year_start_price = hist_data['Close'].iloc[0]
                current_price = hist_data['Close'].iloc[-1]
                additional_data['year_performance'] = ((current_price - year_start_price) / year_start_price) * 100
                
                # Calculate volatility (standard deviation of returns)
                returns = hist_data['Close'].pct_change().dropna()
                additional_data['volatility'] = returns.std() * 100
                
                # Calculate average volume
                additional_data['avg_volume'] = hist_data['Volume'].mean()
            
            # Enhanced valuation metrics
            additional_data['enterprise_value'] = info.get('enterpriseValue', None)
            additional_data['ev_to_revenue'] = info.get('enterpriseToRevenue', None)
            additional_data['ev_to_ebitda'] = info.get('enterpriseToEbitda', None)
            
            # Financial strength indicators
            additional_data['total_cash'] = info.get('totalCash', None)
            additional_data['total_debt'] = info.get('totalDebt', None)
            additional_data['free_cash_flow'] = info.get('freeCashflow', None)
            
            return additional_data
            
        except Exception as e:
            print(f"Error getting additional metrics: {e}")
            return {}
    
    def _get_balance_sheet_data(self, stock):
        """Get balance sheet data"""
        try:
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                # Get latest year data
                latest_bs = balance_sheet.iloc[:, 0]
                return {
                    'total_assets': latest_bs.get('Total Assets', None),
                    'total_liabilities': latest_bs.get('Total Liabilities', None), 
                    'shareholders_equity': latest_bs.get('Stockholders Equity', None),
                    'total_debt': latest_bs.get('Total Debt', None),
                    'cash_and_equivalents': latest_bs.get('Cash And Cash Equivalents', None),
                    'current_assets': latest_bs.get('Current Assets', None),
                    'current_liabilities': latest_bs.get('Current Liabilities', None),
                    'working_capital': latest_bs.get('Working Capital', None)
                }
            return {}
        except Exception as e:
            print(f"Error fetching balance sheet: {e}")
            return {}
    
    def _get_income_statement_data(self, stock):
        """Get income statement data"""
        try:
            income_stmt = stock.financials
            if income_stmt is not None and not income_stmt.empty:
                # Get latest year data
                latest_is = income_stmt.iloc[:, 0]
                return {
                    'total_revenue': latest_is.get('Total Revenue', None),
                    'gross_profit': latest_is.get('Gross Profit', None),
                    'operating_income': latest_is.get('Operating Income', None),
                    'net_income': latest_is.get('Net Income', None),
                    'ebitda': latest_is.get('EBITDA', None),
                    'interest_expense': latest_is.get('Interest Expense', None),
                    'tax_provision': latest_is.get('Tax Provision', None)
                }
            return {}
        except Exception as e:
            print(f"Error fetching income statement: {e}")
            return {}
    
    def _get_cash_flow_data(self, stock):
        """Get cash flow data"""
        try:
            cash_flow = stock.cashflow
            if cash_flow is not None and not cash_flow.empty:
                # Get latest year data
                latest_cf = cash_flow.iloc[:, 0]
                return {
                    'operating_cash_flow': latest_cf.get('Operating Cash Flow', None),
                    'investing_cash_flow': latest_cf.get('Investing Cash Flow', None),
                    'financing_cash_flow': latest_cf.get('Financing Cash Flow', None),
                    'free_cash_flow': latest_cf.get('Free Cash Flow', None),
                    'capital_expenditures': latest_cf.get('Capital Expenditures', None)
                }
            return {}
        except Exception as e:
            print(f"Error fetching cash flow: {e}")
            return {}
