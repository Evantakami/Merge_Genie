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
    efficiency_data = ma_info_tool.run({"symbol": symbol, "info_type": "efficiency"})
    return efficiency_data if efficiency_data else "Unable to retrieve efficiency information."


tools = [
    StructuredTool.from_function(
        func=run_ma_info_tool,
        name="MA_Info_Tool",
        description="Get efficiency information for the target company. Input is the stock symbol."
    )
]

# Create LLM (unchanged)
llm = ChatOpenAI(temperature=0.5, max_tokens=4096, model="gpt-4o-mini")

template = """
Before providing the efficiency analysis, use the MA_Info_Tool to gather comprehensive financial data for the stock symbol {stock_symbol}. If the tool fails to return any financial data, respond with "I do not have the necessary efficiency information to proceed with the analysis."

Conduct a deep and analytical efficiency review covering the following areas:

Operational Efficiency:

Provide a critical analysis of key efficiency metrics such as Return on Assets (ROA), Return on Equity (ROE), and Profit Margins (gross, operating, and net).
Discuss the company’s ability to convert its resources (assets and equity) into profits. Explain how these figures reflect the company’s operational efficiency.
Compare these metrics to industry averages or historical data, identifying any significant trends or deviations. Interpret what these trends may imply about the company's efficiency.
Highlight both risks and opportunities associated with the company’s operational efficiency. Discuss potential areas of improvement or emerging challenges that could impact future performance.
Liquidity and Solvency:

Examine the company's liquidity ratios, including the Current Ratio and Quick Ratio. Discuss the company’s ability to meet short-term obligations.
Analyze Debt-to-Equity Ratio and its implications on the company’s financial leverage. Evaluate how this affects the company's long-term solvency and financial stability.
Discuss Free Cash Flow and Operating Cash Flow to assess the company's cash generation efficiency. Comment on how these cash flows support operational activities, debt repayment, and future investments.
Identify financial risks or strengths related to liquidity and solvency. Highlight any red flags or particularly strong aspects that could influence the company's long-term prospects.
Cash Flow Efficiency:

Analyze the company's ability to generate positive operating cash flows. Evaluate how well the company converts sales into cash, supporting both short-term operations and long-term growth.
Discuss Free Cash Flow generation, focusing on its sufficiency for covering capital expenditures, dividends, or debt repayments.
Highlight any unusual patterns in cash flow metrics, especially deviations from industry standards or historical norms. Provide insights into how these trends could impact the company’s overall efficiency.
Efficiency Ratios:

Provide a detailed review of key efficiency ratios such as Revenue per Share, EPS (Earnings per Share), and forward EPS projections. Analyze how well the company is utilizing its resources to generate revenue and earnings.
Examine metrics such as PEG Ratio, Enterprise Value/EBITDA, and their relationship to the company’s growth potential and operational efficiency.
Compare these efficiency ratios to industry peers and historical averages. Provide an interpretation of whether the company is outperforming or underperforming its competitors.
Key Metrics to Watch:

Identify 3-5 specific efficiency-related metrics or trends that stand out due to significant deviations from industry norms, unusual patterns, or unexpected changes.
For each metric, explain its significance and provide context with comparisons where relevant.
Discuss potential implications, both short-term and long-term, for the company’s operational and financial performance.
Relate these metrics to industry benchmarks or historical data to highlight any anomalies or trends that could influence an acquisition decision.
Provide your comprehensive efficiency analysis report in the following format:

[Company Overview]

Provide a thorough summary of the company, including:

Core business activities and key product/service offerings
Market position, competitive advantages, and weaknesses
Recent significant events, strategic changes, or leadership shifts
[Efficiency Analysis]

Operational Efficiency:
(Deliver a detailed and critical analysis based on the points mentioned above)

Liquidity and Solvency:
(Deliver a detailed and critical analysis based on the points mentioned above)

Cash Flow Efficiency:
(Deliver a detailed and critical analysis based on the points mentioned above)

Efficiency Ratios:
(Deliver a detailed and critical analysis based on the points mentioned above)

[Key Metrics to Watch]
(Deliver a detailed analysis of the unusual or noteworthy metrics and their impact on the acquisition decision)

[Final Recommendation]
Based on the comprehensive efficiency analysis, provide a well-reasoned final recommendation on whether to proceed with the acquisition:

Acquisition Recommendation (Efficiency): (Strongly Recommend/Recommend/Neutral/Not Recommend/Strongly Not Recommend)

In your final recommendation:

Justify the recommendation by summarizing key efficiency-related factors (both risks and opportunities) that influenced your decision.
Discuss the potential impact of any highlighted efficiency risks and strengths on the acquisition decision.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional financial analyst. Use the MA_Info_Tool to obtain financial information about the company, then conduct an analysis."),
    ("human", template),
    ("human", "Analyze the growth of the company with stock symbol {stock_symbol} and provide acquisition advice."),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def analyze_company_efficiency(stock_symbol: str) -> Dict:
    result = agent_executor.invoke({
            "stock_symbol": stock_symbol,
            "input": f"Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."
    })
    
    # Create the result directory in the parent directory
    result_dir = Path(current_dir).parent / f"MAadvisor-main/result/{stock_symbol}/Efficiency"
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the English report to a file
    english_report_path = result_dir / f"{stock_symbol}_efficiency_analysis.md"
    with open(english_report_path, "w", encoding="utf-8") as f:
        f.write(result['output'])
    
    print(f"English efficiency analysis report saved to: {english_report_path}")
    
    # Generate Japanese translation
    translation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional translator specializing in financial and corporate documents, with a focus on translating efficiency analysis reports. Ensure that the translation is formal, uses precise financial terminology, and is suited for Japanese executives or financial advisors."),
        ("human", "{input}")
    ])

    
    translation_chain = translation_prompt | ChatOpenAI(temperature=1, model="gpt-4o-mini")

    
    japanese_translation = translation_chain.invoke({
        "input": result['output']
    })
    
    # Save the Japanese report to a file
    japanese_report_path = result_dir / f"{stock_symbol}_efficiency_analysis_japanese.md"
    with open(japanese_report_path, "w", encoding="utf-8") as f:
        f.write(japanese_translation.content)
    
    print(f"日本語の業務効率分析のレポート保存しました: {japanese_report_path}")
    
    return result
