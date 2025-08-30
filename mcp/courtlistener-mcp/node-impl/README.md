# CourtListener MCP Server (Node.js Implementation)

This is the legacy Node.js implementation of the CourtListener MCP Server. 

**⚠️ Note**: The Python implementation (`../server.py`) is now the recommended version with better error handling, type safety, and maintainability.

## Quick Start

```bash
# Install dependencies
npm install

# Set API key
export COURTLISTENER_API_KEY="your_api_key_here"

# Run server
npm start
```

## MCP Configuration

```json
{
  "mcpServers": {
    "courtlistener": {
      "command": "node",
      "args": ["/home/khizar/Documents/lawyeredAI/mcp/courtlistener-mcp/node-impl/index.js"],
      "env": {
        "COURTLISTENER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

This Node.js implementation includes the original 8 tools with LLM keyword-driven search:

1. **search_cases_by_problem** - Find cases using LLM-extracted keywords
2. **get_case_details** - Deep dive into specific cases
3. **find_similar_precedents** - Discover similar cases
4. **analyze_case_outcomes** - Outcome pattern analysis
5. **get_judge_analysis** - Judge behavior insights
6. **validate_citations** - Citation verification
7. **get_procedural_requirements** - Filing guidance  
8. **track_legal_trends** - Trend analysis

## Migration to Python

For new deployments, consider using the Python implementation (`../server.py`) which offers:

- ✅ Better error handling and debugging
- ✅ Full type safety with hints
- ✅ Comprehensive test suite
- ✅ Improved documentation
- ✅ More maintainable architecture

## Dependencies

- Node.js 18+
- @modelcontextprotocol/sdk
- axios for HTTP requests
- dotenv for configuration

## License

MIT