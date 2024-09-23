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
    valuation_data = ma_info_tool.run({"symbol": symbol, "info_type": "valuation"})
    return valuation_data if valuation_data else "Unable to retrieve valuation information."

# Create tools list
tools = [
    StructuredTool.from_function(
        func=run_ma_info_tool,
        name="MA_Info_Tool",
        description="Get valuation information for the target company. Input is the stock symbol."
    )
]

# Create LLM (unchanged)
llm = ChatOpenAI(temperature=0.5, max_tokens=4096, model="gpt-4o-mini")

template = """
Before providing the valuation analysis, use the MA_Info_Tool to gather comprehensive financial data for the stock symbol {stock_symbol}. If the tool fails to return any financial data, respond with "I do not have the necessary valuation information to proceed with the analysis."

Conduct a thorough and analytical valuation review covering the following areas:

Valuation Metrics:

Price-to-Earnings (P/E) Ratio: Analyze the current P/E ratio, explaining how the market is valuing the company's earnings. Discuss whether a high or low P/E ratio suggests market optimism or pessimism about the company's future earnings potential.
Price-to-Book (P/B) Ratio: Evaluate the P/B ratio to assess the company’s value relative to its book value. Discuss what this implies about market expectations for the company's assets and their ability to generate future returns.
Enterprise Value/EBITDA (EV/EBITDA): Examine the EV/EBITDA ratio, which reflects the company’s valuation based on its operational earnings. Explain how this metric compares to peers and industry standards, and what it suggests about the company’s operational efficiency.
PEG Ratio: Assess the PEG ratio, which adjusts the P/E ratio based on earnings growth. Analyze whether the company is overvalued or undervalued relative to its growth rate.
Comparison with Industry Peers and Historical Trends:

Compare each valuation metric to industry peers and historical averages. Highlight significant deviations or patterns that may indicate if the company is trading at a premium, discount, or fair value.
Discuss any major shifts in these metrics over time and their implications for future valuation and acquisition considerations.
Valuation Implications:

Provide a well-reasoned interpretation of the company’s overall valuation. Summarize whether the company is overvalued, undervalued, or fairly valued, and explain what this may mean for both short-term and long-term acquisition strategies.
Discuss the implications of these valuation metrics in the context of an acquisition. Consider how the company’s current market valuation aligns with its future growth potential and operational performance.
Final Recommendation:

Based on your analysis, provide a recommendation regarding the company’s valuation.
Possible recommendations: "Overvalued", "Undervalued", or "Fairly Valued."
Justify your recommendation by summarizing the key valuation factors that influenced your decision and what this implies for an acquisition decision.
Provide your valuation analysis report in the following format:

[Valuation Analysis Report]
1. Company Overview
Provide a brief summary of the company, including its industry and core activities. Highlight any major factors that could influence its market valuation.

2. Valuation Metrics
P/E Ratio: (Provide detailed analysis based on the points mentioned above)
P/B Ratio: (Provide detailed analysis based on the points mentioned above)
EV/EBITDA: (Provide detailed analysis based on the points mentioned above)
PEG Ratio: (Provide detailed analysis based on the points mentioned above)
3. Comparison with Industry Peers and Historical Trends
(Deliver a detailed analysis of how the company’s valuation metrics compare to its peers and historical performance)

4. Valuation Implications
(Summarize the implications of the company’s valuation, highlighting both risks and opportunities for acquisition)


[Final Recommendation]
Acquisition Recommendation (valuation): (Strongly Recommend/Recommend/Neutral/Not Recommend/Strongly Not Recommend)
(Provide a clear recommendation on whether the company is overvalued, undervalued, or fairly valued, and justify your decision)
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional financial analyst. Use the MA_Info_Tool to obtain financial information about the company, then conduct an analysis."),
    ("human", template),
    ("human", "Analyze the valuation of the company with stock symbol {stock_symbol} and provide acquisition advice."),
    ("placeholder", "{agent_scratchpad}")
])

# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)

# Create agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def analyze_company_valuation(stock_symbol: str) -> Dict:
    result = agent_executor.invoke({
            "stock_symbol": stock_symbol,
            "input": f"Analyze the financial situation of the company with stock symbol {stock_symbol} and provide acquisition advice."
    })
    
    # Create the result directory in the parent directory
    result_dir = Path(current_dir).parent / f"MAadvisor-main/result/{stock_symbol}/Valuation"
    result_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the English report to a file
    english_report_path = result_dir / f"{stock_symbol}_valuation_analysis.md"
    with open(english_report_path, "w", encoding="utf-8") as f:
        f.write(result['output'])
    
    print(f"English valuation analysis report saved to: {english_report_path}")
    
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
    japanese_report_path = result_dir / f"{stock_symbol}_valuation_analysis_japanese.md"
    with open(japanese_report_path, "w", encoding="utf-8") as f:
        f.write(japanese_translation.content)
    
    print(f"日本語の価値分析のレポートが保存されました:: {japanese_report_path}")
    
    return result
