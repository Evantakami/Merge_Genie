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
    management_data = ma_info_tool.run({"symbol": symbol, "info_type": "management"})
    return management_data if management_data else "Unable to retrieve management information."

# Create tools list
tools = [
    StructuredTool.from_function(
        func=run_ma_info_tool,
        name="MA_Info_Tool",
        description="Get management information for the target company. Input is the stock symbol."
    )
]

# Create LLM (unchanged)
llm = ChatOpenAI(temperature=0.5, max_tokens=4096, model="gpt-4o-mini")

template = """


Before providing the management analysis, use the MA_Info_Tool to gather comprehensive operational data for the stock symbol {stock_symbol}. If the tool fails to return any management data, respond with "I do not have the necessary operational information to proceed with the analysis."

Conduct a thorough analysis based on the following aspects of management and governance:

Executive Team:

Analyze the details of the top 5 executives, focusing on their names, roles, ages, and total compensation.
Discuss how the leadership team’s experience and roles contribute to the company’s strategic direction and operational performance. If applicable, note any unusual patterns in the composition of the team (e.g., age distribution or compensation discrepancies).
Compensation Structure:

Review the compensation levels for the top executives. If compensation is provided as a specific number, analyze whether the amounts are aligned with industry standards and the company's performance.
If compensation information is incomplete or non-monetary, discuss potential implications, such as whether compensation levels suggest alignment with shareholder interests.
Key Management Metrics:

Evaluate the provided management-related financial metrics, such as:
Insider Ownership: Analyze the percentage of company shares held by insiders. Discuss how this impacts alignment between management and shareholders.
Institutional Ownership: Consider the percentage of shares held by institutional investors and discuss how this reflects the market’s confidence in the management team.
Employee Headcount: Discuss the size of the company's workforce and any trends that may reflect management’s operational effectiveness.
Governance and Risk Metrics:

Review additional governance and risk indicators, including:
Dividend Payout Ratio: Analyze how management handles profits, whether it returns a significant portion to shareholders or reinvests in the business.
Return on Equity (ROE) and Return on Assets (ROA): Provide an interpretation of these key profitability metrics in the context of management’s effectiveness at using company resources to generate returns.
Key Observations:

Identify 3-5 significant trends or metrics from the provided data that stand out, such as unusual compensation levels, high insider ownership, or above-average returns.
Discuss how these factors could influence the acquisition decision, focusing on both risks and opportunities.
Provide your management analysis report in the following format:

[Company Overview]

Summarize the company’s leadership team and governance structure, highlighting key strengths and potential concerns based on the available data.
[Management Analysis]

Executive Team: (Provide a detailed analysis based on the points mentioned above)

Compensation Structure: (Provide a detailed analysis based on the points mentioned above)

Key Management Metrics: (Analyze the metrics provided such as insider ownership, institutional ownership, etc.)

Governance and Risk Metrics: (Deliver a detailed analysis based on payout ratios, ROE, ROA, and other risk factors)

Key Observations: (Discuss any notable metrics and trends that may impact the acquisition decision)

[Final Recommendation]

Based on the management analysis, provide a final recommendation on whether to proceed with the acquisition:
Acquisition Recommendation (Management): (Strongly Recommend/Recommend/Neutral/Not Recommend/Strongly Not Recommend)
Justify the recommendation by summarizing key management-related factors that could impact the company’s future performance.

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

def analyze_company_management(stock_symbol: str) -> Dict:
    result = agent_executor.invoke({
            "stock_symbol": stock_symbol,
            "input": f"Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."
    })
    
    # Create the result directory in the parent directory
    result_dir = Path(current_dir).parent / f"MAadvisor-main/result/{stock_symbol}/Management"
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the English report to a file
    english_report_path = result_dir / f"{stock_symbol}_management_analysis.md"
    with open(english_report_path, "w", encoding="utf-8") as f:
        f.write(result['output'])
    
    print(f"English management analysis report saved to: {english_report_path}")
    
    # Generate Japanese translation
    translation_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional translator specializing in financial and corporate documents, with a focus on translating management analysis reports. Ensure that the translation is formal, uses precise financial terminology, and is suited for Japanese executives or financial advisors."),
        ("human", "{input}")
    ])

    
    translation_chain = translation_prompt | ChatOpenAI(temperature=1, model="gpt-4o-mini")

    
    japanese_translation = translation_chain.invoke({
        "input": result['output']
    })
    
    # Save the Japanese report to a file
    japanese_report_path = result_dir / f"{stock_symbol}_management_analysis_japanese.md"
    with open(japanese_report_path, "w", encoding="utf-8") as f:
        f.write(japanese_translation.content)
    
    print(f"日本語の経営陣分析のレポートが保存されました:: {japanese_report_path}")
    
    return result
