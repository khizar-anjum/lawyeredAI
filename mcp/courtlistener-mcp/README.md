# CourtListener Legal Research MCP Server (Python)

A specialized Model Context Protocol (MCP) server implemented in **Python** that helps LLMs provide legal advice based on precedents by enabling intelligent case law search and deep investigation capabilities for consumer grievances under $10k in New York State.

## Implementation Versions

- **🐍 Python** (main): `server.py` - Recommended implementation with better error handling and type safety
- **🟨 Node.js** (legacy): `node-impl/index.js` - Original implementation (available in node-impl folder)

## Overview

This advanced MCP server transforms how LLMs interact with legal databases by providing 8 specialized tools for comprehensive legal research. Designed specifically for consumer law in New York State, it combines intelligent search algorithms, outcome analysis, and procedural guidance to support effective legal advice.

## Key Features

### 🔍 **Intelligent Case Discovery**
- Natural language problem-to-case matching
- Automated legal concept extraction
- Precedent similarity analysis
- Citation network exploration

### 📊 **Strategic Analysis Tools**
- Case outcome pattern analysis
- Judge behavior insights
- Legal trend tracking
- Success probability assessment

### 🛠️ **Practical Legal Support**
- Citation validation and expansion
- Procedural requirement guidance
- Court jurisdiction analysis
- Filing strategy recommendations

### 🎯 **Data Optimization**
- Intelligent text truncation to preserve context
- Focused NY court targeting
- Rate limit management
- Error-resilient operations

## Quick Start (Python)

### Prerequisites

1. **Python 3.8+** installed
2. **CourtListener API key** (get from https://www.courtlistener.com/api/)

### Installation

```bash
cd mcp/courtlistener-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Option 1: Environment variable
export COURTLISTENER_API_KEY="your_api_key_here"

# Option 2: Create .env file
cp .env.example .env
# Edit .env and add your API key
```

### Run Server

```bash
source venv/bin/activate
python server.py
```

## Available Tools

### 🔍 search_cases_by_problem
**Purpose**: Find relevant cases using LLM-generated search keywords for precise legal research
- LLM extracts optimal legal keywords from problem descriptions
- Advanced relevance scoring and result ranking
- Focuses on NY consumer law under $10k with intelligent court targeting
- **Parameters**: 
  - `search_keywords` (required): Array of legal terms extracted by LLM (1-10 terms)
  - `problem_summary`: Brief problem context for reference (optional)
  - `case_type`: Consumer issue type (consumer, small-claims, landlord-tenant, etc.)
  - `date_range`: Time preference (recent-2years, established-precedent, all-time)
  - `limit`: Number of cases to return (1-20, default: 10)

**LLM Usage**: The LLM should analyze the client's problem and extract 3-7 relevant legal keywords like `["breach of warranty", "consumer protection", "defective product"]` before calling this function.

### 📋 get_case_details
**Purpose**: Deep dive into specific cases for comprehensive precedent analysis
- Combines docket, cluster, and opinion data intelligently
- Smart text truncation with expansion options
- Includes precedential value assessment
- **Parameters**:
  - `case_id` (required): Case ID from search results
  - `include_full_text`: Include complete opinion text (may be large)

### 🔗 find_similar_precedents
**Purpose**: Discover cases with similar legal reasoning or outcomes
- Uses citation networks and legal concept matching
- Filters by precedential authority and relevance
- **Parameters**:
  - `reference_case_id` (required): Base case to find similar cases
  - `legal_concepts`: Key legal concepts to match
  - `citation_threshold`: Minimum citation count for authority
  - `limit`: Number of similar cases (1-15, default: 8)

### 📊 analyze_case_outcomes
**Purpose**: Analyze outcome patterns to predict success likelihood
- Statistical analysis of similar cases
- Court-specific success rates and duration analysis
- Strategic insights for case positioning
- **Parameters**:
  - `case_type` (required): Type of consumer issue
  - `court_level`: Trial vs appellate analysis
  - `date_range`: Time period for analysis

### ⚖️ get_judge_analysis
**Purpose**: Understand judge's typical rulings for strategic positioning
- Historical decision pattern analysis
- Case type preferences and tendencies
- Strategic recommendations for specific judges
- **Parameters**:
  - `judge_name` (required): Full name of judge
  - `case_type` (required): Area of law to analyze
  - `court`: Specific court identifier

### ✅ validate_citations
**Purpose**: Verify and expand legal citations with related case discovery
- Citation format validation and verification
- Automatic discovery of related cases
- Context relevance assessment
- **Parameters**:
  - `citations` (required): Array of citations to verify
  - `context_text`: Surrounding legal argument for relevance

### 📝 get_procedural_requirements
**Purpose**: Find filing requirements and procedural rules for NY courts
- Court jurisdiction analysis based on claim amount
- Filing fee estimates and deadlines
- Procedural precedent discovery
- **Parameters**:
  - `case_type` (required): Type of consumer complaint
  - `court`: Target NY court (default: ny-civ-ct)
  - `claim_amount`: Dollar amount for jurisdiction analysis

### 📈 track_legal_trends
**Purpose**: Identify recent trends in case law for strategic advantage
- Filing pattern analysis and outcome trends
- Emerging precedent identification
- Strategic timing recommendations
- **Parameters**:
  - `legal_area` (required): Area of law to analyze
  - `time_period`: Analysis timeframe (last-6months, last-year, last-2years)
  - `trend_type`: Type of trend analysis (outcomes, filing-patterns, new-precedents)

## MCP Client Integration

Add to your Claude Desktop or MCP client settings:

```json
{
  "mcpServers": {
    "courtlistener": {
      "command": "python",
      "args": ["/home/khizar/Documents/lawyeredAI/mcp/courtlistener-mcp/server.py"],
      "env": {
        "COURTLISTENER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Note**: Ensure the virtual environment is activated or use the full path to the Python interpreter:
```json
{
  "mcpServers": {
    "courtlistener": {
      "command": "/home/khizar/Documents/lawyeredAI/mcp/courtlistener-mcp/venv/bin/python",
      "args": ["/home/khizar/Documents/lawyeredAI/mcp/courtlistener-mcp/server.py"],
      "env": {
        "COURTLISTENER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Data Management & Context Optimization

### Intelligent Truncation Strategy
To prevent LLM context window overflow:
- **Case excerpts**: 200-500 characters with key information
- **Opinion text**: 1000-5000 characters (expandable with include_full_text)
- **Search results**: Limited to 10-20 items with clear truncation indicators
- **Expansion options**: Clear instructions for getting full content when needed

### Error Handling & Reliability
- Comprehensive error messages with troubleshooting guidance
- Fallback strategies for failed API calls  
- Input validation with helpful suggestions
- Graceful degradation when services are unavailable

## API Rate Limits & Performance

- **Authenticated**: 5,000 requests/hour
- **Unauthenticated**: 100 requests/day (testing only)
- **Optimization**: Field selection, intelligent caching, batch operations
- **Monitoring**: Built-in rate limit tracking and warnings

## Target Courts for LawyeredAI

### Primary Sources (90% of relevant cases)
These courts handle the majority of consumer grievances and small claims under $10,000:

#### New York City
- **Civil Court of the City of New York** (all boroughs)
  - NYC Civil Court, Bronx
  - NYC Civil Court, Kings
  - NYC Civil Court, New York
  - NYC Civil Court, Queens
  - NYC Civil Court, Richmond

#### Major City Courts (Outside NYC)
- Buffalo City Court
- Rochester City Court
- Syracuse City Court
- Albany City Court
- Yonkers City Court
- White Plains City Court
- New Rochelle City Court
- Mount Vernon City Court
- Schenectady City Court
- Utica City Court

#### District Courts
- Nassau County District Court
- Suffolk County District Court

#### Town and Village Justice Courts
Top 20-30 by population, including:
- Hempstead Justice Court
- Brookhaven Justice Court
- Oyster Bay Justice Court
- North Hempstead Justice Court
- Babylon Justice Court

### Secondary Sources (10% of relevant cases)
For precedent-setting decisions and appeals:

- **New York Supreme Court** (County divisions) - Consumer protection cases
- **Appellate Division of the Supreme Court of New York** - Appeals setting consumer law precedent
- **Appellate Terms of the Supreme Court of New York** - Lower court appeals

## LLM Integration Examples

### Keyword Extraction Workflow
The LLM should follow this pattern when using the MCP server:

1. **Analyze client problem** → Extract legal keywords
2. **Call search_cases_by_problem** → With extracted keywords
3. **Review results** → Call get_case_details for promising cases
4. **Expand research** → Use find_similar_precedents for related cases

### Example Usage Scenarios

#### Scenario 1: Defective Product Warranty
**Client Problem**: "I bought a laptop that stopped working after 3 months. The manufacturer won't honor the warranty and claims it's user damage, but I never dropped it."

**LLM Analysis**: Extract keywords → `["breach of warranty", "defective product", "consumer protection", "merchantability"]`

**MCP Call**:
```javascript
{
  "tool": "search_cases_by_problem",
  "arguments": {
    "search_keywords": ["breach of warranty", "defective product", "consumer protection", "merchantability"],
    "problem_summary": "Laptop failed after 3 months, manufacturer denying warranty coverage",
    "case_type": "warranty",
    "date_range": "recent-2years"
  }
}
```

#### Scenario 2: Landlord-Tenant Dispute
**Client Problem**: "My landlord is trying to evict me for non-payment but I've been withholding rent because of mold issues they refuse to fix."

**LLM Analysis**: Extract keywords → `["rent withholding", "habitability", "landlord tenant", "mold", "eviction defense"]`

**MCP Call**:
```javascript
{
  "tool": "search_cases_by_problem", 
  "arguments": {
    "search_keywords": ["rent withholding", "habitability", "landlord tenant", "mold", "eviction defense"],
    "problem_summary": "Tenant withholding rent due to mold, facing eviction",
    "case_type": "landlord-tenant"
  }
}
```

### Keyword Extraction Guidelines
- **3-7 keywords** optimal for balanced precision/recall
- **Use legal terminology** when possible (e.g., "merchantability" vs "quality")
- **Include case type indicators** (warranty, contract, etc.)
- **Add procedural terms** if relevant (dismissal, summary judgment, etc.)
- **Combine specific and general terms** for comprehensive coverage

### Date Range
- Focus on cases from the last 10 years for current precedents
- Use `date_filed_after` parameter with date 10 years ago

### Amount Filters
- Cases with controversy amount under $10,000
- Small claims jurisdiction cases

### Court Identifiers
When using the `court` parameter, prioritize:
- `ny-civ-ct` - NYC Civil Court
- `ny-dist-ct-nassau` - Nassau District Court
- `ny-dist-ct-suffolk` - Suffolk District Court
- `ny-city-ct-*` - Various city courts

## Alternative Implementation (Node.js)

A Node.js implementation is available in the `node-impl/` directory:

```bash
cd node-impl
npm install
npm start
```

**MCP Configuration for Node.js**:
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

## Data Sources

CourtListener aggregates legal data from:
- New York State courts
- Focus on consumer-relevant jurisdictions  
- Recent case law (last 10 years priority)

## Python vs Node.js

| Feature | Python (Recommended) | Node.js (Legacy) |
|---------|---------------------|------------------|
| Error Handling | ✅ Comprehensive | ⚠️ Basic |
| Type Safety | ✅ Full type hints | ❌ No types |
| Async Performance | ✅ Native async/await | ✅ Native async/await |
| Memory Management | ✅ Context managers | ⚠️ Manual cleanup |
| Code Maintainability | ✅ Class-based architecture | ⚠️ Functional approach |
| Testing | ✅ Built-in test suite | ❌ No tests |
| Documentation | ✅ Comprehensive docs | ⚠️ Basic docs |

## License

MIT