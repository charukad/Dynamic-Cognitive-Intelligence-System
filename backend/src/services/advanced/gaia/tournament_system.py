"""
GAIA Tournament System

Manages multi-agent tournaments with brackets and rankings.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4
from enum import Enum
import random

from pydantic import BaseModel

from src.core import get_logger
from src.services.advanced.gaia.match_engine import gaia_engine, OpponentType, MatchConfig

logger = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================

class TournamentFormat(str, Enum):
    """Tournament formats"""
    SINGLE_ELIMINATION = "single_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"


class TournamentStatus(str, Enum):
    """Tournament status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# Data Models
# ============================================================================

class TournamentConfig(BaseModel):
    """Tournament configuration"""
    format: TournamentFormat
    rounds_per_match: int = 5
    domain: str = "general"


class TournamentMatch(BaseModel):
    """Match within a tournament"""
    match_id: UUID
    round_number: int
    bracket_position: int
    player1_id: str
    player2_id: str
    winner_id: Optional[str] = None
    status: str = "pending"


class Tournament(BaseModel):
    """Tournament structure"""
    id: UUID = UUID(int=0)
    name: str
    format: TournamentFormat
    participant_ids: List[str]
    config: TournamentConfig
    status: TournamentStatus = TournamentStatus.PENDING
    current_round: int = 0
    matches: List[TournamentMatch] = []
    bracket: Dict[str, Any] = {}
    rankings: List[Dict[str, Any]] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


# ============================================================================
# Tournament System
# ============================================================================

class TournamentSystem:
    """
    Manages multi-agent tournaments.
    
    Supports:
    - Single elimination brackets
    - Round robin (everyone plays everyone)
    - Swiss system (pair by performance)
    """
    
    def __init__(self):
        self.active_tournaments: Dict[UUID, Tournament] = {}
        self.completed_tournaments: List[Tournament] = []
    
    async def create_tournament(
        self,
        name: str,
        agent_ids: List[str],
        format: TournamentFormat,
        config: Optional[TournamentConfig] = None
    ) -> UUID:
        """
        Create a new tournament.
        
        Args:
            name: Tournament name
            agent_ids: List of participating agents
            format: Tournament format
            config: Configuration
            
        Returns:
            Tournament UUID
        """
        tournament = Tournament(
            id=uuid4(),
            name=name,
            format=format,
            participant_ids=agent_ids,
            config=config or TournamentConfig(format=format)
        )
        
        # Generate bracket
        if format == TournamentFormat.SINGLE_ELIMINATION:
            tournament.bracket = self._generate_elimination_bracket(agent_ids)
        elif format == TournamentFormat.ROUND_ROBIN:
            tournament.matches = self._generate_round_robin_matches(agent_ids)
        elif format == TournamentFormat.SWISS:
            tournament.bracket = {"rounds": [], "pairings": []}
        
        self.active_tournaments[tournament.id] = tournament
        
        logger.info(
            f"🏆 Created {format.value} tournament '{name}' "
            f"with {len(agent_ids)} participants"
        )
        
        return tournament.id
    
    def _generate_elimination_bracket(
        self,
        agent_ids: List[str]
    ) -> Dict[str, Any]:
        """Generate single elimination bracket"""
        # Shuffle for fairness
        participants = list(agent_ids)
        random.shuffle(participants)
        
        # Calculate number of rounds needed
        num_rounds = 0
        temp = len(participants)
        while temp > 1:
            temp = (temp + 1) // 2
            num_rounds += 1
        
        bracket = {
            "num_rounds": num_rounds,
            "rounds": []
        }
        
        # First round pairings
        first_round = []
        for i in range(0, len(participants), 2):
            if i + 1 < len(participants):
                first_round.append({
                    "position": i // 2,
                    "player1": participants[i],
                    "player2": participants[i + 1],
                    "winner": None
                })
            else:
                # Bye (auto-advance)
                first_round.append({
                    "position": i // 2,
                    "player1": participants[i],
                    "player2": None,
                    "winner": participants[i]
                })
        
        bracket["rounds"].append(first_round)
        
        # Generate placeholder rounds
        for round_num in range(1, num_rounds):
            prev_round_size = len(bracket["rounds"][round_num - 1])
            current_round_size = (prev_round_size + 1) // 2
            
            bracket["rounds"].append([
                {
                    "position": i,
                    "player1": None,  # Winner from previous round
                    "player2": None,
                    "winner": None
                }
                for i in range(current_round_size)
            ])
        
        return bracket
    
    def _generate_round_robin_matches(
        self,
        agent_ids: List[str]
    ) -> List[TournamentMatch]:
        """Generate round robin matches (everyone vs everyone)"""
        matches = []
        match_num = 0
        
        for i, agent1 in enumerate(agent_ids):
            for agent2 in agent_ids[i + 1:]:
                matches.append(TournamentMatch(
                    match_id=uuid4(),
                    round_number=1,
                    bracket_position=match_num,
                    player1_id=agent1,
                    player2_id=agent2
                ))
                match_num += 1
        
        logger.info(f"Generated {len(matches)} round robin matches")
        return matches
    
    async def start_tournament(self, tournament_id: UUID) -> None:
        """Start tournament execution"""
        tournament = self.active_tournaments.get(tournament_id)
        if not tournament:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        tournament.status = TournamentStatus.IN_PROGRESS
        tournament.start_time = datetime.utcnow()
        tournament.current_round = 1
        
        logger.info(f"🏁 Starting tournament {tournament.name}")
        
        # Execute based on format
        if tournament.format == TournamentFormat.SINGLE_ELIMINATION:
            await self._execute_elimination_tournament(tournament)
        elif tournament.format == TournamentFormat.ROUND_ROBIN:
            await self._execute_round_robin_tournament(tournament)
    
    async def _execute_elimination_tournament(
        self,
        tournament: Tournament
    ) -> None:
        """Execute single elimination tournament"""
        for round_idx, round_matches in enumerate(tournament.bracket["rounds"]):
            logger.info(f"🎯 Round {round_idx + 1}")
            
            for match_data in round_matches:
                if match_data["player2"] is None:
                    # Bye - auto-advance
                    continue
                
                # Create and run match
                match_id = await gaia_engine.create_match(
                    agent_id=match_data["player1"],
                    opponent_type=OpponentType.PEER,
                    config=MatchConfig(
                        rounds=tournament.config.rounds_per_match,
                        domain=tournament.config.domain
                    ),
                    opponent_id=match_data["player2"]
                )
                
                # Wait for completion (simplified - in production use callbacks)
                import asyncio
                while match_id in gaia_engine.active_matches:
                    await asyncio.sleep(1)
                
                # Get result
                match = gaia_engine.get_match_status(match_id)
                if match and match.result:
                    match_data["winner"] = match.result.winner_id
                    
                    # Advance winner to next round
                    if round_idx + 1 < len(tournament.bracket["rounds"]):
                        next_round = tournament.bracket["rounds"][round_idx + 1]
                        next_position = match_data["position"] // 2
                        
                        if match_data["position"] % 2 == 0:
                            next_round[next_position]["player1"] = match_data["winner"]
                        else:
                            next_round[next_position]["player2"] = match_data["winner"]
        
        # Final winner
        final_round = tournament.bracket["rounds"][-1]
        champion = final_round[0]["winner"] if final_round else None
        
        tournament.status = TournamentStatus.COMPLETED
        tournament.end_time = datetime.utcnow()
        tournament.rankings = self._calculate_elimination_rankings(tournament)
        
        logger.info(f"🏆 Tournament complete! Champion: {champion}")
        
        self.completed_tournaments.append(tournament)
        del self.active_tournaments[tournament.id]
    
    async def _execute_round_robin_tournament(
        self,
        tournament: Tournament
    ) -> None:
        """Execute round robin tournament"""
        for match_data in tournament.matches:
            match_id = await gaia_engine.create_match(
                agent_id=match_data.player1_id,
                opponent_type=OpponentType.PEER,
                config=MatchConfig(
                    rounds=tournament.config.rounds_per_match,
                    domain=tournament.config.domain
                ),
                opponent_id=match_data.player2_id
            )
            
            # Wait for completion
            import asyncio
            while match_id in gaia_engine.active_matches:
                await asyncio.sleep(1)
            
            # Get result
            match = gaia_engine.get_match_status(match_id)
            if match and match.result:
                match_data.winner_id = match.result.winner_id
                match_data.status = "completed"
        
        tournament.status = TournamentStatus.COMPLETED
        tournament.end_time = datetime.utcnow()
        tournament.rankings = self._calculate_round_robin_rankings(tournament)
        
        logger.info(f"🏆 Round robin complete!")
        
        self.completed_tournaments.append(tournament)
        del self.active_tournaments[tournament.id]
    
    def _calculate_elimination_rankings(
        self,
        tournament: Tournament
    ) -> List[Dict[str, Any]]:
        """Calculate rankings from elimination bracket"""
        rankings = []
        
        # Champion (winner of final)
        final_round = tournament.bracket["rounds"][-1]
        if final_round and final_round[0]["winner"]:
            rankings.append({
                "rank": 1,
                "agent_id": final_round[0]["winner"],
                "eliminated_in_round": len(tournament.bracket["rounds"])
            })
        
        # Others based on elimination round
        # Simplified - in production, track all participants
        
        return rankings
    
    def _calculate_round_robin_rankings(
        self,
        tournament: Tournament
    ) -> List[Dict[str, Any]]:
        """Calculate rankings from round robin"""
        # Count wins for each participant
        wins = {agent_id: 0 for agent_id in tournament.participant_ids}
        
        for match in tournament.matches:
            if match.winner_id and match.winner_id in wins:
                wins[match.winner_id] += 1
        
        # Sort by wins
        sorted_agents = sorted(
            wins.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"rank": idx + 1, "agent_id": agent_id, "wins": win_count}
            for idx, (agent_id, win_count) in enumerate(sorted_agents)
        ]
    
    def get_tournament_status(
        self,
        tournament_id: UUID
    ) -> Optional[Tournament]:
        """Get tournament status"""
        if tournament_id in self.active_tournaments:
            return self.active_tournaments[tournament_id]
        
        for completed in self.completed_tournaments:
            if completed.id == tournament_id:
                return completed
        
        return None


# Global instance
tournament_system = TournamentSystem()
