#!/usr/bin/env python3

import asyncio
import os
from typing import Any
import httpx
from datetime import datetime

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"
COURTLISTENER_API_TOKEN = os.getenv("COURTLISTENER_API_TOKEN", "")

# NY State Court Focus as per design spec
NY_PRIMARY_COURTS = [
    "ny-civ-ct",  # NYC Civil Court
    "ny-city-ct-buffalo", 
    "ny-city-ct-rochester",
    "ny-city-ct-syracuse",
    "ny-city-ct-albany",
    "ny-city-ct-yonkers",
    "ny-dist-ct-nassau",  # Nassau County District Court
    "ny-dist-ct-suffolk", # Suffolk County District Court
]

NY_SECONDARY_COURTS = [
    "ny-supreme-ct",
    "ny-app-div-1st",
    "ny-app-div-2nd", 
    "ny-app-div-3rd",
    "ny-app-div-4th",
    "ny-ct-app",
]

server = Server("courtlistener-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_cases_by_problem",
            description="Search for relevant legal cases based on extracted legal keywords. LLM should extract key legal terms and concepts from client problem.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key legal terms and concepts extracted by LLM from client problem",
                        "minItems": 1
                    },
                    "case_type": {
                        "type": "string",
                        "description": "Type of case: consumer, small_claims, landlord_tenant, contract, etc.",
                        "enum": ["consumer", "small_claims", "landlord_tenant", "contract"]
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Date range: recent (last 2 years), established (2-10 years), all",
                        "enum": ["recent", "established", "all"],
                        "default": "recent"
                    },
                    "jurisdiction": {
                        "type": "string",
                        "description": "Court jurisdiction to search",
                        "enum": ["ny", "federal", "all"],
                        "default": "ny"
                    }
                },
                "required": ["keywords"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    if name == "search_cases_by_problem":
        keywords = arguments.get("keywords", [])
        case_type = arguments.get("case_type")
        date_range = arguments.get("date_range", "recent")
        jurisdiction = arguments.get("jurisdiction", "ny")
        
        # Build search query from keywords
        query_terms = list(keywords)  # Use LLM-extracted keywords directly
        
        # Add case type specific terms if provided
        if case_type == "consumer":
            query_terms.extend(["consumer", "warranty", "defect"])
        elif case_type == "small_claims":
            query_terms.extend(["damages", "compensation"])
        elif case_type == "landlord_tenant":
            query_terms.extend(["landlord", "tenant", "lease"])
        elif case_type == "contract":
            query_terms.extend(["contract", "breach", "agreement"])
            
        search_query = " ".join(query_terms)
        
        # Set up API request
        headers = {}
        if COURTLISTENER_API_TOKEN:
            headers["Authorization"] = f"Token {COURTLISTENER_API_TOKEN}"
        
        params = {
            "q": search_query,
            "type": "o",
            "order_by": "score desc",
            "page_size": 20  # Increased for better results
        }
        
        # Apply jurisdiction filtering as per design spec
        if jurisdiction == "ny":
            # Focus on NY courts (90% primary, 10% secondary per spec)
            ny_courts = NY_PRIMARY_COURTS + NY_SECONDARY_COURTS
            params["court"] = ",".join(ny_courts)
        elif jurisdiction == "federal":
            # Focus on federal courts
            params["court__jurisdiction"] = "F"
        
        # Add date filtering
        if date_range == "recent":
            two_years_ago = datetime.now().replace(year=datetime.now().year - 2)
            params["filed_after"] = two_years_ago.strftime("%Y-%m-%d")
        elif date_range == "established":
            ten_years_ago = datetime.now().replace(year=datetime.now().year - 10)
            two_years_ago = datetime.now().replace(year=datetime.now().year - 2)
            params["filed_after"] = ten_years_ago.strftime("%Y-%m-%d")
            params["filed_before"] = two_years_ago.strftime("%Y-%m-%d")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{COURTLISTENER_API_BASE}/search/",
                    params=params,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    error_detail = f"Status: {response.status_code}, URL: {response.url}, Response: {response.text[:500]}"
                    return [types.TextContent(
                        type="text",
                        text=f"API Error: {error_detail}"
                    )]
                
                data = response.json()
                
                # Enhanced response formatting per design spec
                result_text = f"Search Results for Legal Keywords: {', '.join(keywords)}\n"
                result_text += f"Query: {search_query}\n"
                result_text += f"Jurisdiction: {jurisdiction.upper()}\n"
                result_text += f"Case Type: {case_type or 'General'}\n"
                result_text += f"Date Range: {date_range}\n"
                result_text += f"Total Found: {data.get('count', 0)} cases\n"
                result_text += f"Showing: {len(data.get('results', []))} results\n\n"
                
                if not data.get('results'):
                    result_text += "No cases found. Try different keywords or broader search criteria.\n"
                else:
                    result_text += "Relevant Cases:\n"
                    for i, case in enumerate(data.get('results', []), 1):
                        result_text += f"\n{i}. {case.get('case_name', 'Case name not available')}\n"
                        result_text += f"   Court: {case.get('court', 'Court not specified')}\n"
                        result_text += f"   Filed: {case.get('date_filed', 'Date not available')}\n"
                        result_text += f"   Citation Count: {case.get('citation_count', 0)}\n"
                        
                        # Add case IDs for further investigation
                        if case.get('id'):
                            result_text += f"   Case ID: {case.get('id')}\n"
                        if case.get('docket'):
                            result_text += f"   Docket ID: {case.get('docket')}\n"
                        if case.get('cluster'):
                            result_text += f"   Cluster ID: {case.get('cluster')}\n"
                
                return [types.TextContent(type="text", text=result_text)]
                
        except Exception as e:
            return [types.TextContent(
                type="text", 
                text=f"Error searching cases: {str(e)}"
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="courtlistener-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())