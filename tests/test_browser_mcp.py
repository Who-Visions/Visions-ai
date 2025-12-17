import unittest
import sys
import os

# Add parent directory to path to import tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.browser_tool import BrowserTool

class TestBrowserTool(unittest.TestCase):
    def setUp(self):
        print("\nSETUP: Initializing Browser Tool...")
        self.browser = BrowserTool()

    def tearDown(self):
        print("\nTEARDOWN: Closing Browser Tool...")
        if self.browser.client:
            self.browser.client.close()

        
    def test_list_tools(self):
        print("\nTEST: Listing tools...")
        tools = self.browser.list_tools()
        print(f"Tools found: {len(tools)}")
        print(f"Tool names: {[t['name'] for t in tools]}")
        self.assertTrue(len(tools) > 0)


if __name__ == '__main__':
    unittest.main()
