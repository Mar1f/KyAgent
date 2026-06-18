import streamlit as st
import pandas as pd
# import matplotlib.pyplot as plt # Matplotlib might not be needed if using Plotly
import numpy as np
import time
import sys
import os
import plotly.express as px
import plotly.graph_objects as go
import json # <-- Import json
# --- ADDED IMPORTS for Markdown Parsing & Plotting ---
import re
from io import StringIO 
# --- ADDED IMPORTS FOR AUTH ---
import streamlit_authenticator as stauth
import bcrypt
# --- END ADDED IMPORTS ---

# --- Ensure project root is in sys.path --- 
# Get the directory containing the 'app' folder (project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root) # Insert at beginning
    print(f"[Debug] Added to sys.path: {project_root}") # Optional debug print
# --- End Path Addition ---

# Now imports should work relative to the project root
try:
    from app.api.langchain_setup import LangChainManager
    from app.database.db_manager import DatabaseManager
    from app.database.models import Program, User # Import User model
    from sqlalchemy.orm import joinedload # Import joinedload if needed elsewhere, maybe discipline browsing
except ImportError as e:
    st.error(f"Fatal Error: Could not import necessary modules: {e}")
    st.error(f"Project Root added to path: {project_root}")
    st.error(f"Current sys.path: {sys.path}")
    st.error("Please ensure the project structure is correct, the User model exists in models.py, and all dependencies are installed.")
    st.stop() # Stop execution if imports fail

# init_db is primarily for setup, not usually called directly by the app
# from app.database.models import init_db

# --- Database Helper Functions for Users ---

# @st.cache_data # Cache user data for a short time? Maybe not for auth.
def fetch_all_users_from_db():
    """Fetches all users from the database for the authenticator."""
    db = DatabaseManager()
    try:
        users = db.session.query(User).all()
        # Convert User objects to dictionary format needed by authenticator
        user_list = [{
            "username": user.username,
            "name": user.name,
            "password": user.password # Assuming password field stores the hash
        } for user in users]
        return user_list
    except Exception as e:
        st.error(f"Error fetching users from database: {e}")
        # If the User table doesn't exist yet, this will fail.
        # Consider handling the specific exception for "table not found"
        # For now, return empty list on error.
        return []
    finally:
        db.close()

def add_user_to_db(name, username, hashed_password):
    """Adds a new user to the database."""
    db = DatabaseManager()
    try:
        # Check if username already exists
        existing_user = db.session.query(User).filter(User.username == username).first()
        if existing_user:
            st.error(f"Username '{username}' already exists.")
            return False

        # Create new user
        new_user = User(name=name, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        st.success(f"User '{username}' registered successfully.")
        return True
    except Exception as e:
        db.session.rollback() # Rollback in case of error
        st.error(f"Database error during registration: {e}")
        return False
    finally:
        db.close()

# --- END Database Helper Functions ---

# Set page configuration
st.set_page_config(
    page_title="考研信息查询系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and LangChain
@st.cache_resource
def init_resources():
    """Initialize LangChain manager. Database session managed per request/function."""
    # Database initialization (table creation) should happen via setup.py
    # init_db() # Avoid calling this here
    try:
        langchain_manager = LangChainManager()
        return langchain_manager
    except Exception as e:
        st.error(f"Failed to initialize LangChain Manager: {e}")
        st.error("Please check API keys in .env and network connection.")
        return None

# Get university statistics
@st.cache_data
def get_school_stats():
    """Get basic school statistics including province and doctoral programs."""
    db = DatabaseManager()
    try:
        schools = db.get_all_schools()
        # Ensure province and doctoral_programs are included
        school_data = [{
            "name": s.name,
            "province": s.province, # Needed for heatmap/distribution
            "type": s.type,
            "master_programs": s.master_programs,
            "doctoral_programs": s.doctoral_programs, # Needed for PhD chart
        } for s in schools]
        return pd.DataFrame(school_data)
    except Exception as e:
        st.error(f"Error fetching school stats: {e}")
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data
def get_discipline_stats():
    """Get statistics about program discipline categories."""
    db = DatabaseManager()
    try:
        return db.get_discipline_counts()
    except Exception as e:
        st.error(f"Error fetching discipline stats: {e}")
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data
def fetch_school_admission_data(school_name, years=None):
    """Get admission data for a specific school using the new manager method."""
    db = DatabaseManager()
    try:
        df = db.get_admission_data_for_school(school_name, years)
        return df
    except Exception as e:
        st.error(f"Error fetching admission data for school {school_name}: {e}")
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data
def fetch_program_admission_data(program_name, years=None):
    """Get admission data for a specific program name using the new manager method."""
    db = DatabaseManager()
    try:
        df = db.get_admission_data_for_program(program_name, years)
        return df
    except Exception as e:
        st.error(f"Error fetching admission data for program {program_name}: {e}")
        return pd.DataFrame()
    finally:
        db.close()

@st.cache_data
def get_all_school_names():
     """Get a list of all school names."""
     db = DatabaseManager()
     try:
         schools = db.get_all_schools()
         return sorted([s.name for s in schools])
     except Exception as e:
         st.error(f"Error fetching school names: {e}")
         return []
     finally:
         db.close()

@st.cache_data
def get_all_program_names():
     """Get a list of distinct program names."""
     db = DatabaseManager()
     try:
         # Query distinct program names
         program_names = db.session.query(Program.program_name).distinct().order_by(Program.program_name).all()
         return sorted([p[0] for p in program_names if p[0]])
     except Exception as e:
         st.error(f"Error fetching program names: {e}")
         return []
     finally:
         db.close()

@st.cache_data
def get_available_years():
    """Get distinct years present in the program data."""
    db = DatabaseManager()
    try:
        years = db.session.query(Program.year).distinct().order_by(Program.year.desc()).all()
        return [y[0] for y in years if y[0]]
    except Exception as e:
        st.error(f"Error fetching available years: {e}")
        return [2024, 2023, 2022, 2021, 2020] # Fallback
    finally:
        db.close()

# --- Helper function to parse markdown table ---
def parse_markdown_table(md_string):
    """Attempts to parse the first Markdown table found in a string into a Pandas DataFrame."""
    # Regex to find markdown table (simplified: finds header separator line)
    match = re.search(r"(\n|^)(\|?.*\|.*\r?\n)(\|?[-| :]+\|[-| :]+\|?.*\r?\n)((?:\|?.*\|.*\r?\n?)*)", md_string)
    if not match:
        return None
        
    # Extract table content including header and separator
    table_md = match.group(2) + match.group(3) + match.group(4)
    
    # Use StringIO to simulate a file for pandas reading
    try:
        # Read using pandas, guessing separator, skipping initial spaces
        # header=0 tells pandas the first line is the header
        # skipinitialspace=True helps with spacing around pipes
        # sep='\s*\|\s*' uses pipe as separator, allowing optional spaces
        # engine='python' might be needed for complex separators
        df = pd.read_csv(StringIO(table_md), sep='\s*\|\s*', engine='python', skiprows=[1], skipinitialspace=True)
        
        # Remove empty first/last columns if they exist due to leading/trailing pipes
        if df.columns[0].strip() == '': df = df.iloc[:, 1:]
        if df.columns[-1].strip() == '': df = df.iloc[:, :-1]
        
        # Clean column names (remove leading/trailing spaces)
        df.columns = [col.strip() for col in df.columns]
        
        # Remove rows that might be all NaN (sometimes happens with parsing)
        df.dropna(how='all', inplace=True)
        
        return df
    except Exception as e:
        print(f"Error parsing Markdown table with pandas: {e}")
        # Add more robust regex-based parsing as fallback if needed
        return None 

# Main app
def main():
    # Initialize session state for chat history if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # --- Authentication Logic ---
    # Fetch users and prepare credentials dict
    users = fetch_all_users_from_db()
    credentials = {"usernames": {}}
    if users: # Handle case where DB query fails or table is empty
        for user in users:
            credentials["usernames"][user['username']] = {
                "name": user['name'],
                "password": user['password'] # The stored hash
            }
    else:
        st.warning("没有找到用户信息。请先注册用户")
        # Allow registration even if fetching fails initially

    # Authenticator config
    cookie_key = os.getenv("AUTH_COOKIE_KEY", "default_secret_key_please_change") # Provide default or raise error
    if cookie_key == "default_secret_key_please_change":
        st.warning("安全警告: 未在 .env 中设置 AUTH_COOKIE_KEY，正在使用不安全的默认密钥。请生成一个安全密钥。")

    authenticator = stauth.Authenticate(
        credentials,                    # Use the fetched credentials dictionary
        'kyagent_auth_cookie',          # Name of the cookie stored on the client's browser
        cookie_key,                     # Key to sign the cookie (SECRET!)
        cookie_expiry_days=30,          # How long the cookie should be valid for
        preauthorized={'emails': []}    # Pre-authorized users (optional)
    )

    # --- Render Login/Registration (Using Buttons, No Tabs) ---
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None # Initialize if not exists
    if "show_register_form" not in st.session_state:
        st.session_state.show_register_form = False # Default to showing login

    # Only show login/register if not authenticated
    if not st.session_state.authentication_status:

        # --- Registration Form (Show if toggled) ---
        if st.session_state.show_register_form:
            st.subheader("注册新用户")
            
            # Custom registration form using Streamlit components
            with st.form("custom_registration_form"):
                reg_name = st.text_input("姓名", key="reg_name")
                reg_username = st.text_input("用户名", key="reg_username")
                reg_password = st.text_input("密码", type="password", key="reg_password")
                reg_password_repeat = st.text_input("确认密码", type="password", key="reg_password_repeat")
                
                submit_button = st.form_submit_button("注册")
                
                if submit_button:
                    # Basic form validation
                    if not reg_name or not reg_username or not reg_password:
                        st.error("所有字段都为必填项")
                    elif reg_password != reg_password_repeat:
                        st.error("两次输入的密码不一致")
                    else:
                        try:
                            # Hash the password with bcrypt
                            hashed_password = bcrypt.hashpw(reg_password.encode(), bcrypt.gensalt()).decode()
                            
                            # Add user to database
                            if add_user_to_db(reg_name, reg_username, hashed_password):
                                st.success('用户注册成功！请前往登录页面。')
                                # Switch back to login view
                                st.session_state.show_register_form = False
                                st.rerun()
                        except Exception as e:
                            st.error(f"注册过程中发生错误: {e}")
            
            # Button to go back to login
            if st.button("返回登录", key="back_to_login_btn"):
                st.session_state.show_register_form = False
                st.rerun()

        # --- Login Form (Show if not showing register) ---
        else:
            st.subheader("登录")
            login_result = authenticator.login(key='login_widget')
            if login_result:
                name, authentication_status, username = login_result

            if st.session_state.get("authentication_status") is False:
                st.error('用户名或密码不正确')
            elif st.session_state.get("authentication_status") is None:
                st.warning('请输入你的用户名和密码')

            if st.button("没有账号？去注册", key="go_to_register_btn"):
                st.session_state.show_register_form = True
                st.rerun()

    # --- Main App (conditional display) ---
    if st.session_state.get("authentication_status"):
        # Initialize resources (LangChain) AFTER login
        langchain_manager = init_resources()
        if not langchain_manager:
            st.error("初始化应用程序核心资源失败。")
            st.stop()

        # --- Sidebar ---
        st.sidebar.title(f"欢迎 {st.session_state.get('name', '用户')}") # Use logged-in user's name
        authenticator.logout('退出登录', 'sidebar', key='logout_widget') # Add logout to sidebar, unique key
        st.sidebar.divider() # Optional separator

        # The rest of your app navigation and logic
        st.sidebar.title("考研信息查询系统")
        # Added key to radio button to prevent state issues
        page = st.sidebar.radio("导航", ["首页", "智能查询", "数据分析", "关于"], index=1, key="main_nav")

        # --- Page Rendering ---
        if page == "首页": render_home_page()
        elif page == "智能查询": render_query_page(langchain_manager)
        elif page == "数据分析": render_analysis_page()
        elif page == "关于": render_about_page()

    # If not authenticated, the login/register tabs are shown, and this main app part is skipped.

# Page rendering functions
def render_home_page():
    st.title("欢迎使用考研信息查询系统")
    st.markdown("""
    本系统提供以下功能：
    - **智能查询**：通过自然语言提问获取考研相关信息。
    - **数据分析**：查看考研数据的可视化分析。
    - **数据浏览**：按学校或专业浏览历年录取数据。
    
    系统结合了结构化的历史数据与大语言模型的实时查询能力。
    """)

    st.subheader("数据概览")
    
    # Get school stats data once
    school_stats = get_school_stats()
    if school_stats.empty:
        st.info("数据库中暂无学校统计数据。请先运行数据加载脚本。")
        return

    # --- Row 1: Top 10 Charts --- 
    col1, col2 = st.columns(2)

    with col1:
        # Master Programs Chart
        try:
            if 'master_programs' in school_stats.columns:
                school_stats['master_programs_numeric'] = pd.to_numeric(school_stats['master_programs'], errors='coerce').fillna(0)
                top_master = school_stats.nlargest(10, 'master_programs_numeric')
                
                # st.write("硕士点数量 Top 10")
                fig_master = px.bar(
                    top_master,
                    x="name",
                    y="master_programs_numeric",
                    title="高校硕士点数量 (Top 10)",
                    labels={"name": "学校", "master_programs_numeric": "硕士点数量", "province": "所在地", "type": "备注"},
                    hover_data=["province", "type"] # Show more info on hover
                )
                st.plotly_chart(fig_master, use_container_width=True)
            else:
                 st.info("数据中缺少 'master_programs' 信息。")
        except Exception as e:
            st.error(f"加载硕士点图表出错: {e}")

    with col2:
        try:
            if 'doctoral_programs' in school_stats.columns:
                # Ensure column is numeric and handle potential errors
                school_stats['doctoral_programs_numeric'] = pd.to_numeric(school_stats['doctoral_programs'], errors='coerce').fillna(0)
                top_doctoral = school_stats.nlargest(10, 'doctoral_programs_numeric')
                
                # st.write("博士点数量 Top 10")
                fig_doctoral = px.bar(
                    top_doctoral,
                    x="name",
                    y="doctoral_programs_numeric",
                    title="高校博士点数量 (Top 10)", # New Title
                    labels={"name": "学校", "doctoral_programs_numeric": "博士点数量", "province": "所在地", "type": "备注"}, # New Labels
                    hover_data=["province", "type"] 
                )
                st.plotly_chart(fig_doctoral, use_container_width=True)
            else:
                 st.info("数据中缺少 'doctoral_programs' 信息。")
        except Exception as e:
            st.error(f"加载博士点图表出错: {e}")

        # st.subheader("专业门类分布")
    try:
        discipline_stats = get_discipline_stats()
        if not discipline_stats.empty:
            # Limit number of slices for better readability
            top_disciplines = discipline_stats.head(15)
            fig_discipline = px.pie(
                top_disciplines,
                values='count',
                names='discipline',
                title="专业门类记录数量分布 (Top 15)",
                hole=.3,  # Make it a donut chart
                labels={'count':'数量', 'discipline':'学科类别'} # Added labels argument
            )
            fig_discipline.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_discipline, use_container_width=True)
        else:
            st.info("暂无专业门类统计数据。")
    except Exception as e:
        st.error(f"加载专业门类图表出错: {e}")

    # --- Map ---
    st.subheader("招收研究生高校地理分布图")
    try:
        # --- 1. 加载 GeoJSON 文件 --- 
        # Assume geojson is in the data directory relative to the project root
        geojson_path = os.path.join(project_root, "app/data", "china_province.GeoJSON")
        # st.info(f"")
        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                china_geojson = json.load(f)
            # st.info(f"成功加载 GeoJSON 文件: {geojson_path}") # Optional debug
        except FileNotFoundError:
            st.error(f"错误：找不到 GeoJSON 文件 '{geojson_path}'。请确保它位于 'data' 目录下。")
            china_geojson = None
        except json.JSONDecodeError:
            st.error(f"错误：无法解析 GeoJSON 文件 '{geojson_path}'。请确保文件格式正确。")
            china_geojson = None
        except Exception as geo_e:
             st.error(f"加载 GeoJSON 时发生未知错误: {geo_e}")
             china_geojson = None

        # --- Proceed only if GeoJSON loaded and province data exists --- 
        if china_geojson and 'province' in school_stats.columns and not school_stats['province'].isnull().all():
            province_counts = school_stats['province'].value_counts().reset_index()
            province_counts.columns = ['province', 'count']

            # --- 2. 清理省份名称以匹配 GeoJSON --- 
            # !!! IMPORTANT: Review and adjust this cleaning logic based on your actual data !!!
            def clean_province_name(name):
                if isinstance(name, str):
                    # Basic cleaning (remove common suffixes)
                    name = name.replace("省", "").replace("市", "").replace("自治区", "")
                    # Specific mappings (add more as needed based on your GeoJSON's properties.name)
                    if "内蒙古" in name: return "内蒙古"
                    if "黑龙江" in name: return "黑龙江"
                    if "广西" in name: return "广西" 
                    if "新疆" in name: return "新疆" 
                    if "西藏" in name: return "西藏" 
                    if "宁夏" in name: return "宁夏" 
                    # Add other specific cases if needed
                return name
            
            province_counts['province_cleaned'] = province_counts['province'].apply(clean_province_name)
            # st.write("调试：清理后的省份名称和数量", province_counts[['province_cleaned', 'count']].head()) # Optional debug

            # --- 3. 绘制地图 --- 
            try:
                fig_map = px.choropleth(
                    province_counts, 
                    geojson=china_geojson, 
                    locations='province_cleaned', 
                    featureidkey="properties.name", 
                    color='count', 
                    color_continuous_scale="Reds", 
                    scope="asia", # Focus map view
                    title="高校数量地理分布", 
                    labels={'count':'高校数量', 'province_cleaned': '省份'}, 
                    hover_name='province'
                )
                fig_map.update_geos(fitbounds="locations", visible=False)
                fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0}) # Removed mapbox_accesstoken
                st.plotly_chart(fig_map, use_container_width=True)
            except ValueError as ve:
                st.error(f"绘制地图时出错: {ve}")
                st.info("地图绘制失败，尝试显示省份条形图...")
                fig_province_fallback = px.bar(province_counts.head(20), x='province', y='count', title="各省份收录高校数量 (Top 20)", labels={"province": "省份", "count": "高校数量"})
                fig_province_fallback.update_xaxes(tickangle=45)
                st.plotly_chart(fig_province_fallback, use_container_width=True)
            except Exception as map_e:
                 st.error(f"绘制地图时发生未知错误: {map_e}")
                 
        elif not china_geojson:
            st.info("缺少 GeoJSON 文件，无法绘制地图。将显示省份条形图。")
            # Fallback to bar chart if GeoJSON is missing
            if 'province' in school_stats.columns and not school_stats['province'].isnull().all():
                 province_counts = school_stats['province'].value_counts().reset_index()
                 province_counts.columns = ['province', 'count']
                 fig_province_fallback = px.bar(province_counts.head(20), x='province', y='count', title="各省份收录高校数量 (Top 20)", labels={"province": "省份", "count": "高校数量"})
                 fig_province_fallback.update_xaxes(tickangle=45)
                 st.plotly_chart(fig_province_fallback, use_container_width=True)
            else:
                 st.info("数据中缺少有效的 'province' 信息。")

        else: # Case where GeoJSON is loaded but province data is missing
            st.info("数据中缺少有效的 'province' 信息，无法生成省份分布图。")
            
    except Exception as e:
        st.error(f"加载地理分布图表时出错: {e}")

# --- MODIFIED: render_query_page function --- 
def render_query_page(langchain_manager):
    st.title("🎓 智能查询")
    st.caption("与考研信息助手对话，问我任何关于考研复试分数线、学校或专业的问题！")

    # Display existing chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if isinstance(message["content"], dict) and "final_answer" in message["content"]:
                with st.expander("查看思考过程", expanded=False):
                    # Display thinking process using markdown, allowing formatting
                    st.markdown(message["content"].get("thinking_process", "无思考过程记录。"), unsafe_allow_html=True)
                # Display final text answer
                st.markdown(message["content"]["final_answer"])
                # Display chart if it was generated and stored
                if message["content"].get("chart_fig"):
                    st.plotly_chart(message["content"].get("chart_fig"), use_container_width=True)
            elif isinstance(message["content"], str):
                 st.markdown(message["content"])
            else:
                 st.markdown(str(message["content"]))

    # Get user input using chat_input
    if query := st.chat_input("请输入您的问题..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(query)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # Use an expander for the thinking process
            expander_label = "🤖 思考中..."
            with st.expander(expander_label, expanded=True):
                 thinking_process_area = st.empty()
                 thinking_process_content = ""
                 thinking_process_area.markdown("_启动查询引擎..._")
            
            # Placeholder for the final answer stream
            final_answer_area = st.empty()
            final_answer_content = ""
            chart_figure = None # Initialize chart figure
            processing_error = None # Flag for errors
            
            try:
                stream = langchain_manager.process_query(query)
                for chunk in stream:
                    step_description = ""
                    # --- MODIFIED ACTION LOG PARSING --- 
                    if "actions" in chunk:
                        for action in chunk["actions"]:
                            log_content = action.log
                            thought = ""
                            # Attempt to parse Thought
                            thought_match = re.search(r"Thought:(.*?)(Action:|$)", log_content, re.DOTALL | re.IGNORECASE)
                            if thought_match:
                                thought = thought_match.group(1).strip()
                            
                            # Add parsed Thought with Chinese label
                            if thought:
                                step_description += f"\n🤔 **思考**: {thought}\n"
                            # Add Action details with Chinese label
                            step_description += f"⏳ **动作**: 工具=`{action.tool}`, 输入=`{action.tool_input}`\n"
                            # Optionally add raw log for debugging if needed, but might be redundant now
                            # step_description += f"_Raw Log: {action.log}_\n"
                    # --- END MODIFIED --- 
                    elif "steps" in chunk:
                        for step in chunk["steps"]:
                             observation = str(step.observation)
                             if len(observation) > 500:
                                 observation = observation[:250] + "... (内容过长已截断) ..." + observation[-250:]
                             # Use Chinese label for Observation
                             step_description += f"\n✅ **观察结果**: 工具 `{step.action.tool}` 返回:\n```\n{observation}\n```\n"
                    elif "output" in chunk:
                        final_answer_content += chunk["output"]
                        final_answer_area.markdown(final_answer_content + "▌") # Add cursor effect
                    
                    if step_description:
                        thinking_process_content += step_description
                        thinking_process_area.markdown(thinking_process_content, unsafe_allow_html=True)
                
                # --- ADDED: Finalizing step simulation --- 
                with st.status("整理和审查最终答案...", expanded=False) as status:
                    time.sleep(0.75) # Brief pause to make status visible
                    status.update(label="生成完成!", state="complete", expanded=False)
                # --- END ADDED --- 
                
                # Final update after stream finishes and simulated review
                final_answer_area.markdown(final_answer_content)
                if not final_answer_content:
                     final_answer_content = "抱歉，未能根据现有信息生成明确的回答。"
                     final_answer_area.markdown(final_answer_content)
                     
                # Attempt to parse table and plot
                try:
                    df_table = parse_markdown_table(final_answer_content)
                    if df_table is not None and not df_table.empty:
                        st.write("--- 数据可视化 ---") 
                        year_col, score_col, category_col = None, None, None
                        for col in df_table.columns:
                            col_lower = col.lower()
                            if 'year' in col_lower or '年份' in col: year_col = col
                            if 'total' in col_lower or '总分' in col: score_col = col
                            if ('program' in col_lower or '专业' in col or 
                                'school' in col_lower or '大学' in col or '校' in col) and col != year_col:
                                category_col = col
                        if year_col: df_table[year_col] = pd.to_numeric(df_table[year_col], errors='coerce')
                        if score_col: df_table[score_col] = pd.to_numeric(df_table[score_col], errors='coerce')
                        df_table.dropna(subset=[year_col, score_col], inplace=True)
                        if year_col and score_col and len(df_table[year_col].unique()) > 1:
                            chart_figure = px.line(
                                df_table.sort_values(by=year_col),
                                x=year_col, y=score_col, color=category_col, markers=True,
                                title=f"'{category_col if category_col else score_col}' 趋势分析 (Trend Analysis)",
                                labels={year_col: "年份 (Year)", score_col: "分数线 (Score)", category_col: "类别 (Category)" if category_col else None}
                            )
                            st.plotly_chart(chart_figure, use_container_width=True)
                        elif score_col and category_col and len(df_table[category_col].unique()) > 1: 
                            chart_figure = px.bar(
                                df_table,
                                x=category_col, y=score_col,
                                title=f"'{score_col}' 对比 (Comparison)",
                                labels={category_col: "类别 (Category)", score_col: "分数线 (Score)"}
                            )
                            st.plotly_chart(chart_figure, use_container_width=True)
                        else:
                            st.info("从回答中解析的表格数据不足以自动生成图表。")
                except Exception as plot_error:
                    print(f"Error during table parsing or plotting: {plot_error}")
                    
            except Exception as e:
                processing_error = e # Store error
                st.error(f"查询过程中遇到错误: {e}")
                error_message = f"抱歉，处理您的请求时发生错误。\n错误详情: {e}"
                final_answer_content = error_message # Store error as final answer
                final_answer_area.error(error_message)
            
            # Add assistant response to chat history
            # Only store chart if processing was successful (no error)
            assistant_message = {
                "role": "assistant",
                "content": {
                    "thinking_process": thinking_process_content if thinking_process_content else "无",
                    "final_answer": final_answer_content,
                    "chart_fig": chart_figure if not processing_error else None
                }
            }
            st.session_state.messages.append(assistant_message)

def render_analysis_page():
    st.title("数据分析与浏览")

    analysis_type = st.selectbox("选择分析/浏览维度", ["按学校分析", "按专业分析", "按专业门类浏览"])
    
    available_years = get_available_years()
    if not available_years:
         st.warning("数据库中暂无年份数据，无法进行分析。")
         return
         
    selected_years = st.multiselect("选择年份 (可多选)", available_years, default=available_years[:3]) # Default to latest 3 years
    if not selected_years:
         st.warning("请至少选择一个年份进行分析。")
         return

    if analysis_type == "按学校分析":
        render_school_analysis(selected_years)
    elif analysis_type == "按专业分析":
        render_program_analysis(selected_years)
    elif analysis_type == "按专业门类浏览":
         render_discipline_browsing(selected_years)

def render_school_analysis(selected_years):
    st.subheader("按学校分析")
    school_names = get_all_school_names()
    if not school_names:
        st.warning("数据库中暂无学校数据。")
        return
        
    selected_school = st.selectbox("选择学校", school_names)

    if selected_school:
        school_data = fetch_school_admission_data(selected_school, selected_years)

        if not school_data.empty:
            st.write(f"**{selected_school} - {', '.join(map(str, sorted(selected_years)))} 年录取数据**")
            # Improve DataFrame display
            st.dataframe(school_data.style.format({
                 'total_score': '{:.1f}',
                 'politics_score': '{:.0f}',
                 'english_score': '{:.0f}',
                 'major_score1': '{:.0f}',
                 'major_score2': '{:.0f}'
            }))

            st.subheader("分数线趋势 (按专业)")
            if 'total_score' in school_data.columns:
                # Plot average score per program over selected years
                prog_year_scores = school_data.groupby(["year", "program_name"])["total_score"].mean().reset_index()
                
                if not prog_year_scores.empty:
                    fig = px.line(
                        prog_year_scores,
                        x="year",
                        y="total_score",
                        color="program_name",
                        markers=True,
                        title=f"{selected_school} 主要专业平均总分趋势",
                        labels={"year": "年份", "total_score": "平均总分", "program_name": "专业名称"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                     st.info("选中年份内无足够数据绘制专业分数趋势图。")

                # Add more visualizations if needed (e.g., box plot of scores per year)
                st.subheader("总分分布 (按年份)")
                fig_box = px.box(
                     school_data,
                     x='year',
                     y='total_score',
                     title=f"{selected_school} 各年份总分分布",
                     labels={"year": "年份", "total_score": "总分"}
                )
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("数据中缺少'total_score'列，无法绘制分数图表。")
        else:
            st.info(f"在选定年份内没有找到 {selected_school} 的录取数据。")

def render_program_analysis(selected_years):
    st.subheader("按专业分析")
    program_names = get_all_program_names()
    if not program_names:
        st.warning("数据库中暂无专业数据。")
        return
        
    selected_program = st.selectbox("选择专业名称 (模糊匹配)", [" - 输入或选择 - "] + program_names)

    if selected_program != " - 输入或选择 - ":
        program_data = fetch_program_admission_data(selected_program, selected_years)

        if not program_data.empty:
            st.write(f"**专业 '{selected_program}' - {', '.join(map(str, sorted(selected_years)))} 年各校录取数据**")
            st.dataframe(program_data.style.format({
                 'total_score': '{:.1f}',
                 'politics_score': '{:.0f}',
                 'english_score': '{:.0f}',
                 'major_score1': '{:.0f}',
                 'major_score2': '{:.0f}'
            }))

            st.subheader("分数线对比 (按学校)")
            if 'total_score' in program_data.columns:
                school_year_scores = program_data.groupby(["year", "school_name"])["total_score"].mean().reset_index()
                
                if not school_year_scores.empty:
                    fig = px.line(
                        school_year_scores,
                        x="year",
                        y="total_score",
                        color="school_name",
                        markers=True,
                        title=f"'{selected_program}' 专业主要学校平均总分对比",
                        labels={"year": "年份", "total_score": "平均总分", "school_name": "学校名称"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("选中年份内无足够数据绘制学校分数对比图。")
                
                st.subheader("总分分布 (按学校)")
                fig_box = px.box(
                     program_data,
                     x='school_name',
                     y='total_score',
                     title=f"{selected_program} 专业各学校总分分布 ({', '.join(map(str, sorted(selected_years)))})".format(),
                     labels={"school_name": "学校", "total_score": "总分"}
                )
                # Optionally rotate x-axis labels if too many schools
                fig_box.update_xaxes(tickangle=45)
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                 st.info("数据中缺少'total_score'列，无法绘制分数图表。")
        else:
            st.info(f"在选定年份内没有找到专业名称包含 '{selected_program}' 的录取数据。")
            
def render_discipline_browsing(selected_years):
    st.subheader("按专业门类浏览")
    db = DatabaseManager()
    try:
        disciplines = db.get_all_program_disciplines()
    finally:
        db.close()
        
    if not disciplines:
        st.warning("数据库中暂无专业门类数据。")
        return
        
    selected_discipline = st.selectbox("选择专业门类", disciplines)
    
    if selected_discipline:
        db = DatabaseManager()
        try:
            # Fetch programs for the selected discipline and years
            query = db.session.query(Program).filter(
                Program.discipline_category == selected_discipline,
                Program.year.in_(selected_years)
            ).options(joinedload(Program.school)) # Eager load school
            
            programs = query.order_by(Program.school_id, Program.year.desc(), Program.program_name).all()
            
            if programs:
                st.write(f"**'{selected_discipline}' 门类 - {', '.join(map(str, sorted(selected_years)))} 年录取数据**")
                data = [{
                    "年份": p.year,
                    "学校": p.school.name if p.school else "N/A",
                    "专业代码": p.program_code,
                    "专业名称": p.program_name,
                    "学习方式": p.program_type,
                    "总分": p.total_score,
                    "政治": p.politics_score,
                    "外语": p.english_score,
                    "业务课一": p.major_score1,
                    "业务课二": p.major_score2,
                } for p in programs]
                df = pd.DataFrame(data)
                st.dataframe(df.style.format({'总分': '{:.1f}', '政治': '{:.0f}', '外语': '{:.0f}', '业务课一': '{:.0f}', '业务课二': '{:.0f}'}))
                
                # Simple visualization: Average score trend for the discipline
                if '总分' in df.columns and pd.to_numeric(df['总分'], errors='coerce').notna().any():
                     df['总分'] = pd.to_numeric(df['总分'], errors='coerce')
                     avg_score_trend = df.groupby('年份')['总分'].mean().reset_index()
                     st.subheader(f"{selected_discipline} 门类平均总分趋势")
                     fig = px.line(
                          avg_score_trend,
                          x='年份',
                          y='总分',
                          markers=True,
                          title=f"{selected_discipline} 门类平均总分趋势 ({', '.join(map(str, sorted(selected_years)))})",
                          labels={"年份": "年份", "总分": "平均总分"}
                     )
                     st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"在选定年份内没有找到 '{selected_discipline}' 门类的录取数据。")
                
        except Exception as e:
            st.error(f"获取 {selected_discipline} 门类数据时出错: {e}")
        finally:
            db.close()

def render_about_page():
    st.title("关于本系统")
    st.markdown("""
    ### 考研信息查询系统 (KyAgent)
    
    **核心技术:**
    - **数据存储:** MySQL (使用 SQLAlchemy ORM)
    - **智能查询:** LangChain (Agent + Tools: SQL Database, Search)
    - **大语言模型:** OpenAI API (GPT-4 Turbo or specified model)
    - **搜索引擎:** Tavily / Google Serper API
    - **用户界面 & 可视化:** Streamlit, Plotly
    
    **数据来源:**
    - 用户提供的历年考研 Excel 文件 (存储于 MySQL)
    - 实时搜索引擎结果 (用于补充或最新信息)
    
    **主要功能:**
    - **智能问答:** 基于LLM理解用户问题，结合数据库和搜索进行回答。
    - **数据浏览:** 按学校、专业、专业门类等多维度浏览历史数据。
    - **数据分析:** 提供分数趋势、分布等可视化图表。
    
    **运行流程:**
    1. `setup.py`: 创建数据库，执行 `load_data.py` 加载 Excel 数据到 MySQL。
    2. `run.py` / `streamlit run app/app.py`: 启动 Streamlit 应用。
    3. 用户通过界面进行查询或浏览。
    4. LangChain Agent 处理查询，可能涉及数据库查询或网络搜索。
    5. Streamlit 展示结果或图表。
    """)

# Entry point
if __name__ == "__main__":
    main() # Session state init moved to main 