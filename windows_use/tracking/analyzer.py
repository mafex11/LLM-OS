"""
AI-powered activity analyzer.
Analyzes screenshots and calculates productivity metrics.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Screenshot analysis dependencies disabled temporarily
# import base64
# from langchain_core.messages import HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from PIL import Image
# import io

logger = logging.getLogger(__name__)


class ActivityAnalyzer:
    """Analyzes activities and screenshots using AI."""
    
    def __init__(self, llm: Optional[object] = None, google_api_key: Optional[str] = None):
        """
        Initialize activity analyzer.
        
        Args:
            llm: Pre-initialized LLM instance (optional)
            google_api_key: Google API key for Gemini (if llm not provided)
        """
        # Screenshot analysis initialization disabled.
        self.llm = None
        logger.info("Screenshot analysis disabled: skipping LLM initialization.")
        """
        if llm:
            self.llm = llm
        elif google_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    temperature=0.3,
                    google_api_key=google_api_key
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM for analyzer: {e}")
                self.llm = None
        else:
            # Try to get from environment
            import os
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-2.0-flash-exp",
                        temperature=0.3,
                        google_api_key=api_key
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize LLM for analyzer: {e}")
                    self.llm = None
            else:
                self.llm = None
                logger.warning("No LLM provided for activity analyzer. Screenshot analysis will be disabled.")
        """
    
    def analyze_screenshot(self, screenshot_path: Path, app_name: str = None, window_title: str = None) -> Dict:
        """
        Analyze a screenshot using AI vision.
        
        Args:
            screenshot_path: Path to screenshot image
            app_name: Current app name (optional)
            window_title: Window title (optional)
        
        Returns:
            Dict with analysis results including category, focus_score, and description
        """
        logger.info("Screenshot analysis temporarily disabled. Returning default payload.")
        return {
            "ai_analysis": "Screenshot analysis disabled",
            "activity_category": "unknown",
            "focus_score": 50,
            "description": "No analysis generated while feature is disabled."
        }

        """
        Legacy implementation preserved for quick restoration.
        if not self.llm:
            logger.warning("LLM not available for screenshot analysis")
            return {
                "ai_analysis": "Analysis unavailable - LLM not configured",
                "activity_category": "unknown",
                "focus_score": 50
            }
        
        try:
            # Load and encode image
            with open(screenshot_path, 'rb') as f:
                image_data = f.read()
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            image_uri = f"data:image/png;base64,{image_base64}"
            
            # Create analysis prompt
            context = ""
            if app_name:
                context += f"Current application: {app_name}\n"
            if window_title:
                context += f"Window title: {window_title}\n"
            
            prompt = f"""Analyze this screenshot and describe what the user is doing. 
            
Context:
{context}

Provide a detailed analysis including:
1. What activity the user is engaged in (work, research, entertainment, communication, etc.)
2. The category of activity (work, research, entertainment, browsing, communication, other)
3. A focus score from 0-100 (100 = highly focused productive work, 0 = distracted/entertainment)
4. A brief description of what you see

Format your response as JSON:
{{
    "activity_category": "work|research|entertainment|browsing|communication|other",
    "focus_score": 85,
    "description": "User is working in a code editor, viewing Python code with syntax highlighting. Appears focused on programming task."
}}"""

            # Analyze with vision model
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_uri}}
            ])
            
            response = self.llm.invoke([message])
            analysis_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group(0))
            else:
                # Fallback: try to extract information from text
                analysis_data = self._parse_analysis_text(analysis_text)
            
            return {
                "ai_analysis": analysis_text,
                "activity_category": analysis_data.get("activity_category", "unknown"),
                "focus_score": analysis_data.get("focus_score", 50),
                "description": analysis_data.get("description", analysis_text)
            }
        
        except Exception as e:
            logger.error(f"Error analyzing screenshot: {e}")
            return {
                "ai_analysis": f"Analysis error: {str(e)}",
                "activity_category": "unknown",
                "focus_score": 50
            }
        """
    
    def _parse_analysis_text(self, text: str) -> Dict:
        """Parse analysis text when JSON parsing fails."""
        text_lower = text.lower()
        
        # Determine category
        category = "other"
        if any(word in text_lower for word in ["work", "code", "programming", "editing", "writing"]):
            category = "work"
        elif any(word in text_lower for word in ["research", "reading", "documentation", "learning"]):
            category = "research"
        elif any(word in text_lower for word in ["entertainment", "video", "game", "social media"]):
            category = "entertainment"
        elif any(word in text_lower for word in ["browsing", "web", "internet"]):
            category = "browsing"
        elif any(word in text_lower for word in ["email", "message", "chat", "communication"]):
            category = "communication"
        
        # Estimate focus score
        focus_score = 50
        if category == "work":
            focus_score = 85
        elif category == "research":
            focus_score = 75
        elif category == "entertainment":
            focus_score = 20
        elif category == "browsing":
            focus_score = 40
        elif category == "communication":
            focus_score = 60
        
        return {
            "activity_category": category,
            "focus_score": focus_score,
            "description": text[:200]  # First 200 chars
        }
    
    def calculate_daily_summary(self, activities: Dict, screenshots: List[Dict] = None) -> Dict:
        """
        Calculate daily summary from activities.
        Focus time is calculated as time spent on the most used app (main focus).
        Tab tracking is disabled - only app-level activities are tracked.
        
        Args:
            activities: Daily activities dict from storage
            screenshots: List of screenshot metadata (optional)
        
        Returns:
            Daily summary dict with metrics and insights
        """
        app_activities = activities.get("app_activities", [])
        # DISABLED: Tab activities are no longer tracked
        # tab_activities = activities.get("tab_activities", [])
        
        total_active_time = 0
        
        # Track app usage - simple aggregation by app name
        app_usage_stats = {}
        
        # Process app activities only
        for activity in app_activities:
            duration = activity.get("duration_seconds", 0)
            app_name = activity.get("app_name", "unknown")
            
            total_active_time += duration
            
            # Track app usage
            if app_name not in app_usage_stats:
                app_usage_stats[app_name] = 0
            app_usage_stats[app_name] += duration
        
        # Get top apps
        top_apps = sorted(
            [(app, time) for app, time in app_usage_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        top_apps = [{"app": app, "time": time} for app, time in top_apps]
        
        # Calculate focus time as time spent on most used app
        focus_time = top_apps[0]["time"] if top_apps else 0
        
        date = activities.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        return {
            "date": date,
            "total_focus_time": focus_time,
            "work_time": 0,  # Keep for compatibility but not used
            "research_time": 0,  # Keep for compatibility but not used
            "entertainment_time": 0,  # Keep for compatibility but not used
            "distraction_time": 0,  # Keep for compatibility but not used
            "focus_score": 0,  # Keep for compatibility but not used
            "app_usage_stats": app_usage_stats,
            "top_apps": top_apps,
            "insights": f"You spent {focus_time / 3600:.1f} hours focused on {top_apps[0]['app'] if top_apps else 'your activities'} today." if top_apps else "No activities tracked today.",
            "screenshot_count": len(screenshots) if screenshots else 0,
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_insights(self, work_time: int, research_time: int, entertainment_time: int,
                          total_time: int, focus_score: int, top_apps: List[Dict]) -> str:
        """Generate human-readable insights from metrics."""
        hours_worked = work_time / 3600
        hours_research = research_time / 3600
        hours_entertainment = entertainment_time / 3600
        hours_total = total_time / 3600
        
        insights_parts = []
        
        # Overall assessment
        if focus_score >= 80:
            insights_parts.append(f"You maintained excellent focus today with a {focus_score}% focus score.")
        elif focus_score >= 60:
            insights_parts.append(f"You had good focus today with a {focus_score}% focus score.")
        elif focus_score >= 40:
            insights_parts.append(f"Your focus was moderate today ({focus_score}%) with room for improvement.")
        else:
            insights_parts.append(f"Your focus was low today ({focus_score}%). Consider minimizing distractions.")
        
        # Time breakdown
        if hours_worked > 0:
            insights_parts.append(f"You spent {hours_worked:.1f} hours on work tasks.")
        if hours_research > 0:
            insights_parts.append(f"You spent {hours_research:.1f} hours on research and learning.")
        if hours_entertainment > 0:
            insights_parts.append(f"You spent {hours_entertainment:.1f} hours on entertainment.")
        
        # Top apps
        if top_apps:
            top_app = top_apps[0]
            top_hours = top_app["time"] / 3600
            insights_parts.append(f"Your most used app was {top_app['app']} ({top_hours:.1f} hours).")
        
        return " ".join(insights_parts)

