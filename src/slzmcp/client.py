import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import TextContent

async def main():
    url = "http://127.0.0.1:8000/mcp"
    
    async with streamablehttp_client(url) as (read, write, get_session_id):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Call echo tool
            result = await session.call_tool("echo", {"message": "Hello from client!"})
            if result.content and isinstance(result.content[0], TextContent):
                print(f"\nResult: {result.content[0].text}")
            else:
                print(f"\nResult: {result.content}")
            
            # Get session ID (useful for reconnection)
            session_id = get_session_id()
            print(f"\nSession ID: {session_id}")

if __name__ == "__main__":
    asyncio.run(main())
