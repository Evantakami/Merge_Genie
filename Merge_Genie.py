import sys
from pathlib import Path
import os
from langchain_openai import ChatOpenAI
import concurrent.futures

current_dir = Path.cwd()
agents_dir = current_dir / 'agents'
tools_dir = current_dir / 'tools'
sys.path.append(str(agents_dir.resolve()))
sys.path.append(str(tools_dir.resolve()))
os.environ["OPENAI_API_KEY"] = ""

from risk_advisor import analyze_company_risk
from efficiency_advisor import analyze_company_efficiency
from growth_advisor import analyze_company_growth
from management_advisor import analyze_company_management
from valuation_advisor import analyze_company_valuation
from finance_advisor import analyze_company_finance

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

def save_report(report_content, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        if isinstance(report_content, dict):
            f.write(report_content.get('text', str(report_content)))
        else:
            f.write(str(report_content))
    print(f"Report saved to: {file_path}")

# レポート生成用プロンプト作成
summary_template = """
**Target Company:** {target_company}

---

**[Task Description]**

As an M&A Genie, your goal is to provide a final acquisition recommendation for the target company. You must synthesize the final recommendations from the six evaluation reports into a comprehensive acquisition strategy. Focus on integrating the key suggestions from each report without reanalyzing them in detail.

**Note:** The output must be formatted in Markdown (MD). Use headings, bold text, and lists appropriately.

---

**[Synthesis Steps]**

1. **Risk Assessment**
   - **Review:** Review the final recommendation in the {risk_assessment}.
   - **Analyze:** Identify how the risks influence the acquisition decision.
   - **Summarize (200 words):** Summarize whether the risks support or hinder the acquisition.

2. **Efficiency Assessment**
   - **Review:** Review the final recommendation in the {efficiency_assessment}.
   - **Analyze:** Analyze how operational efficiency impacts the acquisition.
   - **Summarize (200 words):** Summarize the effect of efficiency on the acquisition.

3. **Growth Assessment**
   - **Review:** Review the final recommendation in the {growth_assessment}.
   - **Analyze:** Assess the company’s growth potential and its justification for acquisition.
   - **Summarize (200 words):** Summarize how growth potential affects the acquisition decision.

4. **Management Assessment**
   - **Review:** Review the final recommendation in the {management_assessment}.
   - **Analyze:** Evaluate the management team’s performance and strategy in relation to the acquisition.
   - **Summarize (200 words):** Summarize management’s contribution to the acquisition decision.

5. **Valuation Assessment**
   - **Review:** Review the final recommendation in the {valuation_assessment}.
   - **Analyze:** Assess whether the company’s valuation supports the acquisition.
   - **Summarize (200 words):** Summarize how valuation affects the acquisition decision.

6. **Financial Assessment**
   - **Review:** Review the final recommendation in the {finance_assessment}.
   - **Analyze:** Analyze the company’s financial health and its relevance to the acquisition.
   - **Summarize (200 words):** Summarize how financial health impacts the acquisition decision.

---

**[Final Acquisition Recommendation]**

- **Integration:** Integrate the final recommendations from each report and provide a comprehensive judgment on the company’s suitability for acquisition.
- **Decision:** Provide a final recommendation: **Acquire**, **Wait and Monitor**, or **Do Not Acquire**, and explain how each assessment contributes to the overall decision.

"""

generate_report_prompt = PromptTemplate(
    input_variables=["target_company", "risk_assessment", "efficiency_assessment", "growth_assessment", 
                     "management_assessment", "valuation_assessment", "finance_assessment"],
    template=summary_template
)

# レポート通訳用の ChatPromptTemplate作成し
translate_prompt = ChatPromptTemplate.from_messages([ 
    ("system", 
     """You are a professional translator specializing in financial and corporate documents, with a focus on translating M&A reports. Ensure that the translation is formal, uses precise financial terminology, and is suited for Japanese executives or financial advisors.
     When translating, always keep the following structure:
     - Translate '1. Risk Assessment Summary:' as '1. リスク評価サマリー：'
     - Translate '2. Efficiency Assessment Summary:' as '2. 効率性評価サマリー：'
     - Translate '3. Growth Assessment Summary:' as '3. 成長評価サマリー：'
     - Translate '4. Management Assessment Summary:' as '4. 経営評価サマリー：'
     - Translate '5. Valuation Assessment Summary:' as '5. バリュエーション評価サマリー：'
     - Translate '6. Financial Assessment Summary:' as '6. 財務評価サマリー：'
     - Translate '[Final Acquisition Recommendation]' as '最終アドバイス'
     Ensure that the translation follows this structure, and use local Japanese financial terminology where appropriate。"""
    ),
    ("human", "{input}")
])

# レポート生成用 LLMChain
llm = ChatOpenAI(temperature=0.5, max_tokens=16000, model="gpt-4o-mini")
generate_report_chain = LLMChain(llm=llm, prompt=generate_report_prompt)

# レポート通訳用 LLMChain
translate_chain = LLMChain(llm=llm, prompt=translate_prompt)

# 各種agentの結果を並行処理するための関数

def fetch_assessment_data(target_company):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            "risk": executor.submit(analyze_company_risk, target_company),
            "efficiency": executor.submit(analyze_company_efficiency, target_company),
            "growth": executor.submit(analyze_company_growth, target_company),
            "management": executor.submit(analyze_company_management, target_company),
            "valuation": executor.submit(analyze_company_valuation, target_company),
            "finance": executor.submit(analyze_company_finance, target_company)
        }

        results = {key: future.result() for key, future in futures.items()}
    
    return results

# Agentで情報収集/まとめ

def generate_and_save_reports(target_company):
    stock_symbol = target_company
    result_dir = Path.cwd().parent / f"MAadvisor-main/result/{stock_symbol}"
    
    folders = ["Risk", "Efficiency", "Growth", "Management", "Valuation", "Finance", "Final"]
    for folder in folders:
        (result_dir / folder).mkdir(parents=True, exist_ok=True)

    assessments = fetch_assessment_data(target_company)

    # 英語レポートを作成
    final_report = generate_report_chain.invoke({
        "target_company": target_company,
        "risk_assessment": assessments["risk"],
        "efficiency_assessment": assessments["efficiency"],
        "growth_assessment": assessments["growth"],
        "management_assessment": assessments["management"],
        "valuation_assessment": assessments["valuation"],
        "finance_assessment": assessments["finance"]
    })

    if isinstance(final_report, dict):
        final_report = final_report.get('text', str(final_report))

    # 英語レポートを保存
    english_report_path = result_dir / "Final" / f"{stock_symbol}_final_report.md"
    save_report(final_report, english_report_path)

    # 日本語に通訳
    japanese_translation = translate_chain.invoke({
        "input": final_report
    })

    if isinstance(japanese_translation, dict):
        japanese_translation = japanese_translation.get('text', str(japanese_translation))

    # 日本語レポートを保存
    japanese_report_path = result_dir / "Final" / f"{stock_symbol}_final_report_japanese.md"
    save_report(japanese_translation, japanese_report_path)

    return result_dir

import gradio as gr
from pathlib import Path
import sys

current_dir = Path.cwd()
agents_dir = current_dir / 'agents'
tools_dir = current_dir / 'tools'
sys.path.append(str(agents_dir.resolve()))
sys.path.append(str(tools_dir.resolve()))

def read_report(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"レポートファイルが見つかりません: {file_path}"
    except Exception as e:
        return f"レポートの読み込み中にエラーが発生しました: {str(e)}"

def analyze_company(stock_symbol):
    generate_and_save_reports(stock_symbol)
    
    result_dir = Path.cwd().parent / f"MAadvisor-main/result/{stock_symbol}/"
    
    reports = [
        f"Risk/{stock_symbol}_risk_analysis_japanese.md",
        f"Efficiency/{stock_symbol}_efficiency_analysis_japanese.md",
        f"Growth/{stock_symbol}_growth_analysis_japanese.md",
        f"Management/{stock_symbol}_management_analysis_japanese.md",
        f"Valuation/{stock_symbol}_valuation_analysis_japanese.md",
        f"Finance/{stock_symbol}_financial_analysis_japanese.md",
        f"Final/{stock_symbol}_final_report_japanese.md"
    ]
    
    return [read_report(result_dir / file_path) for file_path in reports]

import gradio as gr

with gr.Blocks(theme=gr.themes.Soft(), css="""
    #header {
        text-align: center;
        margin-bottom: 20px;
        font-family: 'Roboto', sans-serif;
        color: #f0f0f0;
    }

    #input-box {
        background-color: #2c3e50;
        color: #ffffff;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #ccc;
    }

    #analyze-button {
        background: linear-gradient(90deg, #4caf50, #2e7d32);
        color: white;
        border-radius: 30px;
        transition: all 0.3s ease;
        padding: 12px 20px;
    }

    #analyze-button:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .gradio-container {
        max-width: 600px;
        margin: auto;
        padding: 25px;
        background-color: #1c2833;
        border-radius: 12px;
        box-shadow: 0 5px 8px rgba(0, 0, 0, 0.08);
    }

    body {
        background-color: #1c2833;
        color: #ffffff;
    }

    h1, h2, p {
        color: #f0f0f0;
    }

    .markdown-output {
        color: #f0f0f0;
    }

    .gr-tab-item {
        background-color: #2e4053;
        color: #f0f0f0;
    }




""") as demo:

    gr.Markdown("""
    <h1 style="font-size: 2.5em; margin-bottom: 10px;">M&A Genie 🧞‍♂️</h1>
    <p style="font-size: 1.2em;">M&A Genieは、企業の未来を見通し、最適なM&Aの意思決定をお手伝いします✨<br>
    証券コードを入力し、魔法の「分析」ボタンを押して、アドバイスを手に入れましょう🔍💼</p>

    """, elem_id="header")

    with gr.Row():
        input_text = gr.Textbox(
            placeholder="分析したい企業の証券コードを教えてください！🧞‍♂️ (例: 4901.T)",
            show_label=False,
            elem_id="input-box"
        )
        analyze_btn = gr.Button("🔍 分析", elem_id="analyze-button")

    with gr.Tabs():
        with gr.TabItem("📊 リスク評価"):
            risk_output = gr.Markdown()
        with gr.TabItem("⚙️ 効率性評価"):
            efficiency_output = gr.Markdown()
        with gr.TabItem("🌱 成長性評価"):
            growth_output = gr.Markdown()
        with gr.TabItem("🏢 経営評価"):
            management_output = gr.Markdown()
        with gr.TabItem("💰 バリュエーション評価"):
            valuation_output = gr.Markdown()
        with gr.TabItem("📈 財務評価"):
            financial_output = gr.Markdown()
        with gr.TabItem("📝 最終報告"):
            final_output = gr.Markdown()

    outputs = [risk_output, efficiency_output, growth_output,
               management_output, valuation_output, financial_output,
               final_output]

    analyze_btn.click(
        analyze_company,
        inputs=input_text,
        outputs=outputs
    )

demo.launch()
