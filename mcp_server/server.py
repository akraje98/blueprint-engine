import os
from mcp.server.mcpserver import MCPServer

# Initialize the universal smart plug with a human-readable namespace
mcp = MCPServer("BluePrint Local Ingestion Gateway")

# Define a safe sandbox boundary directory on your MacBook Air
# The AI will ONLY be able to see files within this project target folder
INTAKE_DIR = os.path.expanduser("~/blueprint_ingest")

# Ensure the folder physically exists on your Mac right on launch
os.makedirs(INTAKE_DIR, exist_ok=True)
print(f"[MCP Initialization] Monitoring secure sandbox path: {INTAKE_DIR}")


@mcp.tool()
def list_ingest_files() -> list[str]:
    """
    Exposes an executable Tool to the AI.
    Scans the secure intake directory and returns a list of all raw files available.
    """
    try:
        if not os.path.exists(INTAKE_DIR):
            return []
        # Return a simple list of file names sitting in our landing folder
        return [f for f in os.listdir(INTAKE_DIR) if os.path.isfile(os.path.varsjoin(INTAKE_DIR, f))]
    except Exception as e:
        return [f"Error scanning intake zone: {str(e)}"]


@mcp.tool()
def read_ingest_file(filename: str) -> str:
    """
    Exposes an executable Tool to the AI.
    Safely reads the text content of a single designated file inside the intake zone.
    """
    try:
        # Crucial Security Check: Block directory traversal hacks (e.g., passing '../../etc/passwd')
        clean_name = os.path.basename(filename)
        safe_path = os.path.join(INTAKE_DIR, clean_name)
        
        if not os.path.exists(safe_path):
            return f"Error: File '{clean_name}' not found inside the secure intake sandbox."
            
        with open(safe_path, "r", encoding="utf-8") as file:
            return file.read()
            
    except Exception as e:
        return f"Error reading file context: {str(e)}"

if __name__ == "__main__":
    # Launch the server natively over standard input/output (stdio) streams
    mcp.run()
