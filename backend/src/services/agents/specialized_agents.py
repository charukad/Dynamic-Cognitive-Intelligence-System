"""Specialized agent implementations."""

from src.domain.models import Agent
from src.services.agents.base_agent import BaseAgent


class LogicianAgent(BaseAgent):
    """
    Logician agent for analytical reasoning and systematic problem-solving.
    
    Strengths: Logical deduction, breaking down problems, identifying edge cases.
    Temperature: 0.1 (highly deterministic)
    """

    async def process(self, task_input: dict) -> dict:
        """Process task with logical reasoning."""
        prompt = f"""Analyze this problem systematically:

Problem: {task_input.get('problem', task_input)}

Provide a step-by-step logical analysis."""

        response = await self.generate_response(prompt)
        
        return {
            "agent": self.agent.name,
            "type": "logical_analysis",
            "response": response,
            "reasoning_type": "deductive",
        }


class CreativeAgent(BaseAgent):
    """
    Creative agent for innovative thinking and novel approaches.
    
    Strengths: Brainstorming, unconventional solutions, creative combinations.
    Temperature: 0.8 (highly creative)
    """

    async def process(self, task_input: dict) -> dict:
        """Process task with creative thinking."""
        prompt = f"""Think creatively about this:

Challenge: {task_input.get('problem', task_input)}

Provide innovative and unconventional approaches."""

        response = await self.generate_response(prompt)
        
        return {
            "agent": self.agent.name,
            "type": "creative_solution",
            "response": response,
            "reasoning_type": "divergent",
        }


class ScholarAgent(BaseAgent):
    """
    Scholar agent for research and knowledge synthesis.
    
    Strengths: Deep knowledge, accurate information, comprehensive research.
    Temperature: 0.3 (balanced and accurate)
    """

    async def process(self, task_input: dict) -> dict:
        """Process task with research-based approach."""
        prompt = f"""Provide a well-researched response to:

Query: {task_input.get('query', task_input)}

Include relevant context and authoritative information."""

        response = await self.generate_response(prompt)
        
        return {
            "agent": self.agent.name,
            "type": "research_synthesis",
            "response": response,
            "reasoning_type": "analytical",
        }


class CriticAgent(BaseAgent):
    """
    Critic agent for evaluation and quality assurance.
    
    Strengths: Identifying flaws, rigorous evaluation, constructive criticism.
    Temperature: 0.2 (precise and critical)
    """

    async def process(self, task_input: dict) -> dict:
        """Process task with critical evaluation."""
        prompt = f"""Critically evaluate the following:

Subject: {task_input.get('subject', task_input)}

Identify potential flaws, weaknesses, and areas for improvement."""

        response = await self.generate_response(prompt)
        
        return {
            "agent": self.agent.name,
            "type": "critical_evaluation",
            "response": response,
            "reasoning_type": "evaluative",
        }


class CoderAgent(BaseAgent):
    """
    Coder agent for software development tasks.
    
    Strengths: Writing code, debugging, optimization, technical implementation.
    Temperature: 0.2 (precise and accurate)
    """

    async def process(self, task_input: dict) -> dict:
        """Process task with coding expertise."""
        prompt = f"""Solve this programming problem:

Task: {task_input.get('task', task_input)}

Provide clean, well-documented code with error handling."""

        response = await self.generate_response(prompt, max_tokens=2000)
        
        return {
            "agent": self.agent.name,
            "type": "code_solution",
            "response": response,
            "reasoning_type": "procedural",
        }


class ExecutiveAgent(BaseAgent):
    """
    Executive agent for coordination and decision-making.
    
    Strengths: Strategic planning, prioritization, synthesis, decision-making.
    Temperature: 0.4 (balanced judgment)
    """

    async def process(self, task_input: dict) -> dict:
        """Process task with executive decision-making."""
        
        # Check for routing request
        if task_input.get("routing_request", False):
            situation = task_input.get('situation', 'No situation provided')
            prompt = f"""
            You are the Executive Orchestrator. Your job is to route tasks to the most appropriate specialized agent.
            
            Available Agents:
            - coder: Software development, debugging, code optimization
            - designer: UI/UX design, aesthetics, user experience
            - data_analyst: Data analysis, visualization, statistics
            - financial: Financial planning, market analysis
            - scholar: Research, fact-checking, knowledge synthesis
            - creative: Brainstorming, novel ideas
            - logician: Logical reasoning, problem decomposition
            
            Task: {situation}
            
            Return a JSON object with:
            - "target": The id of the best agent (e.g., "coder").
            - "reasoning": Brief explanation why.
            
            JSON ONLY. No markdown.
            """
            
            response = await self.generate_response(prompt, max_tokens=200)
            
            # Simple JSON parsing (robustness similar to VLLMClient stream parsing)
            import json
            try:
                # excessive cleanup
                clean_response = response.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_response)
                return {
                    "agent": self.agent.name,
                    "type": "routing_decision",
                    "target": data.get("target", "unknown"),
                    "reasoning": data.get("reasoning", "No reasoning provided"),
                    "raw_response": response
                }
            except Exception as e:
                return {
                    "agent": self.agent.name,
                    "type": "routing_error",
                    "error": str(e),
                    "raw_response": response
                }

        # Default strategic decision
        prompt = f"""Make a strategic decision on:

Situation: {task_input.get('situation', task_input)}

Consider multiple perspectives and provide a well-reasoned decision."""

        response = await self.generate_response(prompt)
        
        return {
            "agent": self.agent.name,
            "type": "executive_decision",
            "response": response,
            "reasoning_type": "strategic",
        }
