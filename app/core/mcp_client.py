import os
import sys
from contextlib import AsyncExitStack
# NEW V2 IMPORT: Bring in the strict Stdio Server parameter configuration mapping object
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """Manages the background process lifecycle and connection to the local MCP server plug."""
    
    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect(self) -> None:
        """Spawns the local MCP server as an isolated subprocess and binds standard I/O streams."""
        if not self.session:
            try:
                # Target the exact virtual environment python path of your project
                venv_python = sys.executable
                server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../mcp_server/server.py"))
                
                print(f"[MCP Client] Spawning standalone plug process via: {venv_python} {server_script}")
                
                # FIX: Wrap the parameter settings inside the mandatory StdioServerParameters object class wrapper!
                server_params = StdioServerParameters(
                    command=venv_python,
                    args=[server_script],
                    env=os.environ.copy()
                )
                
                # Open the process communication tunnel using the AsyncExitStack context context context context
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                
                # Bind the client protocol session wrapper over the open streams
                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                
                # Execute the modern v2 handshake protocol connection probe
                await self.session.initialize()
                print("🔌 [MCP Client] Successfully connected to BluePrint Local Ingestion Gateway!")
                
                # Log available tools to confirm dynamic capability broadcast works
                tools_result = await self.session.list_tools()
                print(f"[MCP Client] Dynamically discovered tools: {[t.name for t in tools_result.tools]}")
                
            except Exception as e:
                print(f"❌ [MCP Client Error] Failed to bind local server plug process: {e}")
                await self.close()
                raise e

    async def close(self) -> None:
        """Tears down the background process stack cleanly on application termination."""
        if self.exit_stack:
            print("[MCP Client] Terminating background plug subprocess channels...")
            await self.exit_stack.aclose()
            print("[MCP Client] Process channels torn down cleanly.")
            self.session = None

    def get_session(self) -> ClientSession:
        """Retrieves the active process session client."""
        if not self.session:
            raise RuntimeError("MCP Session is not active. Did you call connect()?")
        return self.session

# Single global instance matching our structural Singleton design pattern
mcp_client = MCPClientManager()
