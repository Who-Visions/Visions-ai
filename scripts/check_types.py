from google.genai import types
print("Checking types.CodeExecution...")
try:
    print(f"CodeExecution: {types.CodeExecution}")
except AttributeError:
    print("❌ types.CodeExecution not found.")

print("\nAvailable attributes in types:")
for d in dir(types):
    if not d.startswith("_"):
        print(d)
