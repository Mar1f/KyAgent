# KyAgent - 考研信息查询系统

基于LangChain框架和MySQL数据库的考研信息查询系统，具有智能查询、数据可视化和最新信息检索功能。

## 功能特点

- **智能查询**：通过自然语言提问获取考研相关信息
- **数据分析与浏览**：可视化展示考研数据（按学校、专业、专业门类），提供多维度数据浏览
- **搜索引擎集成**：获取最新考研信息（通过LangChain集成Tavily/Serper搜索引擎）
- **数据库存储**：使用MySQL存储历年考研数据 (通过直接加载Excel文件)
- **用户友好界面**：使用Streamlit构建简洁易用的交互界面

## 技术栈

- **LangChain**：大语言模型框架 (Agent, Tools)
- **MySQL**：数据库
- **SQLAlchemy**: Python SQL Toolkit and ORM
- **Streamlit**：前端界面
- **OpenAI API**：智能问答能力 (e.g., GPT-4 Turbo)
- **Tavily/Serper API**：搜索引擎集成
- **Plotly**: 数据可视化
- **Pandas**: Data manipulation

## 安装说明

### 前提条件

- Python 3.10+
- MySQL 8.0+
- Conda (推荐用于环境管理)
- 相关API密钥（OpenAI, Tavily, Serper - 获取并配置在`.env`文件中）
- 原始考研数据 `.xlsx` 或 `.xls` 文件放置在项目根目录下的 `data` 文件夹中。

### 安装步骤

1.  **克隆代码库**
    ```bash
    git clone <repository-url>
    cd KyAgent
    ```

2.  **创建并激活Conda环境**
    ```bash
    # conda create -n py310 python=3.10 # 如果环境不存在
    conda activate py310
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    # 特别注意：确保MySQL驱动已安装
    # pip install mysql-connector-python pymysql 
    ```

4.  **配置环境变量**
    -   复制 `.env.example` 文件为 `.env`。
    -   **编辑 `.env` 文件**，填入你的MySQL数据库连接信息 (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME) 和申请的API密钥 (OPENAI_API_KEY, TAVILY_API_KEY, SERPER_API_KEY)。

5.  **(重要) 调整数据加载配置**
    -   打开 `load_data.py`。
    -   找到 `COL_MAP_SCHOOL` 和 `COL_MAP_PROGRAM` 字典。
    -   **仔细核对并修改这两个字典中的 *键* (Excel Header)，使其与你放在 `data` 目录下的 Excel 文件中的实际列标题完全匹配。** 这是确保数据正确加载的关键。
    -   (可选) 检查 `DISCIPLINE_CODE_MAP` 是否符合你的专业门类划分标准。

6.  **初始化数据库并加载数据**
    -   确保你的MySQL服务正在运行。
    -   运行设置脚本：
        ```bash
        python setup.py
        ```
    -   此脚本会：
        -   连接MySQL并创建数据库（如果需要）。
        -   执行 `scripts/load_data.py`。
        -   `load_data.py` 会根据 `app/database/models.py` 创建表结构（如果需要），然后读取 `data` 目录下的 Excel 文件，根据你的列名映射配置，将数据加载到数据库中。
    -   **仔细查看 `setup.py` 脚本的输出**，检查是否有错误信息，特别是数据库连接错误或数据加载过程中的警告。

## 运行应用

1.  **激活Conda环境**
    ```bash
    conda activate py310
    ```
2.  **启动应用**
    ```bash
    python run.py
    ```
    或者直接使用Streamlit:
    ```bash
    streamlit run app/app.py
    ```
3.  在浏览器中打开显示的地址 (通常是 `http://localhost:8501`)。

## 系统结构
我想知道2023年南京邮电大学计算机技术专业复试线是多少
```
KyAgent/
│
├── app/                  # Streamlit应用核心代码
│   ├── api/              # LangChain及API相关设置 (langchain_setup.py)
│   ├── database/         # 数据库交互 (models.py, db_manager.py)
│   ├── utils/            # 通用工具 (common.py, prompt_templates.py)
│   ├── components/       # (可选) Streamlit自定义组件
│   ├── __init__.py
│   └── app.py            # Streamlit主应用文件
│
├── data/                 # 存放原始Excel数据文件 (.xlsx, .xls)
│
├── scripts/              # 辅助脚本
│   └── load_data.py      # Excel数据加载和数据库插入逻辑
│
├── logs/                 # (自动生成) 日志文件
│
├── .env                  # 环境变量 (数据库密码, API密钥 - **不提交到Git**)
├── .env.example          # 环境变量示例文件
├── config.py             # 读取.env并配置应用变量 (如DATABASE_URL)
├── requirements.txt      # Python依赖列表
├── setup.py              # 数据库创建和数据加载的入口脚本
├── run.py                # 运行Streamlit应用的便捷脚本
└── README.md             # 项目说明文件
```

## 使用示例

1.  **智能查询**：在"智能查询"页面输入自然语言问题，如 "北京大学计算机考研分数线近三年变化趋势？" 或 "对比清华和北大的软件工程专硕"
2.  **数据分析与浏览**：在"数据分析"页面选择维度（学校/专业/门类）和年份，查看数据表格和可视化图表。

## 注意事项

-   **MySQL服务**：运行 `setup.py` 和应用前，请确保MySQL服务已启动且可访问。
-   **API密钥**：所有需要的API密钥（OpenAI, Tavily, Serper）必须在 `.env` 文件中正确配置。
-   **列名映射**：`load_data.py` 中的 `COL_MAP_SCHOOL` 和 `COL_MAP_PROGRAM` 必须与你的Excel文件列名精确匹配。
-   **数据更新**：如果更新了 `data` 目录下的 Excel 文件，需要重新运行 `python setup.py` 来加载新数据（注意：当前脚本是追加数据，如需清空旧数据需手动操作或修改脚本）。
-   **依赖安装**：确保 `requirements.txt` 中的所有库都已成功安装在 `py310` 环境中。

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。

## 许可证

[MIT License](LICENSE) # (如果需要，添加LICENSE文件) 