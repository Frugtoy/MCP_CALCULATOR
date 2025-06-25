from server.api.mcp_calculator import server

if __name__ == '__main__':
    server.run(transport="streamable-http")
