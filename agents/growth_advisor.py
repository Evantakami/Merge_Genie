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
    growth_data = ma_info_tool.run({"symbol": symbol, "info_type": "growth"})
    return growth_data if growth_data else "Unable to retrieve growth information."

# Create tools list
tools = [
    StructuredTool.from_function(
        func=run_ma_info_tool,
        name="MA_Info_Tool",
        description="Get growth information for the target company. Input is the stock symbol."
    )
]

# Create LLM (unchanged)
llm = ChatOpenAI(temperature=0.5, max_tokens=4096, model="gpt-4o-mini")

template = """
Before providing the growth analysis, use the MA_Info_Tool to gather comprehensive financial data for the stock symbol {stock_symbol}. If the tool fails to return any financial data, respond with "I do not have the necessary growth information to proceed with the analysis."

Conduct a detailed and analytical growth potential review covering the following areas:

Revenue Growth: Analyze historical revenue growth rates, both year-over-year and quarter-over-quarter. Identify key factors driving the growth, such as product innovation, market expansion, or pricing strategies. Compare revenue growth to industry peers and assess whether the company is gaining or losing market share. Evaluate the sustainability of revenue growth, considering potential risks like competition, market saturation, or macroeconomic factors.

Earnings Growth: Assess the company’s historical and projected earnings growth rates. Highlight any key product lines or services contributing to earnings growth. Discuss how well the company is managing costs and improving operational efficiency to drive profit growth. Compare the company's earnings growth to industry averages, and identify any significant deviations or trends.

Market Expansion and Competitive Position: Analyze the company’s ability to enter new markets or regions. Evaluate current market share and competitive positioning within its core industry. Discuss the impact of strategic partnerships, acquisitions, or innovations that could enhance the company’s growth potential. Highlight any potential risks to market expansion, such as regulatory barriers, competition, or geopolitical issues.

Product and Innovation Pipeline: Evaluate the company’s research and development (R&D) efforts. Discuss the strength of its innovation pipeline, including any upcoming product releases or technological advancements. Assess the company’s ability to adapt to industry changes and capitalize on emerging market trends, such as digital transformation or sustainability initiatives.

Future Growth Catalysts: Identify potential growth drivers, such as new product launches, market diversification, strategic partnerships, or changes in consumer demand. Consider broader industry trends and how they align with the company’s long-term growth strategy. Highlight any upcoming catalysts that could significantly impact future growth, such as regulatory changes or disruptive technologies. Evaluate the role of mergers and acquisitions in enhancing the company’s growth prospects, if applicable.

Key Risks to Growth: Discuss any risks that could hinder the company’s growth, including market competition, changing consumer preferences, or supply chain disruptions. Evaluate how macroeconomic factors such as interest rates, inflation, or trade policies could affect the company’s growth potential. Highlight any internal risks, such as leadership changes or strategic misalignment, that could derail future growth plans.

Growth Metrics to Watch: Identify 3-5 critical growth-related metrics or trends that stand out due to significant deviations from industry norms or unusual patterns. For each metric:

Explain why it is significant and provide context through comparisons to industry averages or historical performance.
Discuss potential implications for the company’s growth trajectory, both in the short and long term.
Relate to how these metrics could influence a decision on the company’s growth potential.
Provide your comprehensive growth analysis report in the following format:

[Company Overview]
Provide a detailed summary of the company, including:

Core growth drivers (products, markets, etc.)
Current market position and competitive landscape
Key strategic initiatives driving future growth
[Growth Analysis]
Revenue Growth: (Deliver a detailed and critical analysis of revenue growth based on the points mentioned above)

Earnings Growth: (Deliver a detailed and critical analysis of earnings growth based on the points mentioned above)

Market Expansion and Competitive Position: (Deliver a detailed and critical analysis of the company's market position and potential for expansion)

Product and Innovation Pipeline: (Deliver a detailed analysis of the company’s innovation efforts and product pipeline)

Future Growth Catalysts: (Identify key drivers of future growth, highlighting risks and opportunities)

Key Risks to Growth: (Deliver a critical analysis of risks that may impede the company's growth trajectory)

Growth Metrics to Watch: (Deliver a detailed analysis of notable growth metrics and their impact on the company’s future performance)

[Final Recommendation]
Based on the growth analysis, provide a well-reasoned final recommendation on whether to proceed with an acquisition or investment in the company:

Acquisition Recommendation (Growth): (Strongly Recommend/Recommend/Neutral/Not Recommend/Strongly Not Recommend)

In your final recommendation:

Summarize the key growth drivers and risks that influenced your decision.
Provide a balanced view on the company’s long-term growth prospects, taking into account any potential challenges or opportunities.
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

def analyze_company_growth(stock_symbol: str) -> Dict:
    result = agent_executor.invoke({
            "stock_symbol": stock_symbol,
            "input": f"Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."
    })
    
    # Create the result directory in the parent directory
    result_dir = Path(current_dir).parent / f"MAadvisor-main/result/{stock_symbol}/Growth"
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the English report to a file
    english_report_path = result_dir / f"{stock_symbol}_growth_analysis.md"
    with open(english_report_path, "w", encoding="utf-8") as f:
        f.write(result['output'])
    
    print(f"English growth analysis report saved to: {english_report_path}")
    
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
    japanese_report_path = result_dir / f"{stock_symbol}_growth_analysis_japanese.md"
    with open(japanese_report_path, "w", encoding="utf-8") as f:
        f.write(japanese_translation.content)
    
    print(f"日本語の成長性分析のレポートが保存されました: {japanese_report_path}")
    
    return result
