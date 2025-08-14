

from langchain_core.tools import render_text_description, tool as lc_tool
from langchain.agents import AgentExecutor, create_react_agent
from tools.api_tools import APITools
import asyncio
from services.llm_service import AsyncLLMService

llm_service = AsyncLLMService()
api_tools = APITools()

# String-compatible wrappers for all API tools

# Wrappers now call the public string-compatible tool methods

# Wrappers now call the raw methods to avoid LangChain tool invocation issues
@lc_tool(description="Fetch the location of the user based on their IP address (string input, IP optional). Accepts an IP address as a string or empty for current user.")
async def get_location_string(ipAddress: str = "") -> str:
    return await api_tools._get_location_raw(ipAddress)

@lc_tool(description="Fetch the current weather for a given city (string input). Accepts a city name as a string.")
async def get_weather_string(city: str) -> dict:
    return await api_tools._get_weather_raw(city)

@lc_tool(description="Fetch the current weather based on the user's IP address (string input, IP optional). Accepts an IP address as a string or empty for current user.")
async def get_weather_by_ip_string(ipAddress: str = "") -> dict:
    city = await api_tools._get_location_raw(ipAddress)
    if city:
        return await api_tools._get_weather_raw(city)
    return {}

@lc_tool(description="Fetch movie information by title (string input). Accepts a movie title as a string.")
async def get_movie_info_string(title: str) -> dict:
    return await api_tools._get_movie_info_raw(title)

@lc_tool(description="Fetch anime information by title (string input). Accepts an anime title as a string.")
async def get_anime_info_string(title: str) -> dict:
    return await api_tools._get_anime_info_raw(title)

tool_methods = [
    get_location_string,
    get_weather_string,
    get_weather_by_ip_string,
    get_movie_info_string,
    get_anime_info_string,
]


class AsyncAgentExecutor:
    def __init__(self, llm, tools=tool_methods, verbose=False, format="json"):
        self.llm = llm
        self.tools = tools
        self.verbose = verbose
        self.format = format
        self.agent_executor = None

    async def setup(self):
        # JARVIS-like, concise ReAct prompt with private reasoning
        prompt_template = """
            You are Saba, a JARVIS-like AI copilot. Be direct, proactive, and action-focused.
            - Keep replies to 1–2 short sentences.
            - Ask only essential clarifying questions when strictly needed.
            - Prefer using tools to fetch facts; avoid guessing.
            - Your internal reasoning (Thought, Action, Observation) must NEVER appear in the Final Answer.
            - The Final Answer should ONLY contain your direct response to the user.
            - Do NOT include risk assessments, next steps, or any internal analysis in the Final Answer.

            You can use these tools:
            {tools}

            Use the following strict format when deciding and using tools. These steps are for coordination, not for the final answer:
            Question: {input}
            Thought: <brief internal reasoning>
            Action: <one tool from [{tool_names}]>
            Action Input: <the exact input for the tool>
            Observation: <tool result>
            Thought: <decide next step or finalize>
            ... (repeat Action/Action Input/Observation as needed) ...
            Final Answer: <ONLY your direct, conversational response to the user - no internal reasoning>

            Begin:
            Question: {input}
            Thought: {agent_scratchpad}
        """
        from langchain_core.prompts import PromptTemplate
        prompt = PromptTemplate.from_template(prompt_template)
        prompt = prompt.partial(
            tools=render_text_description(self.tools),
            tool_names=", ".join([t.name for t in self.tools]),
        )
        agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            handle_parsing_errors=True,
            verbose=self.verbose,
            format=self.format,
            max_iterations=10,
        )

    async def ainvoke(self, input_text):
        if self.agent_executor is None:
            await self.setup()
        result = await self.agent_executor.ainvoke({"input": input_text})
        # If result is a dict with 'output', check if it's a movie info dict
        output = result['output'] if isinstance(result, dict) and 'output' in result else result
        
        # Clean up the output by removing internal reasoning artifacts
        if isinstance(output, str):
            # Remove risk assessments and next steps that should be internal
            lines = output.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Skip lines that contain internal reasoning artifacts
                if (line.startswith('**Risk:**') or 
                    line.startswith('**Next Step:**') or
                    line.startswith('Risk:') or
                    line.startswith('Next Step:') or
                    'Risk:' in line and ('None detected' in line or 'Low' in line or 'Medium' in line or 'High' in line) or
                    'Next Step:' in line and ('Please' in line or 'Suggest' in line)):
                    continue
                if line:  # Only add non-empty lines
                    cleaned_lines.append(line)
            output = ' '.join(cleaned_lines).strip()
        
        # Try to detect a movie info dict and format a final answer
        if isinstance(output, dict) and all(k in output for k in ("Title", "Plot", "Year")):
            # Format a nice summary
            summary = f"{output['Title']} ({output['Year']}): {output['Plot']}\n"
            if 'Genre' in output:
                summary += f"Genre: {output['Genre']}\n"
            if 'Director' in output:
                summary += f"Director: {output['Director']}\n"
            if 'Actors' in output:
                summary += f"Actors: {output['Actors']}\n"
            if 'imdbRating' in output:
                summary += f"IMDb Rating: {output['imdbRating']}\n"
            return summary.strip()
        return str(output)
    