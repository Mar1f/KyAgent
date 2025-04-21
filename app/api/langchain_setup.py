import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory

from langchain import hub

# --- Updated LangChain Community Imports --- 
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain.tools import Tool
from sqlalchemy import create_engine
from app_config import DATABASE_URL, OPENAI_API_URL,OPENAI_API_KEY, TAVILY_API_KEY, SERPER_API_KEY, MODEL
from app.utils.prompt_templates import AGENT_SYSTEM_PROMPT

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")

# No longer need to load dotenv here if app_config does it
# load_dotenv()

# --- Define the proxy URL --- 
# OPENAI_PROXY_URL = "https://api.chatanywhere.tech/v1"
# --- End Proxy URL --- 

class LangChainManager:
    def __init__(self):
        # Initialize LLM using imported key and proxy base_url
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY, 
            base_url=OPENAI_API_URL,
            model=MODEL,
            temperature=0.2,
            streaming=True 
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='output'
        )
        
        # Initialize search tools
        self.setup_search_tools()
        
        # Initialize SQL toolkit
        self.setup_sql_toolkit()
        
        # Setup agent
        self.setup_agent()
    
    def setup_search_tools(self):
        """Setup search tools for retrieving information from the web"""
        # Serper (Google Search API) using imported key
        self.serper = GoogleSerperAPIWrapper(
            serper_api_key=SERPER_API_KEY # Use imported variable
        )
        
        # Tavily Search Tool Instantiation
        try:
             self.tavily_tool = TavilySearchResults(
                 max_results=5,
                 api_key=TAVILY_API_KEY 
             )
        except Exception as e:
             print(f"Error initializing TavilySearchResults: {e}. Ensure TAVILY_API_KEY is set.")
             def dummy_tavily_func(query): return "Tavily Search tool initialization failed."
             self.tavily_tool = Tool(
                 name="Tavily Search",
                 func=dummy_tavily_func,
                #  description="Tavily Search tool failed to initialize."
                 description="Useful when you need to search for current information about graduate school examination (考研), admission policies, universities, or programs not found in the database. You MUST use this tool when database query returns empty."
             )

        # Create search tools list
        self.search_tools = [
            Tool(
                name="Google Search",
                func=self.serper.run,
                description="Useful when you need to search for current information about graduate school examination (考研), admission policies, universities, or programs not found in the database. You MUST use this tool when database query returns empty."
            ),
            self.tavily_tool # Add the TavilySearchResults instance directly
        ]
    
    def setup_sql_toolkit(self):
        """Setup SQL toolkit for database operations"""
        # Create SQL engine using imported URL
        engine = create_engine(DATABASE_URL)
        
        # Wrap engine in SQLDatabase
        db = SQLDatabase(engine=engine)
        # Pass the SQLDatabase instance to the toolkit
        self.sql_toolkit = SQLDatabaseToolkit(
            db=db, # Pass the db instance, not the engine
            llm=self.llm
        )
        
        # Get SQL tools
        self.sql_tools = self.sql_toolkit.get_tools()
    
    def setup_agent(self):
        """Setup agent with tools, using Hub prompt and injecting custom system instructions."""
        # all tools
        all_tools = self.search_tools + self.sql_tools

        try:
            base_prompt = hub.pull("hwchase17/structured-chat-agent")
            if base_prompt.messages and isinstance(base_prompt.messages[0], SystemMessagePromptTemplate):
                original_system_template = base_prompt.messages[0].prompt.template
                # Prepend our detailed instructions
                enhanced_system_template = AGENT_SYSTEM_PROMPT + "\n\n---\n\n" + original_system_template
                # Create a new SystemMessagePromptTemplate with the combined content
                base_prompt.messages[0] = SystemMessagePromptTemplate.from_template(enhanced_system_template)
                prompt = base_prompt # Use the modified base prompt
            else:
                print("Warning: Could not find SystemMessagePromptTemplate in Hub prompt. Using basic fallback.")
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessagePromptTemplate.from_template(AGENT_SYSTEM_PROMPT),
                    MessagesPlaceholder(variable_name="chat_history"), 
                    HumanMessagePromptTemplate.from_template("{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad")
                ])
        except Exception as e:
             print(f"Error pulling or modifying prompt from LangChain Hub: {e}. Using basic fallback.")
             prompt = ChatPromptTemplate.from_messages([
                 SystemMessagePromptTemplate.from_template(AGENT_SYSTEM_PROMPT),
                 MessagesPlaceholder(variable_name="chat_history"),
                 HumanMessagePromptTemplate.from_template("{input}"),
                 MessagesPlaceholder(variable_name="agent_scratchpad")
             ])

        # Create agent
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=all_tools,
            prompt=prompt
        )

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=all_tools,
            memory=self.memory, # Pass the initialized memory object
            handle_parsing_errors=True, # Helpful for debugging
            max_iterations=3, # Reduce max iterations to prevent repeated queries
            early_stopping_method="force", # Force stop if max iterations reached
            return_intermediate_steps=True, # Return intermediate steps for better control
            verbose=True
        )
    
    def run_agent_stream(self, query_input): # Renamed variable for clarity
        """Run agent and stream intermediate steps."""
        # The executor automatically uses memory with "chat_history" key
        # It expects the user query under the "input" key
        return self.agent_executor.stream({"input": query_input})
    
    def process_query(self, query):
        """Process a user query by passing it directly to the agent stream."""
        # Remove prompt selection/formatting here.
        # The main instructions are now in the agent's system prompt.
        # Pass the raw user query as the 'input'.
        return self.run_agent_stream(query) 