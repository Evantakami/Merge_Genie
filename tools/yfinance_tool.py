from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import yfinance as yf
import pandas as pd

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class MAInfoToolInput(BaseModel):
    symbol: str = Field(..., description="ターゲット企業の株式コード。例えば 'AAPL' はAppleを表します")
    info_type: str = Field(..., description="取得する情報の種類。選択肢: 'financial'（財務）, 'valuation'（評価）, 'growth'（成長）, 'efficiency'（効率）, 'management'（経営）, 'risk'（リスク）")

class MAInfoTool(BaseTool):
    name: str = "M&A_Info_Tool"
    description: str = "ターゲット企業の各種情報を取得し、M&A分析に役立てる"
    args_schema: type[BaseModel] = MAInfoToolInput

    def _run(self, symbol: str, info_type: str) -> str:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            if info_type == "financial":
                return self._get_financial_info(stock, info)
            elif info_type == "valuation":
                return self._get_valuation_info(info)
            elif info_type == "growth":
                return self._get_growth_info(info)
            elif info_type == "efficiency":
                return self._get_efficiency_info(info)
            elif info_type == "management":
                return self._get_management_info(stock)
            elif info_type == "risk":
                return self._get_risk_info(info)
            else:
                return "無効な情報タイプです。'financial', 'valuation', 'growth', 'efficiency', 'management', または 'risk' を選択してください"
        
        except Exception as e:
            return f"{symbol} の情報取得中にエラーが発生しました: {str(e)}"
    def _get_financial_info(self, stock, info):
        try:
            financial_info = f"財務状況（{info['longName']}）：\n"
            financial_info += f"業界：{info.get('industry', 'N/A')}\n"
            financial_info += f"セクター：{info.get('sector', 'N/A')}\n"
            financial_info += f"時価総額：{info.get('marketCap')}\n"
            financial_info += f"総収入：{info.get('totalRevenue')}\n"
            financial_info += f"純利益：{info.get('netIncomeToCommon')}\n"
            financial_info += f"営業キャッシュフロー：{info.get('operatingCashflow')}\n"
            financial_info += f"フリーキャッシュフロー：{info.get('freeCashflow')}\n"
            financial_info += f"EBITDA：{info.get('ebitda')}\n"
            financial_info += f"総資産：{info.get('totalCash')}\n"
            financial_info += f"総負債：{info.get('totalDebt')}\n"
            financial_info += f"株主資本：{info.get('totalStockholderEquity')}\n"
            financial_info += f"1株当たり利益（EPS）：{info.get('trailingEps')}\n"
            financial_info += f"株価収益率（PER）：{info.get('trailingPE')}\n"
            financial_info += f"株価純資産倍率（PBR）：{info.get('priceToBook')}\n"
            financial_info += f"配当利回り：{info.get('dividendYield')}\n"
            financial_info += f"負債資本比率：{info.get('debtToEquity')}\n"
            financial_info += f"総資産利益率（ROA）：{info.get('returnOnAssets')}\n"
            financial_info += f"自己資本利益率（ROE）：{info.get('returnOnEquity')}\n"
            financial_info += f"売上高成長率：{info.get('revenueGrowth')}\n"
            financial_info += f"利益成長率：{info.get('earningsGrowth')}\n"
            financial_info += f"アナリスト推奨：{info.get('recommendationKey', 'N/A')}\n"

            return financial_info

        except Exception as e:
            return f"財務情報の取得中にエラーが発生しました：{str(e)}"

    def _get_valuation_info(self, info):
        valuation_info = f"評価情報（{info['longName']}）:\n"
        valuation_info += f"時価総額：{info.get('marketCap')}\n"
        valuation_info += f"PER（TTM）：{info.get('trailingPE')}\n"
        valuation_info += f"予想PER：{info.get('forwardPE')}\n"
        valuation_info += f"PBR：{info.get('priceToBook')}\n"
        valuation_info += f"PEG比率：{info.get('pegRatio')}\n"
        valuation_info += f"企業価値：{info.get('enterpriseValue')}\n"
        valuation_info += f"EV/EBITDA：{info.get('enterpriseToEbitda')}\n"
        valuation_info += f"EV/売上高：{info.get('enterpriseToRevenue')}\n"
        valuation_info += f"時価総額/売上高：{info.get('priceToSalesTrailing12Months')}\n"
        valuation_info += f"配当利回り：{info.get('dividendYield')}\n"
        valuation_info += f"総現金：{info.get('totalCash')}\n"
        valuation_info += f"総負債：{info.get('totalDebt')}\n"
        valuation_info += f"流動比率：{info.get('currentRatio')}\n"
        valuation_info += f"速動比率：{info.get('quickRatio')}\n"
        valuation_info += f"フリーキャッシュフロー：{info.get('freeCashflow')}\n"
        valuation_info += f"52周最高値：{info.get('fiftyTwoWeekHigh')}\n"
        valuation_info += f"52周最低値：{info.get('fiftyTwoWeekLow')}\n"
        valuation_info += f"平均取引量：{info.get('averageVolume')}\n"
        valuation_info += f"取引量（現在）：{info.get('volume')}\n"
        valuation_info += f"Beta値：{info.get('beta')}\n"
        valuation_info += f"最終配当値：{info.get('lastDividendValue')}\n"
        valuation_info += f"最終配当日：{info.get('lastDividendDate', 'N/A')}\n"
        valuation_info += f"grossMargin：{info.get('grossMargins')}\n"
        valuation_info += f"EBITDAMargin：{info.get('ebitdaMargins')}\n"
        valuation_info += f"営業Margin：{info.get('operatingMargins')}\n"

        return valuation_info

    def _get_growth_info(self, info):
        growth_info = f"成長と業績指標：（{info['longName']}）\n"
        growth_info += f"収入成長率（前年比）：{info.get('revenueGrowth')}\n"
        growth_info += f"利益成長率（前年比）：{info.get('earningsGrowth')}\n"
        growth_info += f"四半期収益成長率：{info.get('earningsQuarterlyGrowth')}\n"
        growth_info += f"52週株価変動率：{info.get('52WeekChange')}\n"
        growth_info += f"営業利益率：{info.get('operatingMargins')}\n"
        growth_info += f"利益率：{info.get('profitMargins')}\n"
        growth_info += f"総資産利益率（ROA）：{info.get('returnOnAssets')}\n"
        growth_info += f"自己資本利益率（ROE）：{info.get('returnOnEquity')}\n"
        growth_info += f"EBITDAマージン：{info.get('ebitdaMargins')}\n"
        growth_info += f"粗利益率：{info.get('grossMargins')}\n"
        growth_info += f"フリーキャッシュフロー：{info.get('freeCashflow')}\n"
        growth_info += f"営業キャッシュフロー：{info.get('operatingCashflow')}\n"
        growth_info += f"1株当たり利益（EPS）：{info.get('trailingEps')}\n"
        growth_info += f"予想EPS：{info.get('forwardEps')}\n"
        growth_info += f"アナリスト推奨：{info.get('recommendationKey', 'N/A')}\n"
        growth_info += f"アナリスト平均目標株価：{info.get('targetMeanPrice')}\n"
        growth_info += f"総収入：{info.get('totalRevenue')}\n"
        growth_info += f"市場キャップ：{info.get('marketCap')}\n"
        growth_info += f"企業価値：{info.get('enterpriseValue')}\n"
        growth_info += f"1株当たり収入：{info.get('revenuePerShare')}\n"
        growth_info += f"負債比率：{info.get('debtToEquity')}\n"
        growth_info += f"従業員数：{info.get('fullTimeEmployees', 'N/A')}\n"

        return growth_info


    def _get_efficiency_info(self, info):
        efficiency_info = f"効率性指標：（{info['longName']}）\n"
        efficiency_info += f"総資産利益率（ROA）：{info.get('returnOnAssets')}\n"
        efficiency_info += f"自己資本利益率（ROE）：{info.get('returnOnEquity')}\n"
        efficiency_info += f"売上高利益率：{info.get('profitMargins')}\n"
        efficiency_info += f"営業利益率：{info.get('operatingMargins')}\n"
        efficiency_info += f"EBITDA利益率：{info.get('ebitdaMargins')}\n"
        efficiency_info += f"粗利益率：{info.get('grossMargins')}\n"
        efficiency_info += f"1株当たり売上高：{info.get('revenuePerShare')}\n"
        efficiency_info += f"1株当たり利益（EPS）：{info.get('trailingEps')}\n"
        efficiency_info += f"予想EPS：{info.get('forwardEps')}\n"
        efficiency_info += f"流動比率：{info.get('currentRatio')}\n"
        efficiency_info += f"当座比率：{info.get('quickRatio')}\n"
        efficiency_info += f"負債資本比率：{info.get('debtToEquity')}\n"
        efficiency_info += f"フリーキャッシュフロー：{info.get('freeCashflow')}\n"
        efficiency_info += f"営業キャッシュフロー：{info.get('operatingCashflow')}\n"
        efficiency_info += f"収益成長率：{info.get('revenueGrowth')}\n"
        efficiency_info += f"利益成長率：{info.get('earningsGrowth')}\n"
        efficiency_info += f"PEG比率：{info.get('pegRatio')}\n"
        efficiency_info += f"企業価値/EBITDA：{info.get('enterpriseToEbitda')}\n"

        return efficiency_info

    def _get_management_info(self, stock):
        info = stock.info 
        officers = info.get('companyOfficers', [])
        management_info = f"経営陣情報：（{info['longName']}）\n"
        
        for officer in officers[:5]:
            name = officer.get('name', 'N/A')
            title = officer.get('title', 'N/A')
            age = officer.get('age', 'N/A')
            year_born = officer.get('yearBorn', 'N/A')
            total_pay = officer.get('totalPay', 'N/A')
            
            management_info += f"氏名: {name}\n"
            management_info += f"  役職: {title}\n"
            management_info += f"  年齢: {age}\n"
            management_info += f"  生年: {year_born}\n"
            management_info += f"  報酬: {total_pay}\n"
            management_info += "\n"

        management_info += f"経営指標：（{info['longName']}）\n"
        management_info += f"従業員数: {info.get('fullTimeEmployees', 'N/A')}\n"
        management_info += f"インサイダー保有率: {info.get('heldPercentInsiders', 'N/A')}\n"
        management_info += f"機関投資家保有率: {info.get('heldPercentInstitutions', 'N/A')}\n"
        management_info += f"配当性向: {info.get('payoutRatio', 'N/A')}\n"
        management_info += f"株主資本利益率（ROE）: {info.get('returnOnEquity', 'N/A')}\n"
        management_info += f"総資産利益率（ROA）: {info.get('returnOnAssets', 'N/A')}\n"
        
        management_info += "\nコーポレートガバナンスリスク指標：\n"
        management_info += f"監査リスク: {info.get('auditRisk', 'N/A')}\n"
        management_info += f"取締役会リスク: {info.get('boardRisk', 'N/A')}\n"
        management_info += f"報酬リスク: {info.get('compensationRisk', 'N/A')}\n"
        management_info += f"株主権利リスク: {info.get('shareHolderRightsRisk', 'N/A')}\n"
        management_info += f"総合リスク: {info.get('overallRisk', 'N/A')}\n"

        return management_info

    def _get_risk_info(self, info):
        risk_info =  f"リスク情報：（{info['longName']}）\n"
        risk_info += f"ベータ係数：{info.get('beta')}\n"
        risk_info += f"52週高値：{info.get('fiftyTwoWeekHigh')}\n"
        risk_info += f"52週安値：{info.get('fiftyTwoWeekLow')}\n"
        risk_info += f"52週変動率：{info.get('52WeekChange')}\n"
        risk_info += f"負債比率：{info.get('debtToEquity')}\n"
        risk_info += f"流動比率：{info.get('currentRatio')}\n"
        risk_info += f"当座比率：{info.get('quickRatio')}\n"
        risk_info += f"インタレストカバレッジ：{info.get('interestCoverage')}\n"
        risk_info += f"総負債/EBITDA比率：{info.get('totalDebt', 0) / info.get('ebitda', 1)}\n"
        risk_info += f"フリーキャッシュフロー/総負債比率：{info.get('freeCashflow', 0) / info.get('totalDebt', 1)}\n"
        risk_info += f"株価ボラティリティ（過去10日）：{info.get('averageVolume10days')}\n"
        risk_info += f"株価収益率（P/E比率）：{info.get('trailingPE')}\n"
        risk_info += f"株価純資産倍率（P/B比率）：{info.get('priceToBook')}\n"
        risk_info += f"売上高利益率：{info.get('profitMargins')}\n"
        risk_info += f"売上高成長率：{info.get('revenueGrowth')}\n"
        risk_info += f"営業キャッシュフロー：{info.get('operatingCashflow')}\n"
        risk_info += f"総資産利益率（ROA）：{info.get('returnOnAssets')}\n"
        risk_info += f"株主資本利益率（ROE）：{info.get('returnOnEquity')}\n"
        risk_info += f"インサイダー保有割合：{info.get('heldPercentInsiders')}\n"
        risk_info += f"機関投資家保有割合：{info.get('heldPercentInstitutions')}\n"
        risk_info += "\nコーポレートガバナンスリスク指標：\n"
        risk_info += f"監査リスク：{info.get('auditRisk', 'N/A')}\n"
        risk_info += f"取締役会リスク：{info.get('boardRisk', 'N/A')}\n"
        risk_info += f"報酬リスク：{info.get('compensationRisk', 'N/A')}\n"
        risk_info += f"株主権利リスク：{info.get('shareHolderRightsRisk', 'N/A')}\n"
        risk_info += f"総合リスク：{info.get('overallRisk', 'N/A')}\n"

        return risk_info

    def _arun(self, symbol: str, info_type: str) -> str:
        return self._run(symbol, info_type)

# ツールのインスタンス化
ma_info_tool = MAInfoTool()

