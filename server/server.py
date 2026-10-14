import click
import logging
import sys
from mcp_instance import mcp_instance
from fd_instance import configure_fd, initialize_fd

# register
import tools

# CLI
@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"], case_sensitive=False),
    default="stdio",
    show_default=True,
    help="MCP transport: stdio (typical for LLM clients) or streamable-http",
)
@click.option("--host", default="127.0.0.1", help="Host to bind to for HTTP (e.g., '127.0.0.1' or '0.0.0.0')")
@click.option("--port", default=3001, help="Port to listen on for HTTP")
@click.option("--attach", is_flag=True, default=False, help="Attached to an existing fd_solutions instance")
@click.option("--server_name", default=None, help="In the case of attach, the name of fd_solutions instance")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(
    transport: str,
    host: str,
    port: int,
    attach: bool,
    server_name: str,
    log_level: str,
) -> int:
    # STDIO uses stdout for the MCP protocol; keep logs on stderr.
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)

    if attach and not server_name:
        logger.error("Error: --server_name is required when using --attach.")
        return 1

    if attach:
        # Existing FD instance is already running — connect immediately.
        logger.info("Attaching to FD Solutions instance '%s'...", server_name)
        initialize_fd(attach=True, server_name=server_name)
    else:
        # Defer FD launch until the first tool/resource actually uses fd_instance.
        configure_fd(attach=False, server_name=None)
        logger.info("FD Solutions will start on first tool use")

    transport = transport.lower()
    if transport == "stdio":
        logger.info("Starting MCP Server (stdio)")
        mcp_instance.run(transport="stdio")
    else:
        logger.info(f"Starting MCP Server on http://{host}:{port}")
        logger.info(f"Endpoint will be: http://{host}:{port}/mcp")
        mcp_instance.run(
            transport="streamable-http",
            host=host,
            port=port,
            json_response=True,
        )

    return 0

if __name__ == "__main__":
    main()
