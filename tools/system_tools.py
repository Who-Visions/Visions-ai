"""
System Voice Control Tools for Visions
Control Windows system features via voice commands.
"""

import subprocess
import os
from datetime import datetime
from typing import Optional


def system_command(action: str, value: Optional[int] = None) -> str:
    """
    Execute system commands via voice.
    
    Args:
        action: The system action to perform
        value: Optional value (e.g., volume level 0-100)
    
    Returns:
        Status message
    """
    action = action.lower()
    
    # Volume Control (Windows)
    if action == "mute":
        # Use nircmd or PowerShell to mute
        try:
            subprocess.run([
                "powershell", "-Command",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
            ], capture_output=True)
            return "System muted."
        except:
            return "Failed to mute."
    
    elif action == "unmute":
        try:
            subprocess.run([
                "powershell", "-Command",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
            ], capture_output=True)
            return "System unmuted."
        except:
            return "Failed to unmute."
    
    elif action == "volume_up":
        try:
            subprocess.run([
                "powershell", "-Command",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"
            ], capture_output=True)
            return "Volume increased."
        except:
            return "Failed to change volume."
    
    elif action == "volume_down":
        try:
            subprocess.run([
                "powershell", "-Command",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
            ], capture_output=True)
            return "Volume decreased."
        except:
            return "Failed to change volume."
    
    elif action == "volume" and value is not None:
        # Set specific volume level (requires nircmd or similar)
        level = max(0, min(100, value))
        try:
            # Use PowerShell to set volume
            subprocess.run([
                "powershell", "-Command",
                f"Set-AudioDevice -PlaybackVolume {level}"
            ], capture_output=True)
            return f"Volume set to {level}%."
        except:
            return f"Volume control requires AudioDeviceCmdlets module."
    
    # Screenshot
    elif action == "screenshot":
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.expanduser(f"~/Pictures/Screenshots/visions_screenshot_{timestamp}.png")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Use PowerShell to take screenshot
            subprocess.run([
                "powershell", "-Command",
                f"""
                Add-Type -AssemblyName System.Windows.Forms
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen
                $bitmap = New-Object System.Drawing.Bitmap($screen.Bounds.Width, $screen.Bounds.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size)
                $bitmap.Save('{save_path}')
                """
            ], capture_output=True)
            return f"Screenshot saved to {save_path}"
        except Exception as e:
            return f"Screenshot failed: {str(e)}"
    
    # Lock Screen
    elif action == "lock":
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], capture_output=True)
            return "Computer locked."
        except:
            return "Failed to lock computer."
    
    # Sleep/Hibernate
    elif action == "sleep":
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], capture_output=True)
            return "Going to sleep..."
        except:
            return "Failed to sleep."
    
    # Open Apps
    elif action == "open_browser":
        try:
            subprocess.Popen(["start", "chrome"], shell=True)
            return "Opening Chrome."
        except:
            return "Failed to open browser."
    
    elif action == "open_explorer":
        try:
            subprocess.Popen(["explorer"], shell=True)
            return "Opening File Explorer."
        except:
            return "Failed to open explorer."
    
    elif action == "open_terminal":
        try:
            subprocess.Popen(["wt"], shell=True)
            return "Opening Windows Terminal."
        except:
            return "Failed to open terminal."
    
    # Time
    elif action == "time":
        now = datetime.now()
        return f"The time is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d')}."
    
    else:
        return f"Unknown system command: {action}"


# Function declaration for Gemini/Voice
SYSTEM_FUNCTION_DECLARATION = {
    "name": "system_command",
    "description": "Control Windows system features. Volume, screenshots, lock screen, open apps. Say 'mute', 'screenshot', 'lock my computer', 'open terminal', 'what time is it'.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["mute", "unmute", "volume_up", "volume_down", "volume", 
                         "screenshot", "lock", "sleep",
                         "open_browser", "open_explorer", "open_terminal", "time"],
                "description": "System action: mute, unmute, volume_up, volume_down, volume (set level), screenshot, lock, sleep, open_browser, open_explorer, open_terminal, time"
            },
            "value": {
                "type": "integer",
                "description": "Value for volume (0-100)"
            }
        },
        "required": ["action"]
    }
}


if __name__ == "__main__":
    # Test
    print(system_command("time"))
    print(system_command("screenshot"))
