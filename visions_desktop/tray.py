"""
Visions Desktop - System Tray Integration
"""

import pystray
from PIL import Image, ImageDraw
import threading


class VisionsTray:
    """System tray icon and menu for Visions."""
    
    def __init__(self, app):
        self.app = app
        self.icon = None
        self._status = "Ready"
    
    def _create_icon_image(self, color="blue"):
        """Create a simple icon image."""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a circle with V
        colors = {
            "blue": (66, 133, 244),
            "green": (52, 168, 83),
            "red": (234, 67, 53),
            "yellow": (251, 188, 5)
        }
        fill = colors.get(color, colors["blue"])
        
        draw.ellipse([4, 4, size-4, size-4], fill=fill)
        
        # Draw V
        draw.text((size//2 - 8, size//2 - 12), "V", fill="white")
        
        return image
    
    def _create_menu(self):
        """Create the tray menu."""
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: f"Status: {self._status}",
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: "🔇 Unmute" if self.app.muted else "🔊 Mute",
                self._on_toggle_mute
            ),
            pystray.MenuItem(
                "🔄 Restart Listener",
                self._on_restart
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "❌ Exit",
                self._on_exit
            )
        )
    
    def run(self):
        """Run the tray icon (blocking)."""
        self.icon = pystray.Icon(
            "Visions",
            self._create_icon_image(),
            "Visions AI Assistant",
            self._create_menu()
        )
        self.icon.run()
    
    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()
    
    def set_status(self, status: str):
        """Update status text."""
        self._status = status
        if self.icon:
            self.icon.update_menu()
    
    def set_color(self, color: str):
        """Change icon color."""
        if self.icon:
            self.icon.icon = self._create_icon_image(color)
    
    def notify(self, title: str, message: str):
        """Show a notification."""
        if self.icon:
            self.icon.notify(message, title)
    
    def _on_toggle_mute(self, icon, item):
        self.app.toggle_mute()
    
    def _on_restart(self, icon, item):
        self.set_status("Restarting...")
        # TODO: Restart voice listener
        self.set_status("Ready")
    
    def _on_exit(self, icon, item):
        self.app.stop()
