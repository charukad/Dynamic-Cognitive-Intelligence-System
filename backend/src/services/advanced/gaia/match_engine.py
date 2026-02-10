"""
GAIA Match Engine - Self-Play Training System

Orchestrates matches between agents for adversarial training.
Inspired by AlphaZero's self-play methodology.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import UUID, uuid4
from enum import Enum
import math

from pydantic import BaseModel

from src.core import get_logger
from src.services.memory.knowledge_graph import knowledge_graph_service as neo4j_service

logger = get_logger(__name__)


# ============================================================================
# Enums and Types
# ============================================================================

class OpponentType(str, Enum):
    """Types of opponents for self-play"""
    SELF = "self"  # Agent vs itself
    SYNTHETIC = "synthetic"  # Agent vs AI-generated opponent
    HISTORICAL = "historical"  # Agent vs past version
    PEER = "peer"  # Agent vs another agent


class MatchStatus(str, Enum):
    """Match status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# Data Models
# ============================================================================

class OpponentProfile(BaseModel):
    """Profile of an opponent"""
    id: UUID = field(default_factory=uuid4)
    type: OpponentType
    name: str
    strategy: str  # aggressive, defensive, balanced, random
    skill_level: float  # 0.0 to 1.0
    behavior_pattern: str
    weaknesses: List[str] = []
    elo_rating: float = 1500.0


class MatchConfig(BaseModel):
    """Configuration for a match"""
    rounds: int = 5
    time_limit_seconds: Optional[int] = None
    domain: str = "general"
    difficulty: float = 0.5


class MatchResult(BaseModel):
    """Result of a completed match"""
    match_id: UUID
    winner_id: Optional[str]  # None for draw
    player1_score: float
    player2_score: float
    rounds_played: int
    total_moves: int
    duration_seconds: float
    performance_metrics: Dict[str, float]
    learning_rate: float


class GAIAMatch(BaseModel):
    """A self-play match"""
    id: UUID = field(default_factory=uuid4)
    agent_id: str
    opponent: OpponentProfile
    config: MatchConfig
    status: MatchStatus = MatchStatus.PENDING
    current_round: int = 0
    agent_score: float = 0.0
    opponent_score: float = 0.0
    trajectory: List[Dict[str, Any]] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[MatchResult] = None


# ============================================================================
# ELO Rating Calculator
# ============================================================================

class ELORatingCalculator:
    """
    Calculate ELO ratings for agent skill tracking.
    
    Standard chess ELO system adapted for agent performance.
    """
    
    def __init__(self, k_factor: float = 32.0):
        """
        Initialize ELO calculator.
        
        Args:
            k_factor: Maximum rating change per game (32 for new players)
        """
        self.k_factor = k_factor
    
    def expected_score(
        self,
        rating_a: float,
        rating_b: float
    ) -> float:
        """
        Calculate expected score for player A vs player B.
        
        Args:
            rating_a: Player A's rating
            rating_b: Player B's rating
            
        Returns:
            Expected score (0.0 to 1.0)
        """
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))
    
    def update_ratings(
        self,
        rating_a: float,
        rating_b: float,
        score_a: float
    ) -> Tuple[float, float]:
        """
        Update ratings after a match.
        
        Args:
            rating_a: Player A's current rating
            rating_b: Player B's current rating
            score_a: Player A's score (1.0 = win, 0.5 = draw, 0.0 = loss)
            
        Returns:
            (new_rating_a, new_rating_b)
        """
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = 1.0 - expected_a
        
        score_b = 1.0 - score_a
        
        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * (score_b - expected_b)
        
        return new_rating_a, new_rating_b


# ============================================================================
# GAIA Match Engine
# ============================================================================

class GAIAMatchEngine:
    """
    Orchestrates self-play matches for agent training.
    
    Features:
    - Agent vs Self (discover optimal strategies)
    - Agent vs Synthetic (curriculum learning)
    - Agent vs Historical (measure improvement)
    - Agent vs Peer (competitive learning)
    """
    
    def __init__(self):
        self.active_matches: Dict[UUID, GAIAMatch] = {}
        self.completed_matches: List[GAIAMatch] = []
        self.elo_calculator = ELORatingCalculator(k_factor=32.0)
        self.agent_ratings: Dict[str, float] = {}  # agent_id -> ELO
    
    async def create_match(
        self,
        agent_id: str,
        opponent_type: OpponentType,
        config: Optional[MatchConfig] = None,
        opponent_id: Optional[str] = None
    ) -> UUID:
        """
        Create a new self-play match.
        
        Args:
            agent_id: Agent identifier
            opponent_type: Type of opponent
            config: Match configuration
            opponent_id: Specific opponent ID (for peer matches)
            
        Returns:
            Match UUID
        """
        # Generate opponent profile
        opponent = await self._generate_opponent(
            agent_id,
            opponent_type,
            config.difficulty if config else 0.5,
            opponent_id
        )
        
        match = GAIAMatch(
            agent_id=agent_id,
            opponent=opponent,
            config=config or MatchConfig()
        )
        
        self.active_matches[match.id] = match
        
        logger.info(
            f"⚔️ Created match {match.id}: {agent_id} vs "
            f"{opponent.name} ({opponent_type.value})"
        )
        
        # Store in Neo4j
        await self._store_match_start(match)
        
        # Start async match execution
        asyncio.create_task(self._run_match(match.id))
        
        return match.id
    
    async def _run_match(self, match_id: UUID) -> None:
        """
        Execute a match asynchronously.
        
        Args:
            match_id: Match identifier
        """
        match = self.active_matches[match_id]
        match.status = MatchStatus.IN_PROGRESS
        match.start_time = datetime.utcnow()
        
        try:
            logger.info(f"⚔️ Starting match {match_id}")
            
            # Simulate match rounds
            for round_num in range(1, match.config.rounds + 1):
                match.current_round = round_num
                
                # Simulate round
                round_result = await self._simulate_round(
                    match.agent_id,
                    match.opponent,
                    round_num,
                    match.config.domain
                )
                
                # Update scores
                match.agent_score += round_result['agent_points']
                match.opponent_score += round_result['opponent_points']
                
                # Record trajectory
                match.trajectory.append({
                    'round': round_num,
                    'agent_move': round_result['agent_move'],
                    'opponent_move': round_result['opponent_move'],
                    'outcome': round_result['outcome']
                })
                
                logger.debug(
                    f"Round {round_num}: Agent {round_result['agent_points']} - "
                    f"{round_result['opponent_points']} Opponent"
                )
            
            # Determine winner
            winner_id = match.agent_id if match.agent_score > match.opponent_score else \
                       str(match.opponent.id) if match.opponent_score > match.agent_score else None
            
            # Calculate result
            match.end_time = datetime.utcnow()
            duration = (match.end_time - match.start_time).total_seconds()
            
            match.result = MatchResult(
                match_id=match.id,
                winner_id=winner_id,
                player1_score=match.agent_score,
                player2_score=match.opponent_score,
                rounds_played=match.config.rounds,
                total_moves=len(match.trajectory),
                duration_seconds=duration,
                performance_metrics=self._calculate_metrics(match),
                learning_rate=self._calculate_learning_rate(match)
            )
            
            # Update ELO ratings
            await self._update_elo_ratings(match)
            
            match.status = MatchStatus.COMPLETED
            
            logger.info(
                f"✅ Match {match_id} complete! Winner: {winner_id or 'DRAW'} "
                f"({match.agent_score:.1f} - {match.opponent_score:.1f})"
            )
            
        except Exception as e:
            logger.error(f"❌ Match {match_id} failed: {e}", exc_info=True)
            match.status = MatchStatus.CANCELLED
        
        finally:
            # Move to completed
            self.completed_matches.append(match)
            del self.active_matches[match_id]
            
            # Store final result
            await self._store_match_completion(match)
    
    async def _simulate_round(
        self,
        agent_id: str,
        opponent: OpponentProfile,
        round_num: int,
        domain: str
    ) -> Dict[str, Any]:
        """
        Simulate a single round of the match.
        
        Args:
            agent_id: Agent ID
            opponent: Opponent profile
            round_num: Current round number
            domain: Problem domain
            
        Returns:
            Round result
        """
        # Simplified simulation - in production, this would:
        # 1. Generate a problem/scenario
        # 2. Get responses from both players
        # 3. Evaluate quality/correctness
        # 4. Assign points
        
        await asyncio.sleep(0.2)  # Simulate thinking time
        
        # Random outcome weighted by skill levels
        agent_skill = self.agent_ratings.get(agent_id, 1500) / 3000
        opponent_skill = opponent.skill_level
        
        agent_performance = agent_skill + (hash(f"{round_num}{agent_id}") % 100) / 200
        opponent_performance = opponent_skill + (hash(f"{round_num}{opponent.id}") % 100) / 200
        
        if agent_performance > opponent_performance:
            outcome = "agent_win"
            agent_points = 1.0
            opponent_points = 0.0
        elif opponent_performance > agent_performance:
            outcome = "opponent_win"
            agent_points = 0.0
            opponent_points = 1.0
        else:
            outcome = "draw"
            agent_points = 0.5
            opponent_points = 0.5
        
        return {
            'agent_move': f"move_{round_num}_a",
            'opponent_move': f"move_{round_num}_o",
            'outcome': outcome,
            'agent_points': agent_points,
            'opponent_points': opponent_points
        }
    
    async def _generate_opponent(
        self,
        agent_id: str,
        opponent_type: OpponentType,
        difficulty: float,
        opponent_id: Optional[str] = None
    ) -> OpponentProfile:
        """Generate opponent based on type"""
        
        if opponent_type == OpponentType.SELF:
            return OpponentProfile(
                type=OpponentType.SELF,
                name=f"{agent_id} (Mirror)",
                strategy="mimic",
                skill_level=self.agent_ratings.get(agent_id, 1500) / 3000,
                behavior_pattern="adaptive",
                elo_rating=self.agent_ratings.get(agent_id, 1500)
            )
        
        elif opponent_type == OpponentType.SYNTHETIC:
            strategies = ["aggressive", "defensive", "balanced", "random"]
            strategy = strategies[hash(agent_id) % len(strategies)]
            
            return OpponentProfile(
                type=OpponentType.SYNTHETIC,
                name=f"Synthetic-{uuid4().hex[:8]}",
                strategy=strategy,
                skill_level=difficulty,
                behavior_pattern="predictable" if difficulty < 0.7 else "adaptive",
                weaknesses=["time_pressure"] if difficulty < 0.5 else [],
                elo_rating=1000 + difficulty * 1000
            )
        
        elif opponent_type == OpponentType.HISTORICAL:
            # Past version of agent (lower skill)
            return OpponentProfile(
                type=OpponentType.HISTORICAL,
                name=f"{agent_id} (v0.9)",
                strategy="past_strategy",
                skill_level=max(0.3, difficulty - 0.2),
                behavior_pattern="historical",
                elo_rating=max(1000, self.agent_ratings.get(agent_id, 1500) - 200)
            )
        
        else:  # PEER
            return OpponentProfile(
                type=OpponentType.PEER,
                name=opponent_id or "peer_agent",
                strategy="competitive",
                skill_level=difficulty,
                behavior_pattern="adaptive",
                elo_rating=self.agent_ratings.get(opponent_id, 1500) if opponent_id else 1500
            )
    
    def _calculate_metrics(self, match: GAIAMatch) -> Dict[str, float]:
        """Calculate performance metrics"""
        total_rounds = match.config.rounds
        win_rate = match.agent_score / total_rounds if total_rounds > 0 else 0.0
        
        return {
            "win_rate": win_rate,
            "avg_score": match.agent_score / total_rounds if total_rounds > 0 else 0.0,
            "dominance": abs(match.agent_score - match.opponent_score) / total_rounds
        }
    
    def _calculate_learning_rate(self, match: GAIAMatch) -> float:
        """Calculate learning rate from match"""
        # Higher learning when facing challenging opponents
        skill_gap = abs(match.opponent.skill_level - 0.5)
        return min(0.3, 0.1 + skill_gap * 0.4)
    
    async def _update_elo_ratings(self, match: GAIAMatch) -> None:
        """Update ELO ratings after match"""
        agent_rating = self.agent_ratings.get(match.agent_id, 1500.0)
        opponent_rating = match.opponent.elo_rating
        
        # Calculate score (1.0 = win, 0.5 = draw, 0.0 = loss)
        total_points = match.agent_score + match.opponent_score
        agent_score = match.agent_score / total_points if total_points > 0 else 0.5
        
        # Update ratings
        new_agent_rating, new_opponent_rating = self.elo_calculator.update_ratings(
            agent_rating,
            opponent_rating,
            agent_score
        )
        
        self.agent_ratings[match.agent_id] = new_agent_rating
        
        logger.info(
            f"📊 ELO Update: {match.agent_id} "
            f"{agent_rating:.0f} → {new_agent_rating:.0f} "
            f"({new_agent_rating - agent_rating:+.0f})"
        )
    
    async def _store_match_start(self, match: GAIAMatch) -> None:
        """Store match start in Neo4j"""
        await neo4j_service.execute_query(
            """
            MERGE (a:Agent {id: $agent_id})
            CREATE (m:Match {
                id: $match_id,
                opponent_type: $opponent_type,
                opponent_name: $opponent_name,
                start_time: datetime($start_time),
                status: $status,
                rounds: $rounds
            })
            CREATE (a)-[:PLAYING]->(m)
            """,
            {
                "agent_id": match.agent_id,
                "match_id": str(match.id),
                "opponent_type": match.opponent.type.value,
                "opponent_name": match.opponent.name,
                "start_time": datetime.utcnow().isoformat(),
                "status": match.status.value,
                "rounds": match.config.rounds
            }
        )
    
    async def _store_match_completion(self, match: GAIAMatch) -> None:
        """Store match completion"""
        if not match.result:
            return
        
        await neo4j_service.execute_query(
            """
            MATCH (m:Match {id: $match_id})
            SET m.end_time = datetime($end_time),
                m.status = $status,
                m.winner_id = $winner_id,
                m.agent_score = $agent_score,
                m.opponent_score = $opponent_score,
                m.duration_seconds = $duration
            """,
            {
                "match_id": str(match.id),
                "end_time": match.end_time.isoformat() if match.end_time else None,
                "status": match.status.value,
                "winner_id": match.result.winner_id,
                "agent_score": match.agent_score,
                "opponent_score": match.opponent_score,
                "duration": match.result.duration_seconds
            }
        )
    
    def get_match_status(self, match_id: UUID) -> Optional[GAIAMatch]:
        """Get match status"""
        if match_id in self.active_matches:
            return self.active_matches[match_id]
        
        for completed in self.completed_matches:
            if completed.id == match_id:
                return completed
        
        return None
    
    def get_leaderboard(self, domain: str = "general", limit: int = 20) -> List[Dict[str, Any]]:
        """Get ELO leaderboard"""
        rankings = [
            {"agent_id": agent_id, "elo": rating, "rank": idx + 1}
            for idx, (agent_id, rating) in enumerate(
                sorted(self.agent_ratings.items(), key=lambda x: x[1], reverse=True)
            )
        ]
        return rankings[:limit]


# Global instance
gaia_engine = GAIAMatchEngine()

# Alias for backwards compatibility
MatchEngine = GAIAMatchEngine
