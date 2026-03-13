"""Gaia simulator for state space exploration."""

from typing import Any, Callable, Dict, List, Optional

from src.core import get_logger
from .mcts import MCTSNode, mcts

logger = get_logger(__name__)


class GaiaSimulator:
    """
    Gaia simulator for exploring decision spaces using MCTS.
    
    Simulates different strategies and finds optimal paths through
    complex state spaces.
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        exploration_weight: float = 1.414,
        max_iterations: int = 1000,
    ) -> None:
        """
        Initialize Gaia simulator.
        
        Args:
            llm_client: Optional LLM client (legacy compatibility)
            exploration_weight: MCTS exploration constant
            max_iterations: Maximum MCTS iterations
        """
        self.llm_client = llm_client
        self.mcts = mcts
        self.mcts.exploration_weight = exploration_weight
        self.mcts.max_iterations = max_iterations

    async def simulate_strategy(
        self,
        initial_state: Dict[str, Any],
        iterations: int = 20,
    ) -> Dict[str, Any]:
        """
        Legacy strategy simulation API expected by older tests.
        """
        actions = initial_state.get(
            "actions",
            ["analyze", "plan", "execute", "review"],
        )
        self.mcts.max_iterations = max(1, int(iterations))

        result = await self.find_optimal_strategy(
            problem_description="Legacy strategy simulation",
            initial_state=initial_state,
            goal_state={"progress": 1.0},
            available_actions=actions,
        )

        best_action = result.get("recommended_action")
        return {
            "best_path": [best_action] if best_action else [],
            "score": result.get("expected_reward", 0.0),
            "strategy": result,
        }

    async def find_optimal_strategy(
        self,
        problem_description: str,
        initial_state: Dict[str, Any],
        goal_state: Dict[str, Any],
        available_actions: List[str],
    ) -> Dict[str, Any]:
        """
        Find optimal strategy for achieving goal from initial state.
        
        Args:
            problem_description: Description of the problem
            initial_state: Starting state
            goal_state: Target state
            available_actions: List of available action names
            
        Returns:
            Strategy recommendation with expected reward
        """
        logger.info(f"Finding optimal strategy for: {problem_description}")

        # Define state space functions
        def get_actions(state: Dict[str, Any]) -> List[str]:
            """Get available actions for a state."""
            # Filter actions based on state
            valid_actions = []
            for action in available_actions:
                if self._is_action_valid(state, action):
                    valid_actions.append(action)
            return valid_actions

        def apply_action(state: Dict[str, Any], action: str) -> Dict[str, Any]:
            """Apply action to state."""
            return self._simulate_action(state, action)

        def is_terminal(state: Dict[str, Any]) -> bool:
            """Check if state is terminal."""
            return self._matches_goal(state, goal_state) or self._is_failed_state(state)

        def evaluate(state: Dict[str, Any]) -> float:
            """Evaluate terminal state."""
            if self._matches_goal(state, goal_state):
                return 1.0  # Success
            return 0.0  # Failure

        # Run MCTS
        best_action, expected_reward = self.mcts.search(
            initial_state=initial_state,
            get_actions_fn=get_actions,
            apply_action_fn=apply_action,
            is_terminal_fn=is_terminal,
            evaluate_fn=evaluate,
        )

        return {
            "problem": problem_description,
            "recommended_action": best_action,
            "expected_reward": expected_reward,
            "confidence": expected_reward,
            "initial_state": initial_state,
            "goal_state": goal_state,
        }

    def _is_action_valid(self, state: Dict[str, Any], action: str) -> bool:
        """
        Check if action is valid in current state.
        
        Args:
            state: Current state
            action: Action to validate
            
        Returns:
            True if action is valid
        """
        # Simple validation - can be extended
        return True

    def _simulate_action(
        self,
        state: Dict[str, Any],
        action: str,
    ) -> Dict[str, Any]:
        """
        Simulate applying an action to a state.
        
        Args:
            state: Current state
            action: Action to apply
            
        Returns:
            New state after action
        """
        # Create new state (don't modify original)
        new_state = state.copy()
        
        # Simple state transition simulation
        # In production, this would use domain-specific logic
        new_state["step"] = state.get("step", 0) + 1
        new_state["last_action"] = action
        
        # Simulate some progress toward goal
        if "progress" in new_state:
            new_state["progress"] = min(1.0, new_state.get("progress", 0.0) + 0.1)
        
        return new_state

    def _matches_goal(
        self,
        state: Dict[str, Any],
        goal: Dict[str, Any],
    ) -> bool:
        """
        Check if state matches goal.
        
        Args:
            state: Current state
            goal: Goal state
            
        Returns:
            True if goal is reached
        """
        # Check if all goal conditions are met
        for key, value in goal.items():
            if state.get(key) != value:
                # Check progress threshold
                if key == "progress" and state.get("progress", 0.0) >= 0.9:
                    return True
                return False
        return True

    def _is_failed_state(self, state: Dict[str, Any]) -> bool:
        """
        Check if state is a failure.
        
        Args:
            state: State to check
            
        Returns:
            True if state is failed
        """
        # Check for failure conditions
        if state.get("step", 0) > 100:  # Too many steps
            return True
        if state.get("failed", False):
            return True
        return False

    async def simulate_conversation_strategy(
        self,
        query: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        topic: Optional[str] = None,
        num_turns: int = 3,
    ) -> Dict[str, Any]:
        """
        Simulate conversation strategies to find best approach.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Recommended strategy
        """
        effective_query = topic or query or "general conversation"
        conversation_context = context or {}

        available_actions = [
            "ask_clarifying_question",
            "provide_direct_answer",
            "break_down_problem",
            "search_knowledge_base",
            "use_creative_approach",
            "use_analytical_approach",
        ]
        
        initial_state = {
            "query": effective_query,
            "understanding": 0.5,
            "progress": 0.0,
            "step": 0,
            "num_turns": num_turns,
            **conversation_context,
        }
        
        goal_state = {
            "progress": 1.0,
        }
        
        strategy = await self.find_optimal_strategy(
            problem_description=f"Respond to: {effective_query}",
            initial_state=initial_state,
            goal_state=goal_state,
            available_actions=available_actions,
        )
        return {
            "conversation": [
                {
                    "turn": i + 1,
                    "action": strategy.get("recommended_action"),
                    "topic": effective_query,
                }
                for i in range(max(1, num_turns))
            ],
            **strategy,
        }

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Legacy wrapper for MCTS selection phase."""
        if not node.children:
            return node
        selected = self.mcts._best_child(node, self.mcts.exploration_weight)
        return selected or node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """Legacy wrapper for MCTS expansion phase."""
        if not node.untried_actions:
            node.untried_actions = list(node.state.get("actions", []))
        if not node.untried_actions:
            node.untried_actions = ["next_step"]
        return self.mcts._expand(
            node,
            get_actions_fn=lambda state: list(state.get("actions", [])),
            apply_action_fn=lambda state, action: {
                **state,
                "step": state.get("step", 0) + 1,
                "last_action": action,
            },
        )

    def _backpropagate(self, node: MCTSNode, reward: float) -> None:
        """Legacy wrapper for MCTS backpropagation phase."""
        self.mcts._backpropagate(node, reward)


# Singleton instance
gaia_simulator = GaiaSimulator()
