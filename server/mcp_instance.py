from mcp.server.mcpserver import MCPServer
from system_instructions import SIMWORKS_INSTRUCTIONS, system_instructions

mcp_instance = MCPServer(name="simworks-fd-solutions-mcp-server",
    # Auto-injected by MCP clients that honor server instructions
    # (Cursor surfaces this as namespaceUseInstructions).
    instructions=SIMWORKS_INSTRUCTIONS,
)

# Named MCP Prompt — same text as system_instructions.py / instructions=.
mcp_instance.prompt(
    name="system_instructions",
    description=(
        "System instructions for the SimWorks FD Solutions MCP simulation assistant. "
        "Operational rules only: MCP tools only, SI units, confirm before run, "
        "name tracking / select paths. No separate guideline-fetch tool required."
    ),
)(system_instructions)
