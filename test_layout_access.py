from rich.layout import Layout
from rich import print
from rich.panel import Panel

def test_layout():
    root = Layout()
    root.split_column(
        Layout(name="child1"),
        Layout(name="child2")
    )
    
    # Try accessing by name
    try:
        print(f"Accessing child1: {root['child1']}")
        root["child1"].update(Panel("Hello"))
        print("Update success.")
    except Exception as e:
        print(f"Error accessing by name: {e}")

    # Try deep access
    root["child2"].split_row(Layout(name="grandchild"))
    try:
        print(f"Accessing grandchild: {root['grandchild']}")
    except Exception as e:
        print(f"Error accessing grandchild: {e}")

if __name__ == "__main__":
    test_layout()
