"""
Advanced AI Services - Centralized Integration Manager

Integrates all advanced AI capabilities:
- Oneiroi Dreaming System
- GAIA Self-Play Tournament
- Multi-modal Processing
- Meta-Orchestrator
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from src.core import get_logger
from src.services.advanced.oneiroi.dream_engine import DreamEngine
from src.services.advanced.gaia.match_engine import MatchEngine
from src.services.advanced.multimodal.vision_processor import VisionProcessor
from src.services.advanced.multimodal.audio_processor import AudioProcessor
from src.services.orchestrator.meta_orchestrator import MetaOrchestrator

logger = get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AIServiceStatus:
    """Status of an AI service"""
    service_name: str
    status: str  # 'online', 'busy', 'offline'
    last_activity: datetime
    total_requests: int
    success_rate: float


@dataclass
class DreamCycleRequest:
    """Request to run a dream cycle"""
    agent_id: str
    num_experiences: int = 100
    focus_areas: List[str] = None


@dataclass
class MatchRequest:
    """Request to run a GAIA match"""
    agent_id: str
    opponent_type: str = 'synthetic'
    num_rounds: int = 5


@dataclass
class MultiModalRequest:
    """Request for multi-modal processing"""
    content_type: str  # 'image' or 'audio'
    content_data: bytes
    operations: List[str]  # ['caption', 'detect', 'ocr'] for images


# ============================================================================
# Advanced AI Services Manager
# ============================================================================

class AdvancedAIServicesManager:
    """
    Centralized manager for all advanced AI capabilities.
    
    Provides unified interface to:
    - Oneiroi dreaming for self-improvement
    - GAIA competitive training
    - Multi-modal processing (image/audio)
    - Meta-orchestration with AI enhancements
    """
    
    def __init__(self):
        self.dream_engine = DreamEngine()
        self.match_engine = MatchEngine()
        self.vision_processor = VisionProcessor()
        self.audio_processor = AudioProcessor()
        self.meta_orchestrator = MetaOrchestrator()
        
        # Service metrics
        self.service_metrics: Dict[str, AIServiceStatus] = {
            'oneiroi': AIServiceStatus(
                service_name='Oneiroi Dreaming',
                status='online',
                last_activity=datetime.now(),
                total_requests=0,
                success_rate=1.0
            ),
            'gaia': AIServiceStatus(
                service_name='GAIA Tournament',
                status='online',
                last_activity=datetime.now(),
                total_requests=0,
                success_rate=1.0
            ),
            'multimodal': AIServiceStatus(
                service_name='Multi-modal Processing',
                status='online',
                last_activity=datetime.now(),
                total_requests=0,
                success_rate=1.0
            ),
            'orchestrator': AIServiceStatus(
                service_name='Meta-Orchestrator',
                status='online',
                last_activity=datetime.now(),
                total_requests=0,
                success_rate=1.0
            )
        }
    
    # ========================================================================
    # Oneiroi Dreaming
    # ========================================================================
    
    async def run_dream_cycle(self, request: DreamCycleRequest) -> Dict[str, Any]:
        """
        Execute a complete dream cycle for agent self-improvement.
        
        Args:
            request: Dream cycle configuration
            
        Returns:
            Dream cycle results with insights
        """
        try:
            logger.info(f"Starting dream cycle for agent {request.agent_id}")
            self._update_metric('oneiroi', 'busy')
            
            # Run REM phase (experience replay)
            rem_results = await self.dream_engine.rem_phase(
                agent_id=request.agent_id,
                num_experiences=request.num_experiences
            )
            
            # Run NREM phase (pattern mining)
            nrem_results = await self.dream_engine.nrem_phase(
                experiences=rem_results['replayed_experiences']
            )
            
            # Integration phase (apply insights)
            integration_results = await self.dream_engine.integration_phase(
                agent_id=request.agent_id,
                patterns=nrem_results['patterns'],
                insights=nrem_results['insights']
            )
            
            self._update_metric('oneiroi', 'online', success=True)
            
            return {
                'dream_cycle_id': rem_results['cycle_id'],
                'agent_id': request.agent_id,
                'experiences_processed': request.num_experiences,
                'patterns_discovered': len(nrem_results['patterns']),
                'insights_generated': len(nrem_results['insights']),
                'insights_applied': len(integration_results['applied_insights']),
                'performance_improvement': integration_results.get('improvement_score', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Dream cycle failed: {e}", exc_info=True)
            self._update_metric('oneiroi', 'online', success=False)
            raise
    
    async def get_dream_insights(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Get recent insights from dream cycles"""
        return await self.dream_engine.get_insights(agent_id, limit)
    
    # ========================================================================
    # GAIA Self-Play
    # ========================================================================
    
    async def run_match(self, request: MatchRequest) -> Dict[str, Any]:
        """
        Run a GAIA competitive match.
        
        Args:
            request: Match configuration
            
        Returns:
            Match results with ELO updates
        """
        try:
            logger.info(f"Starting GAIA match for agent {request.agent_id}")
            self._update_metric('gaia', 'busy')
            
            # Run match
            match_result = await self.match_engine.run_match(
                player1_id=request.agent_id,
                opponent_type=request.opponent_type,
                num_rounds=request.num_rounds
            )
            
            self._update_metric('gaia', 'online', success=True)
            
            return {
                'match_id': match_result['match_id'],
                'agent_id': request.agent_id,
                'opponent_type': request.opponent_type,
                'winner': match_result['winner'],
                'score': match_result['score'],
                'elo_before': match_result['elo_before'],
                'elo_after': match_result['elo_after'],
                'elo_change': match_result['elo_change'],
                'rounds_played': request.num_rounds,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"GAIA match failed: {e}", exc_info=True)
            self._update_metric('gaia', 'online', success=False)
            raise
    
    async def get_agent_elo(self, agent_id: str) -> float:
        """Get current ELO rating for agent"""
        return await self.match_engine.get_elo(agent_id)
    
    async def get_match_history(self, agent_id: str, limit: int = 20) -> List[Dict]:
        """Get recent match history"""
        return await self.match_engine.get_history(agent_id, limit)
    
    # ========================================================================
    # Multi-modal Processing
    # ========================================================================
    
    async def process_image(
        self,
        image_data: bytes,
        operations: List[str]
    ) -> Dict[str, Any]:
        """
        Process image with multiple AI operations.
        
        Args:
            image_data: Raw image bytes
            operations: List of operations ['caption', 'detect', 'ocr', 'segment']
            
        Returns:
            Combined results from all operations
        """
        try:
            logger.info(f"Processing image with operations: {operations}")
            self._update_metric('multimodal', 'busy')
            
            results = {}
            
            if 'caption' in operations:
                results['caption'] = await self.vision_processor.generate_caption(image_data)
            
            if 'detect' in operations:
                results['objects'] = await self.vision_processor.detect_objects(image_data)
            
            if 'ocr' in operations:
                results['text'] = await self.vision_processor.extract_text(image_data)
            
            if 'segment' in operations:
                results['segments'] = await self.vision_processor.segment_image(image_data)
            
            # Generate embedding
            results['embedding'] = await self.vision_processor.get_embedding(image_data)
            
            self._update_metric('multimodal', 'online', success=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}", exc_info=True)
            self._update_metric('multimodal', 'online', success=False)
            raise
    
    async def process_audio(
        self,
        audio_data: bytes,
        operations: List[str]
    ) -> Dict[str, Any]:
        """
        Process audio with multiple AI operations.
        
        Args:
            audio_data: Raw audio bytes
            operations: List of operations ['transcribe', 'diarize', 'classify']
            
        Returns:
            Combined results from all operations
        """
        try:
            logger.info(f"Processing audio with operations: {operations}")
            self._update_metric('multimodal', 'busy')
            
            results = {}
            
            if 'transcribe' in operations:
                results['transcription'] = await self.audio_processor.transcribe(audio_data)
            
            if 'diarize' in operations:
                results['speakers'] = await self.audio_processor.diarize(audio_data)
            
            if 'classify' in operations:
                results['sounds'] = await self.audio_processor.classify_sounds(audio_data)
            
            # Generate embedding
            results['embedding'] = await self.audio_processor.get_embedding(audio_data)
            
            self._update_metric('multimodal', 'online', success=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}", exc_info=True)
            self._update_metric('multimodal', 'online', success=False)
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        modality: str,
        top_k: int = 5
    ) -> List[Dict]:
        """Search for similar content across modalities"""
        if modality == 'image':
            return await self.vision_processor.search_similar(query_embedding, top_k)
        elif modality == 'audio':
            return await self.audio_processor.search_similar(query_embedding, top_k)
        else:
            raise ValueError(f"Unsupported modality: {modality}")
    
    # ========================================================================
    # Meta-Orchestration
    # ========================================================================
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        use_ai_enhancements: bool = True
    ) -> str:
        """
        Process query through meta-orchestrator with optional AI enhancements.
        
        Args:
            query: User query
            user_id: User ID for context
            use_ai_enhancements: Apply Mirror/Contrastive/Causal/GNN enhancements
            
        Returns:
            Final response
        """
        try:
            logger.info(f"Processing query with orchestrator (enhancements={use_ai_enhancements})")
            self._update_metric('orchestrator', 'busy')
            
            response = await self.meta_orchestrator.process_query(
                query=query,
                user_id=user_id
            )
            
            self._update_metric('orchestrator', 'online', success=True)
            
            return response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            self._update_metric('orchestrator', 'online', success=False)
            raise
    
    # ========================================================================
    # Service Management
    # ========================================================================
    
    def get_service_status(self) -> Dict[str, AIServiceStatus]:
        """Get status of all AI services"""
        return self.service_metrics
    
    def _update_metric(
        self,
        service: str,
        status: str,
        success: Optional[bool] = None
    ):
        """Update service metrics"""
        metric = self.service_metrics[service]
        metric.status = status
        metric.last_activity = datetime.now()
        
        if success is not None:
            metric.total_requests += 1
            if success:
                metric.success_rate = (
                    (metric.success_rate * (metric.total_requests - 1) + 1.0)
                    / metric.total_requests
                )
            else:
                metric.success_rate = (
                    (metric.success_rate * (metric.total_requests - 1))
                    / metric.total_requests
                )


# ============================================================================
# Global Instance
# ============================================================================

# Singleton instance
_ai_services_manager: Optional[AdvancedAIServicesManager] = None

def get_ai_services_manager() -> AdvancedAIServicesManager:
    """Get or create global AI services manager"""
    global _ai_services_manager
    
    if _ai_services_manager is None:
        _ai_services_manager = AdvancedAIServicesManager()
    
    return _ai_services_manager
