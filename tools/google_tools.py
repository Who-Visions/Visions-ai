"""
Google Tasks & Calendar Voice Control for Visions
Requires OAuth2 credentials from Google Cloud Console.

Setup:
1. Go to console.cloud.google.com → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Desktop App)
3. Download JSON → save as 'credentials.json' in project root
4. Run this script once to authorize
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Install: pip install google-auth-oauthlib google-api-python-client")

# Scopes for Tasks and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'


def get_credentials():
    """Get or refresh OAuth2 credentials."""
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds


class GoogleTasksClient:
    """Google Tasks API wrapper."""
    
    def __init__(self):
        creds = get_credentials()
        if creds:
            self.service = build('tasks', 'v1', credentials=creds)
        else:
            self.service = None
    
    def add_task(self, title: str, notes: str = None, due_date: str = None) -> str:
        """Add a task to the default task list."""
        if not self.service:
            return "Google Tasks not authorized. Run 'python tools/google_tools.py' to set up."
        
        try:
            # Get default task list
            tasklists = self.service.tasklists().list().execute()
            default_list = tasklists['items'][0]['id']
            
            task = {'title': title}
            if notes:
                task['notes'] = notes
            if due_date:
                # Convert to RFC 3339 format
                task['due'] = due_date + 'T00:00:00.000Z'
            
            result = self.service.tasks().insert(tasklist=default_list, body=task).execute()
            return f"Task added: {title}"
        except Exception as e:
            return f"Failed to add task: {str(e)}"
    
    def list_tasks(self, max_results: int = 10) -> str:
        """List upcoming tasks."""
        if not self.service:
            return "Google Tasks not authorized."
        
        try:
            tasklists = self.service.tasklists().list().execute()
            default_list = tasklists['items'][0]['id']
            
            results = self.service.tasks().list(
                tasklist=default_list,
                maxResults=max_results,
                showCompleted=False
            ).execute()
            
            tasks = results.get('items', [])
            if not tasks:
                return "No pending tasks."
            
            task_list = []
            for task in tasks:
                due = task.get('due', '')[:10] if task.get('due') else 'No date'
                task_list.append(f"• {task['title']} ({due})")
            
            return "Your tasks:\n" + "\n".join(task_list)
        except Exception as e:
            return f"Failed to list tasks: {str(e)}"
    
    def complete_task(self, title: str) -> str:
        """Mark a task as completed."""
        if not self.service:
            return "Google Tasks not authorized."
        
        try:
            tasklists = self.service.tasklists().list().execute()
            default_list = tasklists['items'][0]['id']
            
            # Find the task
            results = self.service.tasks().list(tasklist=default_list).execute()
            for task in results.get('items', []):
                if title.lower() in task['title'].lower():
                    task['status'] = 'completed'
                    self.service.tasks().update(
                        tasklist=default_list,
                        task=task['id'],
                        body=task
                    ).execute()
                    return f"Completed: {task['title']}"
            
            return f"Task not found: {title}"
        except Exception as e:
            return f"Failed to complete task: {str(e)}"


class GoogleCalendarClient:
    """Google Calendar API wrapper."""
    
    def __init__(self):
        creds = get_credentials()
        if creds:
            self.service = build('calendar', 'v3', credentials=creds)
        else:
            self.service = None
    
    def get_events_today(self) -> str:
        """Get today's calendar events."""
        if not self.service:
            return "Google Calendar not authorized."
        
        try:
            now = datetime.utcnow()
            start = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            end = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return "No events scheduled for today."
            
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                time_str = start[11:16] if 'T' in start else 'All day'
                event_list.append(f"• {time_str}: {event['summary']}")
            
            return "Today's schedule:\n" + "\n".join(event_list)
        except Exception as e:
            return f"Failed to get events: {str(e)}"
    
    def get_events_tomorrow(self) -> str:
        """Get tomorrow's calendar events."""
        if not self.service:
            return "Google Calendar not authorized."
        
        try:
            tomorrow = datetime.utcnow() + timedelta(days=1)
            start = tomorrow.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            end = tomorrow.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return "No events scheduled for tomorrow."
            
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                time_str = start[11:16] if 'T' in start else 'All day'
                event_list.append(f"• {time_str}: {event['summary']}")
            
            return "Tomorrow's schedule:\n" + "\n".join(event_list)
        except Exception as e:
            return f"Failed to get events: {str(e)}"
    
    def create_event(self, title: str, date: str, time: str = None, duration_hours: int = 1) -> str:
        """Create a calendar event."""
        if not self.service:
            return "Google Calendar not authorized."
        
        try:
            if time:
                start_dt = f"{date}T{time}:00"
                end_dt = datetime.fromisoformat(start_dt) + timedelta(hours=duration_hours)
                event = {
                    'summary': title,
                    'start': {'dateTime': start_dt, 'timeZone': 'America/New_York'},
                    'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/New_York'},
                }
            else:
                event = {
                    'summary': title,
                    'start': {'date': date},
                    'end': {'date': date},
                }
            
            result = self.service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created: {title}"
        except Exception as e:
            return f"Failed to create event: {str(e)}"


# Voice command function
def google_command(action: str, title: str = None, date: str = None, time: str = None) -> str:
    """
    Execute Google Tasks/Calendar commands via voice.
    
    Args:
        action: add_task, list_tasks, complete_task, today, tomorrow, create_event
        title: Task or event title
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24hr)
    """
    action = action.lower()
    
    if action in ['add_task', 'add task', 'new task']:
        client = GoogleTasksClient()
        return client.add_task(title or "Untitled task", due_date=date)
    
    elif action in ['list_tasks', 'list tasks', 'my tasks', 'tasks']:
        client = GoogleTasksClient()
        return client.list_tasks()
    
    elif action in ['complete_task', 'complete task', 'done']:
        client = GoogleTasksClient()
        return client.complete_task(title or "")
    
    elif action in ['today', 'schedule today', 'calendar today']:
        client = GoogleCalendarClient()
        return client.get_events_today()
    
    elif action in ['tomorrow', 'schedule tomorrow', 'calendar tomorrow']:
        client = GoogleCalendarClient()
        return client.get_events_tomorrow()
    
    elif action in ['create_event', 'create event', 'new event', 'schedule']:
        client = GoogleCalendarClient()
        return client.create_event(title or "Untitled event", date or datetime.now().strftime('%Y-%m-%d'), time)
    
    else:
        return f"Unknown Google action: {action}"


# Function declaration for Gemini
GOOGLE_FUNCTION_DECLARATION = {
    "name": "google_command",
    "description": "Control Google Tasks and Calendar. Add tasks, list tasks, check schedule, create events.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add_task", "list_tasks", "complete_task", "today", "tomorrow", "create_event"],
                "description": "Action: add_task, list_tasks, complete_task, today (calendar), tomorrow (calendar), create_event"
            },
            "title": {
                "type": "string",
                "description": "Task or event title"
            },
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format"
            },
            "time": {
                "type": "string",
                "description": "Time in HH:MM format (24hr)"
            }
        },
        "required": ["action"]
    }
}


if __name__ == "__main__":
    print("🔐 Google OAuth2 Setup")
    print("=" * 40)
    
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Missing {CREDENTIALS_PATH}")
        print("\nTo set up:")
        print("1. Go to console.cloud.google.com")
        print("2. APIs & Services → Credentials")
        print("3. Create OAuth 2.0 Client ID (Desktop App)")
        print("4. Download JSON → save as 'credentials.json'")
    else:
        print("✅ credentials.json found")
        print("🔄 Authorizing...")
        creds = get_credentials()
        if creds:
            print("✅ Authorization successful!")
            print("\nTesting Tasks API...")
            tasks = GoogleTasksClient()
            print(tasks.list_tasks())
            print("\nTesting Calendar API...")
            cal = GoogleCalendarClient()
            print(cal.get_events_today())
        else:
            print("❌ Authorization failed")
