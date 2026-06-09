import os
import sys
import re
import yaml
import logging
import json
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
config_dir = os.path.join(project_root, 'config')

if src_path not in sys.path:
    sys.path.append(src_path)

try:
    from crewai_tools import SerperDevTool
    serper_tool = SerperDevTool()
except ImportError:
    serper_tool = None

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "qwen-plus"
DEFAULT_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class ArticleAgentExecutor:
    """使用 CrewAI 的文章创作 Agent 执行器。"""

    def __init__(self):
        load_dotenv()
        self.agents_config = self._load_config(os.path.join(config_dir, 'article_agents.yaml'))
        self.tasks_config = self._load_config(os.path.join(config_dir, 'article_tasks.yaml'))
        self.llm = self._setup_llm()
        self.agents = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _setup_llm(self) -> ChatOpenAI:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        model_name = os.environ.get("MODEL_NAME", DEFAULT_MODEL)
        os.environ["OPENAI_API_BASE"] = DEFAULT_API_BASE
        os.environ["OPENAI_BASE_URL"] = DEFAULT_API_BASE
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        return ChatOpenAI(
            model=model_name,
            base_url=DEFAULT_API_BASE,
            api_key=api_key,
            temperature=0.7,
        )

    def _create_agent(self, agent_name: str) -> Agent:
        if agent_name in self.agents:
            return self.agents[agent_name]
        config = self.agents_config.get(agent_name)
        if not config:
            raise ValueError(f"未找到 Agent 配置: {agent_name}")
        tools = []
        for tool_name in config.get('tools', []):
            if tool_name == 'serper_dev_tool':
                if serper_tool:
                    tools.append(serper_tool)
                else:
                    raise ValueError(f"Agent {agent_name} 所需的 serper_dev_tool 不可用")
        agent = Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=tools,
            llm=self.llm.model_name,
            verbose=True,
            allow_delegation=False,
        )
        self.agents[agent_name] = agent
        return agent

    def _create_task(self, task_name: str, agent: Agent, **kwargs) -> Task:
        config = self.tasks_config.get(task_name)
        if not config:
            raise ValueError(f"未找到任务配置: {task_name}")
        return Task(
            description=config['description'].format(**kwargs),
            expected_output=config.get('expected_output', 'Task result'),
            agent=agent,
        )

    def _get_agent_output(self, result) -> str:
        if hasattr(result, 'raw'):
            return result.raw
        return str(result)

    def _parse_outline(self, json_str: str) -> Optional[Dict]:
        try:
            cleaned = json_str.strip()
            match = re.search(r'```json\s*(.*?)\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            elif '```' in cleaned:
                cleaned = cleaned.split("```")[1].strip()
            data = json.loads(cleaned)
            sections = data.get('sections') or data.get('chapters')
            if sections:
                data['sections'] = sections
                return data
        except Exception as e:
            logger.error(f"JSON 解析失败: {e}")
        return None

    def execute(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        phase = task_payload.get('phase')
        handlers = {
            'research': self._run_research,
            'outline': self._run_outline,
            'section': self._run_section,
            'chapter': self._run_section,
            'review': self._run_review,
        }
        handler = handlers.get(phase)
        if not handler:
            raise ValueError(f"未知阶段: {phase}")
        return handler(task_payload)

    def _run_research(self, payload):
        agent = self._create_agent('xiao_mei')
        task = self._create_task(
            'research_task', agent,
            topic=payload.get('topic'),
            requirements=payload.get('requirements', ''),
        )
        result = Crew(agents=[agent], tasks=[task], process=Process.sequential).kickoff()
        return {"result": self._get_agent_output(result).strip()}

    def _run_outline(self, payload):
        agent = self._create_agent('xiao_qing')
        task = self._create_task(
            'outline_task', agent,
            topic=payload.get('topic'),
            requirements=payload.get('requirements', ''),
            chosen_direction=payload.get('chosen_direction', ''),
        )
        result = Crew(agents=[agent], tasks=[task], process=Process.sequential).kickoff()
        output = self._get_agent_output(result)
        parsed = self._parse_outline(output)
        if not parsed:
            return {"result": output, "parsed": False}
        return {"result": parsed, "parsed": True}

    def _run_section(self, payload):
        agent = self._create_agent('xiao_qing')
        task = self._create_task(
            'section_writing_task', agent,
            topic=payload.get('topic'),
            requirements=payload.get('requirements', ''),
            section_index=payload.get('section_index') or payload.get('chapter_index'),
            section_title=payload.get('section_title') or payload.get('chapter_title'),
            section_summary=payload.get('section_summary') or payload.get('chapter_summary'),
            article_title=payload.get('article_title') or payload.get('course_title'),
        )
        result = Crew(agents=[agent], tasks=[task], process=Process.sequential).kickoff()
        return {"result": self._get_agent_output(result)}

    def _run_review(self, payload):
        agent = self._create_agent('xiao_yin')
        task = self._create_task(
            'review_task', agent,
            topic=payload.get('topic'),
            requirements=payload.get('requirements', ''),
            article_title=payload.get('article_title') or payload.get('course_title'),
            article_content=payload.get('article_content') or payload.get('course_content'),
            chosen_direction=payload.get('chosen_direction', ''),
        )
        result = Crew(agents=[agent], tasks=[task], process=Process.sequential).kickoff()
        return {"result": self._get_agent_output(result)}
