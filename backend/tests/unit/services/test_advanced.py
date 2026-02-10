"""Unit tests for advanced AI services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.advanced.gaia import GaiaSimulator, MCTSNode
from src.services.advanced.debater import debater_service
from src.services.advanced.swarm import swarm_optimizer


@pytest.mark.unit
@pytest.mark.asyncio
class TestGaiaMCTS:
    """Test suite for Gaia MCTS Simulator."""

    def test_mcts_node_creation(self):
        """Test creating MCTS node."""
        node = MCTSNode(state={"step": 0})
        
        assert node is not None
        assert node.state == {"step": 0}
        assert node.visits == 0
        assert node.value == 0.0

    def test_node_ucb1_calculation(self):
        """Test UCB1 score calculation."""
        parent = MCTSNode(state={"step": 0})
        parent.visits = 10
        
        child = MCTSNode(state={"step": 1}, parent=parent)
        child.visits = 5
        child.value = 3.0
        
        ucb1 = child.ucb1_score()
        
        assert ucb1 > 0

    def test_node_is_fully_expanded(self):
        """Test checking if node is fully expanded."""
        node = MCTSNode(state={"step": 0})
        
        # Initially not expanded
        assert not node.is_fully_expanded()

    async def test_simulator_initialization(self, mock_llm_client):
        """Test Gaia simulator initialization."""
        simulator = GaiaSimulator(llm_client=mock_llm_client)
        
        assert simulator is not None
        assert simulator.llm_client == mock_llm_client

    async def test_simulate_strategy(self, mock_llm_client):
        """Test simulating a strategy."""
        simulator = GaiaSimulator(llm_client=mock_llm_client)
        
        initial_state = {"goal": "Solve problem"}
        
        result = await simulator.simulate_strategy(
            initial_state=initial_state,
            iterations=10,
        )
        
        assert result is not None
        assert "best_path" in result
        assert "score" in result

    async def test_conversation_strategy(self, mock_llm_client):
        """Test simulating conversation strategy."""
        simulator = GaiaSimulator(llm_client=mock_llm_client)
        
        result = await simulator.simulate_conversation_strategy(
            topic="AI Ethics",
            num_turns=5,
        )
        
        assert result is not None
        assert "conversation" in result

    async def test_mcts_selection(self, mock_llm_client):
        """Test MCTS selection phase."""
        simulator = GaiaSimulator(llm_client=mock_llm_client)
        
        root = MCTSNode(state={"step": 0})
        
        # Add some children
        child1 = MCTSNode(state={"step": 1}, parent=root)
        child2 = MCTSNode(state={"step": 2}, parent=root)
        root.children = [child1, child2]
        
        # Give child1 better stats
        child1.visits = 5
        child1.value = 4.0
        root.visits = 10
        
        selected = simulator._select(root)
        
        assert selected is not None

    async def test_mcts_expansion(self, mock_llm_client):
        """Test MCTS expansion phase."""
        simulator = GaiaSimulator(llm_client=mock_llm_client)
        
        node = MCTSNode(state={"step": 0, "actions": ["action1", "action2"]})
        
        expanded = simulator._expand(node)
        
        assert expanded is not None
        assert expanded.parent == node

    async def test_mcts_backpropagation(self, mock_llm_client):
        """Test MCTS backpropagation."""
        simulator = GaiaSimulator(llm_client=mock_llm_client)
        
        root = MCTSNode(state={"step": 0})
        child = MCTSNode(state={"step": 1}, parent=root)
        
        # Backpropagate a reward
        simulator._backpropagate(child, reward=1.0)
        
        assert child.visits == 1
        assert child.value == 1.0
        assert root.visits == 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestDebaterService:
    """Test suite for multi-agent debater."""

    async def test_debater_initialization(self, mock_llm_client):
        """Test debater service initialization."""
        service = debater_service
        service.llm_client = mock_llm_client
        
        assert service is not None

    async def test_create_debate(self, sample_agents, mock_llm_client):
        """Test creating a debate."""
        service = debater_service
        service.llm_client = mock_llm_client
        
        # Register agents
        for agent in sample_agents[:2]:  # Use 2 agents
            await service.agent_repo.create(agent)
        
        debate_id = await service.create_debate(
            topic="Is AI beneficial?",
            agent_ids=[a.id for a in sample_agents[:2]],
        )
        
        assert debate_id is not None

    async def test_execute_debate_round(self, sample_agents, mock_llm_client):
        """Test executing one debate round."""
        service = debater_service
        service.llm_client = mock_llm_client
        
        for agent in sample_agents[:2]:
            await service.agent_repo.create(agent)
        
        debate_id = await service.create_debate(
            topic="Is Python better than Java?",
            agent_ids=[a.id for a in sample_agents[:2]],
        )
        
        result = await service.execute_round(debate_id, round_number=1)
        
        assert result is not None
        assert "arguments" in result or len(result) > 0

    async def test_get_debate_summary(self, sample_agents, mock_llm_client):
        """Test getting debate summary."""
        service = debater_service
        service.llm_client = mock_llm_client
        
        for agent in sample_agents[:2]:
            await service.agent_repo.create(agent)
        
        debate_id = await service.create_debate(
            topic="Test Topic",
            agent_ids=[a.id for a in sample_agents[:2]],
        )
        
        # Execute a round
        await service.execute_round(debate_id, round_number=1)
        
        summary = await service.get_debate_summary(debate_id)
        
        assert summary is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestSwarmOptimizer:
    """Test suite for swarm optimization."""

    def test_swarm_initialization(self):
        """Test swarm optimizer initialization."""
        optimizer = swarm_optimizer
        
        assert optimizer is not None

    async def test_optimize_simple(self):
        """Test simple optimization problem."""
        optimizer = swarm_optimizer
        
        # Define a simple objective function
        def objective(x):
            return sum([(xi - 1.0) ** 2 for xi in x])
        
        result = await optimizer.optimize(
            objective_function=objective,
            dimensions=3,
            num_particles=10,
            iterations=20,
        )
        
        assert result is not None
        assert "best_position" in result
        assert "best_score" in result

    async def test_optimize_with_bounds(self):
        """Test optimization with parameter bounds."""
        optimizer = swarm_optimizer
        
        def objective(x):
            return sum([xi ** 2 for xi in x])
        
        result = await optimizer.optimize(
            objective_function=objective,
            dimensions=2,
            num_particles=5,
            iterations=10,
            bounds=[(-10, 10), (-10, 10)],
        )
        
        assert result is not None
        # Best position should be near zero
        assert len(result["best_position"]) == 2

    async def test_particle_initialization(self):
        """Test particle initialization."""
        optimizer = swarm_optimizer
        
        particles = optimizer._initialize_particles(
            num_particles=5,
            dimensions=3,
            bounds=[(-5, 5)] * 3,
        )
        
        assert len(particles) == 5
        assert all(len(p["position"]) == 3 for p in particles)

    async def test_velocity_update(self):
        """Test particle velocity update."""
        optimizer = swarm_optimizer
        
        particle = {
            "position": [1.0, 2.0],
            "velocity": [0.1, 0.2],
            "best_position": [1.5, 2.5],
            "best_score": 1.0,
        }
        
        global_best = [2.0, 3.0]
        
        new_velocity = optimizer._update_velocity(
            particle=particle,
            global_best_position=global_best,
        )
        
        assert len(new_velocity) == 2

    async def test_parallel_evaluation(self):
        """Test parallel objective function evaluation."""
        optimizer = swarm_optimizer
        
        def objective(x):
            return sum([xi ** 2 for xi in x])
        
        particles = [
            {"position": [1.0, 2.0]},
            {"position": [3.0, 4.0]},
        ]
        
        scores = await optimizer._evaluate_particles(objective, particles)
        
        assert len(scores) == 2
        assert all(isinstance(s, (int, float)) for s in scores)
