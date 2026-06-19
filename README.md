# KyAgent - 考研信息查询系统

KyAgent 是一个基于 **Streamlit + MySQL + LangChain** 的考研信息查询系统，支持：

- 历年复试分数线数据导入与查询
- 按学校 / 专业 / 学科门类的数据分析与可视化
- 结合数据库与联网搜索的自然语言问答
- 基于数据库用户表的登录注册

---

## 技术栈

- **Python 3.10+**
- **Streamlit**：前端界面
- **MySQL**：数据存储
- **SQLAlchemy**：ORM / 数据访问
- **LangChain**：Agent 与工具编排
- **OpenAI API**：大模型问答能力
- **Tavily / Google Serper**：联网搜索补充
- **Plotly / Pandas**：数据分析与可视化

---

## 当前目录结构

```text
KyAgent/
├── app/
│   ├── api/
│   │   └── langchain_setup.py
│   ├── data/
│   │   ├── 20-22研究生复试分数线.xlsx
│   │   ├── 2023研究生复试分数线.xlsx
│   │   ├── 2024研究生复试分数线.xlsx
│   │   └── china_province.GeoJSON
│   ├── database/
│   │   ├── db_manager.py
│   │   ├── load_data.py
│   │   └── models.py
│   ├── utils/
│   │   ├── common.py
│   │   └── prompt_templates.py
│   ├── __init__.py
│   └── app.py
├── app_config.py
├── run.py
├── setup.py
├── requirements.txt
├── test_openai_api.py
└── README.md
```

> 注意：原始数据文件当前位于 `app/data/`，不是根目录 `data/`。

---

## 功能说明

### 1. 智能查询
在“智能查询”页面中输入自然语言问题，例如：

- `2023年南京邮电大学计算机技术专业复试线是多少？`
- `对比清华和北大的软件工程专硕复试线`
- `北京大学计算机考研分数线近三年变化趋势？`

系统会优先查询 MySQL 中的结构化历史数据，并在需要时调用搜索工具补充最新信息。

### 2. 数据分析与浏览
支持以下维度：

- 按学校分析
- 按专业分析
- 按专业门类浏览

系统会展示表格、趋势图、分布图与省份分布图。

### 3. 数据导入
通过 `setup.py` 建库并执行 `app/database/load_data.py`，从 `app/data/*.xlsx` 导入数据到 MySQL。

当前导入流程已经支持**重复执行不再持续追加重复 Program 记录**。

---

## 环境准备

### 前提条件

- Python 3.10+
- MySQL 8.0+
- 可正常访问 OpenAI / 搜索 API 的网络环境

### 推荐做法

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

然后安装依赖：

```bash
pip install -r requirements.txt
```

当前 `requirements.txt` 已整理为 UTF-8 的最小运行依赖集合，适合作为项目安装入口。

---

## 配置环境变量

在项目根目录创建 `.env` 文件。可以先复制样例：

```bash
cp .env.example .env
```

需要的主要配置项：

- 数据库：`DB_USER`、`DB_PASSWORD`、`DB_HOST`、`DB_PORT`、`DB_NAME`
- 大模型：`OPENAI_API_KEY`、`OPENAI_API_URL`、`MODEL`
- 搜索：`TAVILY_API_KEY`、`SERPER_API_KEY`
- 登录 Cookie：`AUTH_COOKIE_KEY`

完整样例见 `.env.example`。

---

## 初始化数据库并加载数据

第一次运行前，先确保 MySQL 服务已启动，并且 `.env` 中配置的是**真实可连接**的数据库账号。

执行：

```bash
python setup.py
```

此脚本会：

1. 使用 `.env` 中的配置连接 MySQL
2. 创建数据库（如果不存在）
3. 创建表结构
4. 读取 `app/data/*.xlsx` 并导入数据

如果你修改了 Excel 文件内容，可以再次运行：

```bash
python setup.py
```

或直接运行：

```bash
python app/database/load_data.py
```

---

## 启动应用

方式一：

```bash
python run.py
```

方式二：

```bash
streamlit run app/app.py
```

启动后，按 Streamlit 提示在浏览器打开地址（通常是 `http://localhost:8501`）。

---

## 测试 OpenAI 连接

如果你想单独测试 OpenAI 连接：

```bash
python test_openai_api.py
```

该脚本会读取 `.env` 中的 OpenAI 配置，并通过当前配置的代理 / base URL 发起一次简单请求。

---

## 当前实现说明

### 配置行为

- `app_config.py` 作为统一配置出口
- 入口脚本（如 `run.py`、`setup.py`、`test_openai_api.py`）负责加载 `.env`
- 缺失关键环境变量时，会在入口阶段明确报错

### 数据导入行为

- 学校数据按学校名去重
- 专业数据按导入键查找后更新或创建
- 重复执行导入时，不会继续无上限追加同一批 Program 数据

### 学科统计行为

首页学科门类统计已改为数据库聚合查询，不再为了计数全量加载全部 `Program` 实体。

---

## 常见问题

### 1. `Access denied for user ...`
说明 `.env` 中的数据库用户名或密码不正确，或该账号没有权限。

### 2. `Unknown database ...`
说明 `.env` 中配置的数据库名不存在。先运行：

```bash
python setup.py
```

### 3. `OPENAI_API_KEY` 缺失
请检查 `.env` 中是否配置了正确的 OpenAI Key。

### 4. 地图不显示
请确认 `app/data/china_province.GeoJSON` 文件存在且格式正确。

---

## 后续优化方向

当前仓库仍有一些可继续优化的点：

- Prompt 结构收敛
- `app/app.py` 拆分为更清晰的页面 / service 结构
- 更完整的测试体系
- 更细粒度的测试与自动化校验

---

## 许可证

本项目采用 [MIT License](LICENSE)。
