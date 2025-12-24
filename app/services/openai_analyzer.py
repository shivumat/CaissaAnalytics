import asyncio
import logging
from typing import List, Dict
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIAnalyzer:
    """Service for analyzing mistakes with OpenAI"""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.batch_size = settings.openai_batch_size
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    async def analyze_mistake(self, mistake: dict) -> str:
        """
        Analyze a single mistake using OpenAI.
        
        Args:
            mistake: Dictionary containing mistake information
            
        Returns:
            AI analysis of the mistake
        """
        if not self.client:
            return "OpenAI API key not configured"
        
        try:
            prompt = f"""Analyze this chess mistake:

Move: {mistake['move_san']} (move {mistake['move_number']})
Position (FEN): {mistake['fen_before']}
Evaluation before: {mistake['eval_before']/100:.2f} pawns
Evaluation after: {mistake['eval_after']/100:.2f} pawns
Evaluation drop: {mistake['eval_drop']/100:.2f} pawns

Provide a brief tactical/strategic explanation of why this move was a mistake. Keep it concise (2-3 sentences)."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a chess expert analyzing mistakes in chess games. Provide clear, concise explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing mistake with OpenAI: {e}")
            return f"Error: {str(e)}"
    
    async def analyze_mistakes_batch(self, mistakes: List[dict]) -> List[str]:
        """
        Analyze multiple mistakes in batches asynchronously.
        
        Args:
            mistakes: List of mistake dictionaries
            
        Returns:
            List of AI analyses corresponding to each mistake
        """
        if not mistakes:
            return []
        
        if not self.client:
            return ["OpenAI API key not configured"] * len(mistakes)
        
        # Process in batches to avoid rate limits
        results = []
        
        for i in range(0, len(mistakes), self.batch_size):
            batch = mistakes[i:i + self.batch_size]
            
            # Analyze batch concurrently
            tasks = [self.analyze_mistake(mistake) for mistake in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append(f"Error: {str(result)}")
                else:
                    results.append(result)
        
        return results
