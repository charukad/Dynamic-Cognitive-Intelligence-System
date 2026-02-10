"""Monte Carlo Tree Search (MCTS) implementation for Gaia simulator."""

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.core import get_logger

logger = get_logger(__name__)


@dataclass
class MCTSNode:
    """Node in the MCTS tree."""
    
    state: Any
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    reward: float = 0.0
    untried_actions: List[Any] = field(default_factory=list)
    action: Any = None  # Action that led to this node
    
    @property
    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried."""
        return len(self.untried_actions) == 0
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return len(self.untried_actions) == 0 and len(self.children) == 0


class MCTS:
    """
    Monte Carlo Tree Search implementation.
    
    Used by Gaia simulator to explore decision trees and find optimal strategies.
    """

    def __init__(
        self,
        exploration_weight: float = 1.414,  # UCB1 exploration constant
        max_iterations: int = 1000,
        max_depth: int = 50,
    ) -> None:
        """
        Initialize MCTS.
        
        Args:
            exploration_weight: UCB1 exploration constant (√2 is optimal)
            max_iterations: Maximum search iterations
            max_depth: Maximum tree depth
        """
        self.exploration_weight = exploration_weight
        self.max_iterations = max_iterations
        self.max_depth = max_depth

    def search(
        self,
        initial_state: Any,
        get_actions_fn: Callable[[Any], List[Any]],
        apply_action_fn: Callable[[Any, Any], Any],
        is_terminal_fn: Callable[[Any], bool],
        evaluate_fn: Callable[[Any], float],
    ) -> tuple[Any, float]:
        """
        Execute MCTS to find best action.
        
        Args:
            initial_state: Starting state
            get_actions_fn: Function to get available actions for a state
            apply_action_fn: Function to apply action to state
            is_terminal_fn: Function to check if state is terminal
            evaluate_fn: Function to evaluate terminal state
            
        Returns:
            Tuple of (best_action, expected_reward)
        """
        logger.info("Starting MCTS search")
        
        # Create root node
        root = MCTSNode(
            state=initial_state,
            untried_actions=get_actions_fn(initial_state),
        )
        
        # Execute iterations
        for iteration in range(self.max_iterations):
            # Selection & Expansion
            node = self._select(root, get_actions_fn, apply_action_fn, is_terminal_fn)
            
            # Simulation (Rollout)
            reward = self._simulate(
                node.state,
                get_actions_fn,
                apply_action_fn,
                is_terminal_fn,
                evaluate_fn,
            )
            
            # Backpropagation
            self._backpropagate(node, reward)
            
            if (iteration + 1) % 100 == 0:
                logger.debug(f"MCTS iteration {iteration + 1}/{self.max_iterations}")
        
        # Select best action
        best_child = self._best_child(root, exploration_weight=0)  # Exploit only
        
        if best_child:
            expected_reward = best_child.reward / best_child.visits if best_child.visits > 0 else 0.0
            logger.info(f"MCTS completed: best action={best_child.action}, expected_reward={expected_reward:.3f}")
            return best_child.action, expected_reward
        
        # Fallback to random action
        actions = get_actions_fn(initial_state)
        if actions:
            return random.choice(actions), 0.0
        
        return None, 0.0

    def _select(
        self,
        node: MCTSNode,
        get_actions_fn: Callable,
        apply_action_fn: Callable,
        is_terminal_fn: Callable,
        depth: int = 0,
    ) -> MCTSNode:
        """
        Selection phase: traverse tree using UCB1 until expandable node found.
        
        Args:
            node: Current node
            get_actions_fn: Function to get actions
            apply_action_fn: Function to apply actions
            is_terminal_fn: Function to check terminal
            depth: Current depth
            
        Returns:
            Selected node for expansion
        """
        # Stop if terminal or max depth
        if is_terminal_fn(node.state) or depth >= self.max_depth:
            return node
        
        # Expand if not fully expanded
        if not node.is_fully_expanded:
            return self._expand(node, get_actions_fn, apply_action_fn)
        
        # Otherwise, select best child using UCB1
        best_child = self._best_child(node, self.exploration_weight)
        
        if best_child:
            return self._select(
                best_child,
                get_actions_fn,
                apply_action_fn,
                is_terminal_fn,
                depth + 1,
            )
        
        return node

    def _expand(
        self,
        node: MCTSNode,
        get_actions_fn: Callable,
        apply_action_fn: Callable,
    ) -> MCTSNode:
        """
        Expansion phase: create child node for untried action.
        
        Args:
            node: Node to expand
            get_actions_fn: Function to get actions
            apply_action_fn: Function to apply actions
            
        Returns:
            New child node
        """
        # Select random untried action
        action = random.choice(node.untried_actions)
        node.untried_actions.remove(action)
        
        # Apply action to get new state
        new_state = apply_action_fn(node.state, action)
        
        # Create child node
        child = MCTSNode(
            state=new_state,
            parent=node,
            action=action,
            untried_actions=get_actions_fn(new_state),
        )
        
        node.children.append(child)
        
        return child

    def _simulate(
        self,
        state: Any,
        get_actions_fn: Callable,
        apply_action_fn: Callable,
        is_terminal_fn: Callable,
        evaluate_fn: Callable,
        max_depth: int = 50,
    ) -> float:
        """
        Simulation phase: random rollout to terminal state.
        
        Args:
            state: Starting state
            get_actions_fn: Function to get actions
            apply_action_fn: Function to apply actions
            is_terminal_fn: Function to check terminal
            evaluate_fn: Function to evaluate state
            max_depth: Maximum rollout depth
            
        Returns:
            Reward from terminal state
        """
        current_state = state
        depth = 0
        
        while not is_terminal_fn(current_state) and depth < max_depth:
            actions = get_actions_fn(current_state)
            
            if not actions:
                break
            
            # Random rollout policy
            action = random.choice(actions)
            current_state = apply_action_fn(current_state, action)
            depth += 1
        
        # Evaluate terminal state
        reward = evaluate_fn(current_state)
        
        return reward

    def _backpropagate(self, node: MCTSNode, reward: float) -> None:
        """
        Backpropagation phase: update node statistics up the tree.
        
        Args:
            node: Leaf node to start from
            reward: Reward to backpropagate
        """
        current = node
        
        while current is not None:
            current.visits += 1
            current.reward += reward
            current = current.parent

    def _best_child(
        self,
        node: MCTSNode,
        exploration_weight: float,
    ) -> Optional[MCTSNode]:
        """
        Select best child using UCB1 formula.
        
        UCB1 = exploitation + exploration
             = (avg_reward) + c * sqrt(ln(parent_visits) / child_visits)
        
        Args:
            node: Parent node
            exploration_weight: Exploration constant
            
        Returns:
            Best child node or None
        """
        if not node.children:
            return None
        
        best_score = float('-inf')
        best_child = None
        
        for child in node.children:
            if child.visits == 0:
                # Prioritize unvisited children
                score = float('inf')
            else:
                # UCB1 formula
                exploitation = child.reward / child.visits
                exploration = exploration_weight * math.sqrt(
                    math.log(node.visits) / child.visits
                )
                score = exploitation + exploration
            
            if score > best_score:
                best_score = score
                best_child = child
        
        return best_child

    def get_tree_stats(self, node: MCTSNode) -> Dict[str, Any]:
        """
        Get statistics about the MCTS tree.
        
        Args:
            node: Root node
            
        Returns:
            Tree statistics
        """
        total_nodes = 0
        max_depth = 0
        
        def traverse(n: MCTSNode, depth: int = 0):
            nonlocal total_nodes, max_depth
            total_nodes += 1
            max_depth = max(max_depth, depth)
            
            for child in n.children:
                traverse(child, depth + 1)
        
        traverse(node)
        
        return {
            "total_nodes": total_nodes,
            "max_depth": max_depth,
            "root_visits": node.visits,
            "root_reward": node.reward,
            "avg_root_reward": node.reward / node.visits if node.visits > 0 else 0.0,
        }


# Singleton instance
mcts = MCTS()
