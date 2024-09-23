from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from pathlib import Path
import sys
from typing import Dict

current_dir = Path.cwd()
tools_dir = current_dir.parent / 'tools'
sys.path.append(str(tools_dir))
from yfinance_tool import MAInfoTool


# Create MAInfoTool
def run_ma_info_tool(symbol: str) -> str:
    ma_info_tool = MAInfoTool()
    risk_data = ma_info_tool.run({"symbol": symbol, "info_type": "risk"})
    return risk_data if risk_data else "Unable to retrieve risk information."

# Create tools list
tools = [
    StructuredTool.from_function(
        func=run_ma_info_tool,
        name="MA_Info_Tool",
        description="Get risk information for the target company. Input is the stock symbol."
    )
]

# Create LLM (unchanged)
llm = ChatOpenAI(temperature=0.5, max_tokens=4096, model="gpt-4o-mini")

template = """
Before providing the risk analysis, use the MA_Info_Tool to gather comprehensive financial data for the stock symbol {stock_symbol}. If the tool fails to return any financial data, respond with "I do not have the necessary risk information to proceed with the analysis."

Conduct a thorough and analytical risk review covering the following areas:

1. Market Risk:
Beta Coefficient: Evaluate the company's beta coefficient. Analyze the company’s sensitivity to overall market movements and compare it to industry peers to determine its exposure to market volatility.
52-week High and Low: Assess the company’s 52-week high and low stock prices. Discuss what these figures reveal about market sentiment, investor confidence, and stock volatility.
52-week Change: Compare the company's 52-week price change to broader market indices such as the S&P 500. Identify any significant deviations and discuss their implications for stock performance.
Stock Volatility: Evaluate the company's stock volatility based on recent trading volumes. Assess how short-term fluctuations in stock price could impact the company’s market risk.
2. Financial Risk:
Debt-to-Equity Ratio: Analyze the company’s debt-to-equity ratio to assess its leverage position. Discuss potential risks related to high levels of debt and compare to industry standards.
Liquidity Ratios: Examine the company's current and quick ratios to evaluate its ability to meet short-term financial obligations. Discuss any liquidity concerns that could impact its financial stability.
Interest Coverage: Assess the company's ability to meet its interest payments through its interest coverage ratio. Discuss the potential implications of this ratio on the company’s financial risk.
Debt/EBITDA Ratio: Analyze the total debt-to-EBITDA ratio to evaluate the company’s ability to service its debt through operational earnings. Highlight any red flags related to high leverage.
Free Cash Flow/Debt Ratio: Review the company's free cash flow in relation to its total debt. Discuss how well the company is positioned to repay its debt using available cash flows.
3. Operational Risk:
P/E Ratio: Analyze the company’s trailing price-to-earnings (P/E) ratio. Compare this to industry peers to determine if the stock is overvalued or undervalued.
P/B Ratio: Evaluate the company’s price-to-book (P/B) ratio to assess how the market values the company’s assets. Discuss the implications for potential growth or financial stability.
Profit Margins: Examine the company's profit margins, including gross, operating, and net margins. Discuss the company’s operational efficiency and its ability to generate sustainable profits.
Revenue Growth: Analyze the company’s revenue growth rate over the past period. Identify key drivers of growth and assess the company’s potential for continued expansion.
Operating Cash Flow: Review the company’s operating cash flow to evaluate its ability to generate cash from core operations. Discuss how cash flow supports the company’s financial health and operational risk.
Return on Assets (ROA): Evaluate the company's return on assets (ROA) to assess how effectively the company uses its assets to generate profits.
Return on Equity (ROE): Analyze the company’s return on equity (ROE) to measure how efficiently the company generates returns for shareholders.
4. Corporate Governance Risk:
Insider Ownership: Assess the percentage of insider ownership and discuss its potential impact on governance and decision-making. Consider whether insider control could lead to misaligned interests.
Institutional Ownership: Evaluate the level of institutional ownership and its implications for market confidence in the company’s governance practices.
Audit Risk: Review the company's audit risk and assess the likelihood of financial reporting issues. Discuss the company’s strategies to mitigate audit-related risks.
Board Risk: Analyze the effectiveness of the company’s board in overseeing management and ensuring sound governance. Discuss the potential risks related to board composition and governance practices.
Compensation Risk: Assess the company’s executive compensation structure and discuss the potential risks of misaligned incentives between management and shareholders.
Shareholder Rights Risk: Evaluate the risks related to shareholder rights and governance practices. Discuss any potential issues related to unequal treatment of shareholders.
Overall Governance Risk: Provide a comprehensive assessment of the company’s governance risk, including any significant red flags in its governance structure or practices.
5. Key Risk Indicators:
Identify and explain 3-5 key risk indicators that stand out as particularly significant or unusual. Discuss how these metrics could affect the company’s overall risk profile and compare them to industry standards.
For each indicator, provide a detailed analysis of its short-term and long-term implications on the company’s financial stability and market position.
6. Risk Mitigation Strategy:
Propose risk mitigation strategies based on the identified key risks. Recommend actionable steps that the company could take to reduce market, financial, and governance risks to ensure long-term sustainability.
Provide your comprehensive risk analysis report in the following format:

[Company Overview]
Summarize the company's core business activities, key markets, and recent strategic developments.

[Risk Analysis]

Market Risk: Provide an analysis based on the market risk indicators above.
Financial Risk: Deliver a detailed analysis of the company’s financial risk based on the liquidity, debt, and profitability metrics.
Operational Risk: Discuss the company’s operational risks, including efficiency, profitability, and cash flow generation.
Corporate Governance Risk: Offer an in-depth analysis of governance-related risks.
[Key Risk Indicators]
Identify and discuss the most important risk indicators and their potential impact on the company’s risk profile.

[Risk Mitigation Strategy]
Provide recommendations on how the company could address and mitigate its key risks.

[Final Recommendation]
Acquisition Recommendation (Risk): (Strongly Recommend/Recommend/Neutral/Not Recommend/Strongly Not Recommend)
Conclude with an overall risk assessment, summarizing the key risks and their potential impact on the company’s future performance or acquisition decision.

"""

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional financial analyst. Use the MA_Info_Tool to obtain financial information about the company, then conduct an analysis."),
    ("human", template),
    ("human", "Analyze the risk of the company with stock symbol {stock_symbol} and provide acquisition advice."),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def analyze_company_risk(stock_symbol: str) -> Dict:
    result = agent_executor.invoke({
            "stock_symbol": stock_symbol,
            "input": f"Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."
    })
    
    # Create the result directory in the parent directory
    result_dir = Path(current_dir).parent / f"MAadvisor-main/result/{stock_symbol}/Risk"
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the English report to a file
    english_report_path = result_dir / f"{stock_symbol}_risk_analysis.md"
    with open(english_report_path, "w", encoding="utf-8") as f:
        f.write(result['output'])
    
    print(f"English risk analysis report saved to: {english_report_path}")
    
    # Generate Japanese translation
    translation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional translator specializing in financial documents. Translate the following risk analysis report from English to Japanese."),
        ("human", "{input}")
    ])
    
    translation_chain = translation_prompt | ChatOpenAI(temperature=0.3, model="gpt-4o-mini")

    
    japanese_translation = translation_chain.invoke({
        "input": result['output']
    })
    
    # Save the Japanese report to a file
    japanese_report_path = result_dir / f"{stock_symbol}_risk_analysis_japanese.md"
    with open(japanese_report_path, "w", encoding="utf-8") as f:
        f.write(japanese_translation.content)
    
    print(f"日本語のリスク分析のレポートが保存されました:: {japanese_report_path}")
    
    return result
