"""
YouTube Tools - Agent-facing tools for YouTube video analysis using Gemini.
"""
import os
import json
import re
import urllib.request
import urllib.parse
from google import genai
from google.genai import types


class YouTubeTools:
    """
    Tools for searching and analyzing YouTube videos using Gemini.
    """
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self._client = None
        self._global_client = None  # For gemini-3-pro-preview (global only)

    @property
    def client(self):
        """Regional client for Gemini 2.5 Flash."""
        if self._client is None:
            print("Initializing GenAI Client for YouTube Tools...")
            self._client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
        return self._client
    
    @property
    def global_client(self):
        """Global client for Gemini 3 Pro (requires global routing)."""
        if self._global_client is None:
            print("Initializing Global GenAI Client for Gemini 3 Pro...")
            self._global_client = genai.Client(vertexai=True, project=self.project_id, location="global")
        return self._global_client

    def search_videos(self, query: str) -> str:
        """
        Searches for YouTube videos matching the query.
        Returns a formatted string of video URLs.
        """
        print(f"🔍 Searching YouTube for: {query}")
        try:
            query_encoded = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={query_encoded}"
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
            
            seen = set()
            unique_ids = [x for x in video_ids if not (x in seen or seen.add(x))]
            
            results = [f"https://www.youtube.com/watch?v={vid}" for vid in unique_ids[:5]]
                
            if not results:
                return "No videos found."
                
            return f"Found relevant videos:\n" + "\n".join([f"• {r}" for r in results])
            
        except Exception as e:
            return f"Error searching YouTube: {e}"

    def _generate_with_retry(self, func, *args, **kwargs):
        """Helper to retry API calls with exponential backoff."""
        retries = 8
        base_delay = 4
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                is_rate_limit = "429" in str(e) or "ResourceExhausted" in str(e) or "Quota" in str(e) or "TooManyRequests" in str(e)
                if is_rate_limit:
                    if i == retries - 1:
                        print(f"   ❌ Rate limit exhausted after {retries} retries.")
                        raise e
                    import time, random
                    sleep_time = base_delay * (2 ** i) + (random.random() * 1.0)
                    print(f"   ⏳ Rate limit hit (Attempt {i+1}/{retries}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    raise e

    def analyze_video(self, video_url: str, question: str = "Summarize this video") -> str:
        """
        Analyzes a YouTube video using Gemini 2.5 Pro (Fallback).
        """
        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            return "Error: Invalid YouTube URL provided."
            
        try:
            # User requested 2.5 Pro for fallback
            model_id = "gemini-2.5-pro"
            print(f"   Analyzing video: {video_url} with {model_id}...")
            
            video_part = types.Part.from_uri(
                file_uri=video_url,
                mime_type="video/mp4"
            )
            
            prompt = f"""
            Analyze this YouTube video.
            User Question: {question}
            
            Provide a detailed breakdown of key points, timestamps if possible, and actionable insights.
            """
            
            # Use regional client for 2.5 Pro (us-central1)
            response = self._generate_with_retry(
                self.client.models.generate_content,
                model=model_id,
                contents=[video_part, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096  # Increased for Pro
                )
            )
            
            if response.text:
                return f"🎬 **Video Analysis** ({model_id})\nURL: {video_url}\n\n{response.text}"
            else:
                return "No text response generated from video analysis."
                 
        except Exception as e:
            return f"Error analyzing video: {str(e)}"
    
    def extract_workflow(self, video_url: str, output_format: str = "markdown") -> str:
        """
        Uses Gemini 3 Pro with deep thinking to extract workflows or visual summaries.
        Args:
            video_url: URL
            output_format: "markdown" (default) or "mermaid" (for visual flowchart)
        """
        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            return "Error: Invalid YouTube URL provided."
            
        try:
            model_id = "gemini-3-pro-preview"
            print(f"   🧠 Deep analysis with {model_id} (Thinking: HIGH)...")
            
            video_part = types.Part.from_uri(
                file_uri=video_url,
                mime_type="video/mp4"
            )
            
            # Dynamic Prompt based on output format
            if output_format == "mermaid":
                prompt = """
                Analyze this video to create a visual flowchart of the process shown.
                
                OUTPUT FORMAT: **Mermaid JS** code block (`graph TD`).
                - Use structured nodes (Stage 1 --> Stage 2).
                - Use subgraphs for key sections.
                - Keep node text concise.
                
                Return ONLY the mermaid code block.
                """
            else:
                prompt = """
                You are an expert at analyzing tutorial videos and extracting actionable workflows.
                
                Analyze this video and return a **valid JSON object** with the following structure:
                {
                    "title": "Video Title",
                    "summary": "Brief summary",
                    "steps": [
                        {
                            "time": "MM:SS",
                            "action": "Step description",
                            "code": "Optional code snippet",
                            "tool": "Tool used"
                        }
                    ],
                    "key_takeaways": ["Point 1", "Point 2"]
                }
                
                Do not wrap in markdown code blocks. Return RAW JSON only.
                """
            
            response = self._generate_with_retry(
                self.global_client.models.generate_content,
                model=model_id,
                contents=[video_part, prompt],
                # Force JSON response mime type if possible, but raw text parsing is fine for now
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                    response_mime_type="application/json", # Force JSON
                    thinking_config=types.ThinkingConfig(
                        thinking_level="high"
                    )
                )
            )
            
            if response.text:
                return response.text # Return raw JSON string
            else:
                return '{"error": "No workflow extracted"}'
                 
        except Exception as e:
            return f"Error extracting workflow: {str(e)}"
