"""
Streaming Analyzer for Real-time Data Processing

Provides real-time analysis capabilities for streaming data
including live sentiment analysis, topic detection, and pattern recognition.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from collections import deque
import json

logger = logging.getLogger(__name__)

class StreamingAnalyzer:
    """
    Real-time streaming data analyzer.
    
    Analyzes data streams in real-time with configurable windows
    and provides live insights and alerts.
    """
    
    def __init__(self, window_size: int = 100, analysis_interval: float = 1.0):
        """
        Initialize streaming analyzer.
        
        Args:
            window_size: Size of the analysis window
            analysis_interval: Interval between analyses in seconds
        """
        self.window_size = window_size
        self.analysis_interval = analysis_interval
        
        # Data buffers
        self.data_buffer = deque(maxlen=window_size)
        self.analysis_buffer = deque(maxlen=50)
        
        # Analysis state
        self.running = False
        self.analysis_task = None
        
        # Metrics
        self.total_processed = 0
        self.start_time = None
        
        logger.info(f"Streaming analyzer initialized with window size {window_size}")
    
    async def start(self):
        """Start the streaming analyzer"""
        self.running = True
        self.start_time = datetime.utcnow()
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        logger.info("Streaming analyzer started")
    
    async def stop(self):
        """Stop the streaming analyzer"""
        self.running = False
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        logger.info("Streaming analyzer stopped")
    
    async def add_data(self, data: Dict[str, Any]):
        """
        Add data to the stream for analysis.
        
        Args:
            data: Data to analyze
        """
        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
        
        # Add to buffer
        self.data_buffer.append(data)
        self.total_processed += 1
        
        logger.debug(f"Added data to stream: {len(self.data_buffer)} items in buffer")
    
    async def _analysis_loop(self):
        """Main analysis loop"""
        while self.running:
            try:
                if len(self.data_buffer) > 0:
                    analysis_result = await self._analyze_current_window()
                    if analysis_result:
                        self.analysis_buffer.append(analysis_result)
                
                await asyncio.sleep(self.analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(1)
    
    async def _analyze_current_window(self) -> Optional[Dict[str, Any]]:
        """Analyze current window of data"""
        if not self.data_buffer:
            return None
        
        try:
            # Convert buffer to list for analysis
            window_data = list(self.data_buffer)
            
            # Perform analysis
            analysis = {
                "timestamp": datetime.utcnow().isoformat(),
                "window_size": len(window_data),
                "sentiment_analysis": await self._analyze_sentiment(window_data),
                "topic_analysis": await self._analyze_topics(window_data),
                "pattern_analysis": await self._analyze_patterns(window_data),
                "statistics": await self._calculate_statistics(window_data)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing window: {e}")
            return None
    
    async def _analyze_sentiment(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment in the data window"""
        sentiments = []
        
        for item in data:
            # Extract text for sentiment analysis
            text = ""
            if "text" in item:
                text = item["text"]
            elif "message" in item:
                text = item["message"]
            elif "content" in item:
                text = item["content"]
            
            if text:
                # Simple sentiment analysis (would use real NLP in production)
                sentiment = self._simple_sentiment(text)
                sentiments.append(sentiment)
        
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            return {
                "average_sentiment": avg_sentiment,
                "sentiment_trend": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral",
                "sample_count": len(sentiments)
            }
        
        return {"average_sentiment": 0.0, "sentiment_trend": "neutral", "sample_count": 0}
    
    def _simple_sentiment(self, text: str) -> float:
        """Simple sentiment analysis"""
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "happy", "love", "like"]
        negative_words = ["bad", "terrible", "awful", "hate", "sad", "angry", "frustrated", "disappointed"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    async def _analyze_topics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze topics in the data window"""
        all_words = []
        
        for item in data:
            # Extract text for topic analysis
            text = ""
            if "text" in item:
                text = item["text"]
            elif "message" in item:
                text = item["message"]
            elif "content" in item:
                text = item["content"]
            
            if text:
                # Simple word extraction
                words = [word.lower().strip() for word in text.split() if len(word) > 3]
                all_words.extend(words)
        
        # Count word frequencies
        word_counts = {}
        for word in all_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top topics
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        top_topics = [word for word, count in sorted_words[:5]]
        
        return {
            "top_topics": top_topics,
            "topic_diversity": len(word_counts),
            "total_words": len(all_words)
        }
    
    async def _analyze_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in the data window"""
        patterns = {
            "activity_pattern": "steady",
            "time_distribution": {},
            "data_types": {},
            "anomalies": []
        }
        
        # Analyze data types
        for item in data:
            data_type = item.get("type", "unknown")
            patterns["data_types"][data_type] = patterns["data_types"].get(data_type, 0) + 1
        
        # Analyze time distribution
        hour_counts = {}
        for item in data:
            timestamp = item.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                except:
                    pass
        
        patterns["time_distribution"] = hour_counts
        
        # Simple anomaly detection (unusual volume)
        if len(data) > self.window_size * 0.8:
            patterns["anomalies"].append("high_volume")
        elif len(data) < self.window_size * 0.2:
            patterns["anomalies"].append("low_volume")
        
        return patterns
    
    async def _calculate_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for the data window"""
        return {
            "window_size": len(data),
            "processing_rate": self.total_processed / max((datetime.utcnow() - self.start_time).total_seconds(), 1) if self.start_time else 0,
            "buffer_utilization": len(self.data_buffer) / self.window_size,
            "total_processed": self.total_processed
        }
    
    async def get_live_insights(self) -> Dict[str, Any]:
        """Get current live insights"""
        if not self.analysis_buffer:
            return {"message": "No analysis data available yet"}
        
        latest_analysis = self.analysis_buffer[-1]
        
        # Generate insights based on latest analysis
        insights = {
            "current_sentiment": latest_analysis.get("sentiment_analysis", {}).get("sentiment_trend", "neutral"),
            "trending_topics": latest_analysis.get("topic_analysis", {}).get("top_topics", []),
            "activity_level": "high" if latest_analysis.get("statistics", {}).get("window_size", 0) > self.window_size * 0.7 else "normal",
            "anomalies": latest_analysis.get("pattern_analysis", {}).get("anomalies", []),
            "timestamp": latest_analysis.get("timestamp", "")
        }
        
        return insights
    
    async def get_analysis_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get analysis history"""
        return list(self.analysis_buffer)[-limit:]
    
    async def stream_insights(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream live insights as they become available"""
        last_analysis_count = 0
        
        while self.running:
            current_count = len(self.analysis_buffer)
            
            if current_count > last_analysis_count:
                # New analysis available
                insights = await self.get_live_insights()
                yield insights
                last_analysis_count = current_count
            
            await asyncio.sleep(0.5)
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            "running": self.running,
            "window_size": self.window_size,
            "analysis_interval": self.analysis_interval,
            "buffer_size": len(self.data_buffer),
            "analysis_count": len(self.analysis_buffer),
            "total_processed": self.total_processed,
            "uptime": (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        }
