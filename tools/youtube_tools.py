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

    def analyze_video(self, video_url: str, question: str = "Summarize this video") -> str:
        """
        Analyzes a YouTube video using Gemini 2.5 Flash native support.
        """
        if "youtube.com" not in video_url and "youtu.be" not in video_url:
            return "Error: Invalid YouTube URL provided."
            
        try:
            model_id = "gemini-2.5-flash"
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
            
            response = self.client.models.generate_content(
                model=model_id,
                contents=[video_part, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2048
                )
            )
            
            if response.text:
                return f"🎬 **Video Analysis**\nURL: {video_url}\n\n{response.text}"
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
                
                1. Extract detailed steps & tools.
                2. Note parameters/code.
                3. Include timestamps.
                
                Format as a clear, numbered Markdown workflow.
                """
            
            response = self.global_client.models.generate_content(
                model=model_id,
                contents=[video_part, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="high"
                    )
                )
            )
            
            if response.text:
                return f"🎓 **Workflow Extraction** (Gemini 3 Pro)\nURL: {video_url}\n\n{response.text}"
            else:
                return "No workflow extracted from video."
                 
        except Exception as e:
            return f"Error extracting workflow: {str(e)}"
