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
    financial_data = ma_info_tool.run({"symbol": symbol, "info_type": "financial"})
    return financial_data if financial_data else "Unable to retrieve financial information."

# Create tools list
tools = [
    StructuredTool.from_function(
        func=run_ma_info_tool,
        name="MA_Info_Tool",
        description="Get financial information for the target company. Input is the stock symbol."
    )
]

# Create LLM (unchanged)
llm = ChatOpenAI(temperature=0.5, max_tokens=4096, model="gpt-4o-mini")

template = """
Before providing the financial analysis, use the MA_Info_Tool to gather comprehensive financial data for the stock symbol {stock_symbol}. If the tool fails to return any financial data, respond with "I do not have the necessary financial information to proceed with the analysis."

Conduct a deep and analytical financial review covering the following areas:

1. Profitability:
Provide a critical analysis of profit margins (gross, operating, and net profit margins). Go beyond the numbers to discuss why they are where they are, and what they indicate about the company’s operational efficiency.
Evaluate and interpret Return on Equity (ROE) and Return on Assets (ROA). What do these figures say about management's effectiveness and the company’s ability to generate profit from its resources?
Compare these metrics to industry averages and historical trends. Identify any significant deviations or patterns.
Discuss the implications of these profitability metrics, focusing on how they may influence the company’s financial performance and future sustainability. Highlight both risks and opportunities.
2. Financial Health:
Analyze short-term and long-term debt levels. Assess the company's leverage position and discuss the potential implications of its debt structure on future operations.
Examine liquidity ratios (current ratio, quick ratio). Provide not just the numbers but an interpretation—what do these ratios reveal about the company's ability to cover short-term obligations?
Evaluate operating cash flow and free cash flow. Discuss how cash generation capabilities support ongoing operations, debt repayment, and future growth investments.
Discuss the company's financial obligations and its ability to meet them under current and potential future conditions. Consider factors such as interest coverage ratios.
Identify financial risks or strengths. Highlight any red flags or particularly strong aspects of the company's financial health that could influence its future prospects.
3. Valuation:
Analyze the Price-to-Earnings (P/E) ratio. Explain how the market is valuing the company's earnings. Discuss what a high or low P/E may imply in the current market environment.
Evaluate the Price-to-Book (P/B) ratio. Assess the company’s value compared to its assets and book value.
Consider additional valuation metrics such as EV/EBITDA and PEG ratio. Discuss how these provide a more complete picture of the company's valuation relative to its earnings growth and operational efficiency.
Compare these ratios to industry peers and historical averages. Provide a well-reasoned interpretation of whether the company is overvalued, undervalued, or fairly valued.
Discuss valuation implications and what this may mean for an acquisition decision, considering both short-term and long-term perspectives.
4. Growth Potential:
Analyze historical growth rates for revenue and earnings. Highlight key drivers and obstacles for past performance.
Evaluate market share and competitive position in the industry. Consider how the company’s strategy aligns with broader market trends.
Consider industry trends and market opportunities that could impact future growth, particularly in emerging markets or innovative product lines.
Discuss analyst projections and compare them to the company’s internal growth strategies.
Identify catalysts for future growth, such as new products, market expansion, or strategic partnerships. Discuss any significant risks that could hinder this growth.
5. Key Metrics to Watch:
Identify 3-5 specific financial metrics or trends that stand out due to significant deviations from industry norms, unusual patterns, or unexpected changes.
For each metric:
Explain why it stands out, providing context and comparisons where relevant.
Discuss potential implications, both short-term and long-term, for the company’s financial health and future performance.
Relate to industry benchmarks or historical data to highlight any anomalies or significant trends.
Discuss how these unusual metrics could influence the acquisition decision, weighing both risks and opportunities.
Provide your comprehensive financial analysis report in the following format:
[Company Overview]
Provide a thorough summary of the company, including:

Core business activities and key product/service offerings
Market position, competitive advantages, and weaknesses
Recent significant events, strategic changes, or leadership shifts
[Financial Analysis]
Profitability:
(Deliver a detailed and critical analysis based on the points mentioned above)

Financial Health:
(Deliver a detailed and critical analysis based on the points mentioned above)

Valuation:
(Deliver a detailed and critical analysis based on the points mentioned above)

Growth Potential:
(Deliver a detailed and critical analysis based on the points mentioned above)

Key Metrics to Watch:
(Deliver a detailed analysis of the unusual or noteworthy metrics and their impact on the acquisition decision)

[Final Recommendation]
Based on the comprehensive financial analysis, provide a well-reasoned final recommendation on whether to proceed with the acquisition:

Acquisition Recommendation (Finance): (Strongly Recommend/Recommend/Neutral/Not Recommend/Strongly Not Recommend)
In your final recommendation:

Justify the recommendation by summarizing key factors (both risks and opportunities) that influenced your decision.
Discuss the potential impact of any highlighted financial risks and strengths on the acquisition decision.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional financial analyst. Use the MA_Info_Tool to obtain financial information about the company, then conduct an analysis."),
    ("human", template),
    ("human", "Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def analyze_company_finance(stock_symbol: str) -> Dict:
    result = agent_executor.invoke({
        "stock_symbol": stock_symbol,
        "input": f"Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."
    })
    
    # Create the result directory in the parent directory
    result_dir = Path(current_dir).parent / f"MAadvisor-main/result/{stock_symbol}/Finance"
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the English report to a file
    english_report_path = result_dir / f"{stock_symbol}_financial_analysis.md"
    with open(english_report_path, "w", encoding="utf-8") as f:
        f.write(result['output'])
    
    print(f"English financial analysis report saved to: {english_report_path}")
    
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
    japanese_report_path = result_dir / f"{stock_symbol}_financial_analysis_japanese.md"
    with open(japanese_report_path, "w", encoding="utf-8") as f:
        f.write(japanese_translation.content)
    
    print(f"日本語の金融面分析のレポートが保存されました:{japanese_report_path}")
    
    return result