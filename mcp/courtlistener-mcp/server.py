#!/usr/bin/env python3
"""
CourtListener Legal Research MCP Server

A specialized Model Context Protocol (MCP) server that helps LLMs provide 
legal advice based on precedents by enabling intelligent case law search 
and deep investigation capabilities for consumer grievances under $10k in New York State.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode

import httpx
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configuration
COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"
API_KEY = os.getenv("COURTLISTENER_API_KEY", "")

class CourtListenerMCPServer:
    """MCP server for CourtListener legal database integration."""
    
    def __init__(self):
        self.server = Server("courtlistener-mcp")
        self.http_client = None
        
    async def __aenter__(self):
        # Create HTTP client with appropriate headers
        headers = {}
        if API_KEY:
            headers["Authorization"] = f"Token {API_KEY}"
        
        self.http_client = httpx.AsyncClient(
            base_url=COURTLISTENER_API_BASE,
            headers=headers,
            timeout=30.0
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()
    
    def get_ny_courts(self) -> Dict[str, List[str]]:
        """Get NY court identifiers organized by priority."""
        return {
            "primary": [
                "ny-civ-ct", "ny-city-ct-buffalo", "ny-city-ct-rochester", 
                "ny-city-ct-syracuse", "ny-city-ct-albany", "ny-city-ct-yonkers",
                "ny-dist-ct-nassau", "ny-dist-ct-suffolk"
            ],
            "secondary": [
                "ny-supreme-ct", "ny-app-div-1st", "ny-app-div-2nd", 
                "ny-app-div-3rd", "ny-app-div-4th", "ny-ct-app"
            ]
        }
    
    def validate_search_keywords(self, keywords: List[str]) -> List[str]:
        """Validate and clean search keywords from LLM."""
        if not isinstance(keywords, list) or len(keywords) == 0:
            raise ValueError("search_keywords must be a non-empty array of legal terms")
        
        if len(keywords) > 10:
            raise ValueError("Maximum 10 search keywords allowed for optimal performance")
        
        valid_keywords = [
            keyword.strip() for keyword in keywords 
            if isinstance(keyword, str) and keyword.strip() and len(keyword) <= 100
        ]
        
        if not valid_keywords:
            raise ValueError("No valid search keywords provided. Keywords must be non-empty strings.")
        
        return valid_keywords
    
    def truncate_text(self, text: Optional[str], max_length: int = 1000) -> str:
        """Truncate text to prevent context window overflow."""
        if not text or len(text) <= max_length:
            return text or ""
        return text[:max_length] + "... [TRUNCATED - use get_case_details with include_full_text for complete text]"
    
    async def search_cases_by_problem(self, args: Dict[str, Any]) -> CallToolResult:
        """Find relevant cases using LLM-generated search keywords."""
        try:
            search_keywords = args.get("search_keywords", [])
            problem_summary = args.get("problem_summary", "")
            case_type = args.get("case_type")
            date_range = args.get("date_range", "recent-2years")
            limit = min(args.get("limit", 10), 20)
            
            # Validate and clean keywords
            valid_keywords = self.validate_search_keywords(search_keywords)
            
            # Build search query from LLM-provided keywords
            primary_terms = valid_keywords[:5]  # Use top 5 keywords for primary search
            search_query = " OR ".join([f'"{term}"' for term in primary_terms])
            
            # Add consumer context if not already present
            has_consumer = any("consumer" in k.lower() for k in valid_keywords)
            if not has_consumer:
                enhanced_query = f"({search_query}) AND (consumer OR \"consumer protection\")"
            else:
                enhanced_query = search_query
            
            # Date filtering
            params = {
                "q": enhanced_query,
                "type": "o",
                "court": ",".join(self.get_ny_courts()["primary"]),
                "cited_gt": 0,
                "page_size": min(limit * 2, 40),  # Get more results to filter for relevance
                "fields": "id,case_name,court,date_filed,citation_count,snippet"
            }
            
            # Apply date filters
            current_date = datetime.now()
            if date_range == "recent-2years":
                two_years_ago = current_date - timedelta(days=730)
                params["filed_after"] = two_years_ago.strftime("%Y-%m-%d")
            elif date_range == "established-precedent":
                ten_years_ago = current_date - timedelta(days=3650)
                five_years_ago = current_date - timedelta(days=1825)
                params["filed_after"] = ten_years_ago.strftime("%Y-%m-%d")
                params["filed_before"] = five_years_ago.strftime("%Y-%m-%d")
            
            # Make API request
            response = await self.http_client.get("/search/", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Score results based on keyword relevance
            scored_results = []
            for item in data.get("results", []):
                text = f"{item.get('case_name', '')} {item.get('snippet', '')}".lower()
                keyword_score = sum(1 for keyword in valid_keywords if keyword.lower() in text)
                scored_results.append({**item, "relevance_score": keyword_score})
            
            # Sort by relevance score, then citation count
            sorted_results = sorted(
                scored_results,
                key=lambda x: (x.get("relevance_score", 0), x.get("citation_count", 0)),
                reverse=True
            )[:limit]
            
            # Format results
            results = []
            for item in sorted_results:
                citation_count = item.get("citation_count", 0)
                precedential_value = (
                    "Strong" if citation_count > 10 else
                    "Moderate" if citation_count > 2 else
                    "Limited"
                )
                
                results.append({
                    "case_id": item.get("id"),
                    "case_name": item.get("case_name"),
                    "court": item.get("court"),
                    "date_filed": item.get("date_filed"),
                    "citation_count": citation_count,
                    "relevance_summary": self.truncate_text(item.get("snippet"), 200),
                    "keyword_matches": item.get("relevance_score", 0),
                    "precedential_value": precedential_value
                })
            
            result_data = {
                "search_strategy": {
                    "keywords_used": valid_keywords,
                    "query_constructed": enhanced_query,
                    "date_range_applied": date_range,
                    "courts_searched": "NY primary consumer courts"
                },
                "problem_context": problem_summary or "No summary provided",
                "search_results": {
                    "total_found": data.get("count", 0),
                    "returned_count": len(results),
                    "cases": results
                },
                "usage_note": (
                    "Results limited for readability. Use find_similar_precedents with top cases for deeper research."
                    if len(results) == limit else
                    "All relevant cases returned based on keyword search."
                )
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result_data, indent=2))]
            )
            
        except Exception as error:
            error_data = {
                "error": f"Search failed: {str(error)}",
                "suggestion": "Ensure search_keywords is an array of 1-10 legal terms. Example: [\"breach of warranty\", \"consumer protection\", \"defective product\"]",
                "example_usage": {
                    "search_keywords": ["breach of warranty", "consumer protection"],
                    "problem_summary": "Client purchased defective car, dealer refuses warranty repair",
                    "case_type": "warranty"
                }
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(error_data, indent=2))]
            )
    
    async def get_case_details(self, args: Dict[str, Any]) -> CallToolResult:
        """Deep dive into specific case for precedent analysis."""
        case_id = args.get("case_id")
        include_full_text = args.get("include_full_text", False)
        
        if not case_id:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": "case_id is required"}, indent=2))]
            )
        
        try:
            # Try to get cluster first, fallback to docket
            cluster_response = None
            try:
                cluster_response = await self.http_client.get(f"/clusters/{case_id}/")
                cluster_response.raise_for_status()
            except httpx.HTTPError:
                # Try as docket ID
                docket_response = await self.http_client.get(f"/dockets/{case_id}/")
                docket_response.raise_for_status()
                docket = docket_response.json()
                
                if docket.get("clusters"):
                    cluster_id = docket["clusters"][0].split("/")[-2]
                    cluster_response = await self.http_client.get(f"/clusters/{cluster_id}/")
                    cluster_response.raise_for_status()
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps({
                            "case_id": case_id,
                            "error": "No opinions found for this case",
                            "docket_info": {
                                "case_name": docket.get("case_name"),
                                "court": docket.get("court"),
                                "date_filed": docket.get("date_filed"),
                                "nature_of_suit": docket.get("nature_of_suit")
                            }
                        }, indent=2))]
                    )
            
            cluster = cluster_response.json()
            
            # Get opinion details
            opinions = []
            if cluster.get("sub_opinions"):
                for opinion_url in cluster["sub_opinions"][:3]:  # Limit to 3 opinions
                    try:
                        opinion_id = opinion_url.split("/")[-2]
                        fields = "id,type,author_str,plain_text,html_with_citations" if include_full_text else "id,type,author_str,snippet"
                        opinion_response = await self.http_client.get(f"/opinions/{opinion_id}/", params={"fields": fields})
                        opinion_response.raise_for_status()
                        opinion = opinion_response.json()
                        
                        content = (
                            self.truncate_text(opinion.get("plain_text"), 5000) if include_full_text
                            else self.truncate_text(opinion.get("snippet", "No excerpt available"), 500)
                        )
                        
                        opinions.append({
                            "opinion_id": opinion.get("id"),
                            "type": opinion.get("type"),
                            "author": opinion.get("author_str"),
                            "content": content
                        })
                    except Exception as e:
                        print(f"Error fetching opinion: {e}", file=sys.stderr)
            
            citation_count = cluster.get("citation_count", 0)
            result = {
                "case_id": cluster.get("id"),
                "case_name": cluster.get("case_name"),
                "court": cluster.get("court"),
                "date_filed": cluster.get("date_filed"),
                "citation_count": citation_count,
                "precedential_status": cluster.get("precedential_status"),
                "judges": cluster.get("judges"),
                "opinions": opinions,
                "cited_by_count": citation_count,
                "legal_significance": (
                    "High" if citation_count > 10 else
                    "Medium" if citation_count > 2 else
                    "Low"
                )
            }
            
            if not include_full_text and any("TRUNCATED" in op.get("content", "") for op in opinions):
                result["note"] = "Use include_full_text: true to get complete opinion text"
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
            
        except Exception as error:
            error_data = {
                "case_id": case_id,
                "error": f"Failed to retrieve case details: {str(error)}",
                "suggestion": "Verify the case_id is correct. Use search_cases_by_problem to find valid case IDs."
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(error_data, indent=2))]
            )
    
    async def find_similar_precedents(self, args: Dict[str, Any]) -> CallToolResult:
        """Find cases with similar legal reasoning or outcomes."""
        reference_case_id = args.get("reference_case_id")
        legal_concepts = args.get("legal_concepts", [])
        citation_threshold = args.get("citation_threshold", 1)
        limit = min(args.get("limit", 8), 15)
        
        if not reference_case_id:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": "reference_case_id is required"}, indent=2))]
            )
        
        try:
            # Get reference case details
            reference_response = await self.http_client.get(f"/clusters/{reference_case_id}/")
            reference_response.raise_for_status()
            reference_case = reference_response.json()
            
            # Build search terms from reference case and provided concepts
            search_terms = []
            search_terms.extend(legal_concepts[:3])  # Use provided concepts
            
            # Extract terms from case name
            case_name = reference_case.get("case_name", "")
            if " v. " in case_name:
                search_terms.append(case_name.split(" v. ")[0])
            
            # Limit to 5 terms total
            search_terms = [term for term in search_terms if term][:5]
            if not search_terms:
                search_terms = ["consumer protection"]
            
            search_query = " OR ".join(f'"{term}"' for term in search_terms)
            ny_courts = self.get_ny_courts()
            all_courts = ny_courts["primary"] + ny_courts["secondary"]
            
            params = {
                "q": search_query,
                "type": "o",
                "court": ",".join(all_courts),
                "cited_gt": max(citation_threshold - 1, 0),
                "page_size": limit + 5,
                "fields": "id,case_name,court,date_filed,citation_count,snippet"
            }
            
            response = await self.http_client.get("/search/", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Filter out the reference case and format results
            results = []
            for item in data.get("results", []):
                if item.get("id") != int(reference_case_id):
                    citation_count = item.get("citation_count", 0)
                    precedential_value = (
                        "Strong" if citation_count > 10 else
                        "Moderate" if citation_count > 2 else
                        "Limited"
                    )
                    
                    results.append({
                        "case_id": item.get("id"),
                        "case_name": item.get("case_name"),
                        "court": item.get("court"),
                        "date_filed": item.get("date_filed"),
                        "citation_count": citation_count,
                        "similarity_summary": self.truncate_text(item.get("snippet"), 150),
                        "precedential_value": precedential_value
                    })
                    
                    if len(results) >= limit:
                        break
            
            result_data = {
                "reference_case": {
                    "id": reference_case.get("id"),
                    "name": reference_case.get("case_name"),
                    "court": reference_case.get("court")
                },
                "search_strategy": {
                    "legal_concepts_used": search_terms,
                    "citation_threshold": citation_threshold,
                    "courts_searched": "NY primary and secondary courts"
                },
                "similar_cases": results,
                "analysis_note": f"Found {len(results)} similar cases. Cases with higher citation counts have stronger precedential value."
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result_data, indent=2))]
            )
            
        except Exception as error:
            error_data = {
                "reference_case_id": reference_case_id,
                "error": f"Cannot find similar precedents: {str(error)}",
                "suggestion": "Verify the reference case ID. Use search_cases_by_problem to find valid case IDs first."
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(error_data, indent=2))]
            )
    
    async def analyze_case_outcomes(self, args: Dict[str, Any]) -> CallToolResult:
        """Analyze outcome patterns for similar cases to predict success likelihood."""
        case_type = args.get("case_type")
        court_level = args.get("court_level", "all") 
        date_range = args.get("date_range", "last-2years")
        
        if not case_type:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": "case_type is required"}, indent=2))]
            )
        
        try:
            current_date = datetime.now()
            params = {
                "q": f'"{case_type}" OR consumer',
                "type": "r",
                "page_size": 50,
                "fields": "id,case_name,court,date_filed,date_terminated,nature_of_suit"
            }
            
            if date_range == "last-year":
                params["filed_after"] = (current_date - timedelta(days=365)).strftime("%Y-%m-%d")
            elif date_range == "last-2years":
                params["filed_after"] = (current_date - timedelta(days=730)).strftime("%Y-%m-%d")
            elif date_range == "last-5years":
                params["filed_after"] = (current_date - timedelta(days=1825)).strftime("%Y-%m-%d")
            
            ny_courts = self.get_ny_courts()
            courts_to_search = (
                ny_courts["primary"] if court_level == "trial" else
                ny_courts["secondary"] if court_level == "appellate" else
                ny_courts["primary"] + ny_courts["secondary"]
            )
            params["court"] = ",".join(courts_to_search)
            
            response = await self.http_client.get("/search/", params=params)
            response.raise_for_status()
            cases = response.json().get("results", [])
            
            outcomes = {
                "total_cases": len(cases),
                "terminated_cases": len([c for c in cases if c.get("date_terminated")]),
                "ongoing_cases": len([c for c in cases if not c.get("date_terminated")]),
                "court_breakdown": {},
                "avg_case_duration": None
            }
            
            for case in cases:
                court = case.get("court", "unknown")
                outcomes["court_breakdown"][court] = outcomes["court_breakdown"].get(court, 0) + 1
            
            terminated_cases = [c for c in cases if c.get("date_terminated") and c.get("date_filed")]
            if terminated_cases:
                durations = []
                for case in terminated_cases:
                    try:
                        filed = datetime.fromisoformat(case["date_filed"].replace("Z", "+00:00"))
                        terminated = datetime.fromisoformat(case["date_terminated"].replace("Z", "+00:00"))
                        duration_days = (terminated - filed).days
                        if 0 < duration_days < 3650:
                            durations.append(duration_days)
                    except (ValueError, KeyError):
                        continue
                if durations:
                    outcomes["avg_case_duration"] = round(sum(durations) / len(durations))
            
            most_active_court = max(outcomes["court_breakdown"].items(), key=lambda x: x[1])[0] if outcomes["court_breakdown"] else "none"
            case_closure_rate = round((outcomes["terminated_cases"] / outcomes["total_cases"]) * 100) if outcomes["total_cases"] > 0 else 0
            
            result_data = {
                "analysis_parameters": {
                    "case_type": case_type,
                    "court_level": court_level, 
                    "date_range": date_range,
                    "courts_analyzed": len(courts_to_search)
                },
                "outcome_patterns": outcomes,
                "success_indicators": {
                    "case_closure_rate": f"{case_closure_rate}%" if outcomes["terminated_cases"] > 0 else "Insufficient data",
                    "avg_duration_days": outcomes["avg_case_duration"],
                    "most_active_court": most_active_court
                },
                "strategic_insight": (
                    "Most cases reach resolution - favorable for litigation"
                    if outcomes["terminated_cases"] > outcomes["ongoing_cases"]
                    else "Many cases still pending - consider alternative dispute resolution"
                )
            }
            
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result_data, indent=2))])
            
        except Exception as error:
            error_data = {
                "case_type": case_type,
                "error": f"Analysis failed: {str(error)}",
                "suggestion": "Try a broader case_type or different date_range for better results."
            }
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(error_data, indent=2))])

    async def get_judge_analysis(self, args: Dict[str, Any]) -> CallToolResult:
        """Analyze judge's typical rulings on similar issues for strategic insights."""
        judge_name = args.get("judge_name")
        case_type = args.get("case_type")
        court = args.get("court")
        
        if not judge_name or not case_type:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({
                    "error": "Both judge_name and case_type are required"
                }, indent=2))]
            )
        
        try:
            judge_params = {"name__icontains": judge_name, "fields": "id,name_full,positions"}
            judge_response = await self.http_client.get("/people/", params=judge_params)
            judge_response.raise_for_status()
            judges = judge_response.json().get("results", [])
            
            if not judges:
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({
                        "judge_name": judge_name,
                        "error": "Judge not found in database",
                        "suggestion": "Check spelling or try last name only"
                    }, indent=2))]
                )
            
            judge = judges[0]
            opinion_params = {
                "author": judge.get("id"),
                "q": case_type,
                "type": "o",
                "page_size": 20,
                "fields": "id,case_name,court,date_filed,type"
            }
            if court:
                opinion_params["court"] = court
            
            opinion_response = await self.http_client.get("/search/", params=opinion_params)
            opinion_response.raise_for_status()
            opinions = opinion_response.json().get("results", [])
            
            opinion_types = {}
            courts_served = {}
            for opinion in opinions:
                op_type = opinion.get("type", "unknown")
                opinion_types[op_type] = opinion_types.get(op_type, 0) + 1
                op_court = opinion.get("court", "unknown")
                courts_served[op_court] = courts_served.get(op_court, 0) + 1
            
            analysis = {
                "judge_info": {
                    "name": judge.get("name_full"),
                    "id": judge.get("id"),
                    "positions": judge.get("positions", [])[-3:] if judge.get("positions") else []
                },
                "case_analysis": {
                    "total_opinions_found": len(opinions),
                    "opinion_types": opinion_types,
                    "courts_served": courts_served,
                    "recent_cases": [
                        {
                            "case_name": op.get("case_name"),
                            "court": op.get("court"),
                            "date": op.get("date_filed"),
                            "type": op.get("type")
                        }
                        for op in opinions[:5]
                    ]
                },
                "strategic_insight": (
                    "Judge has significant experience in this area"
                    if len(opinions) > 5
                    else "Limited data available - consider broader search"
                )
            }
            
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(analysis, indent=2))])
            
        except Exception as error:
            error_data = {
                "judge_name": judge_name,
                "case_type": case_type, 
                "error": f"Analysis failed: {str(error)}",
                "suggestion": "Verify judge name spelling and ensure case_type is relevant"
            }
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(error_data, indent=2))])

    async def validate_citations(self, args: Dict[str, Any]) -> CallToolResult:
        """Verify and expand legal citations with related case discovery."""
        citations = args.get("citations", [])
        context_text = args.get("context_text")
        
        if not citations:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": "citations array is required"}, indent=2))]
            )
        
        results = {
            "validation_summary": {"total_citations": len(citations), "valid_citations": 0, "invalid_citations": 0},
            "citation_details": [],
            "related_cases": []
        }
        
        for citation in citations[:10]:  # Limit to 10
            try:
                search_params = {
                    "q": f'"{citation}"',
                    "type": "o",
                    "page_size": 5,
                    "fields": "id,case_name,court,date_filed,citation_count,snippet"
                }
                
                response = await self.http_client.get("/search/", params=search_params)
                response.raise_for_status()
                matches = response.json().get("results", [])
                
                if matches:
                    results["validation_summary"]["valid_citations"] += 1
                    best_match = matches[0]
                    results["citation_details"].append({
                        "input_citation": citation,
                        "status": "valid",
                        "matched_case": {
                            "case_id": best_match.get("id"),
                            "case_name": best_match.get("case_name"),
                            "court": best_match.get("court"),
                            "date_filed": best_match.get("date_filed"),
                            "citation_count": best_match.get("citation_count")
                        },
                        "context_relevance": "relevant" if context_text and best_match.get("snippet") else "needs_review"
                    })
                    
                    for match in matches[1:3]:
                        results["related_cases"].append({
                            "case_id": match.get("id"),
                            "case_name": match.get("case_name"),
                            "relationship": "related_citation"
                        })
                else:
                    results["validation_summary"]["invalid_citations"] += 1
                    results["citation_details"].append({
                        "input_citation": citation,
                        "status": "not_found",
                        "suggestion": "Check citation format or search for case name directly"
                    })
                    
            except Exception as error:
                results["validation_summary"]["invalid_citations"] += 1
                results["citation_details"].append({
                    "input_citation": citation,
                    "status": "error",
                    "error": str(error)
                })
        
        if len(citations) > 10:
            results["note"] = f"Only first 10 citations processed. Total: {len(citations)}"
        
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(results, indent=2))])

    async def get_procedural_requirements(self, args: Dict[str, Any]) -> CallToolResult:
        """Find procedural rules and requirements for case type in NY courts."""
        case_type = args.get("case_type")
        court = args.get("court", "ny-civ-ct")
        claim_amount = args.get("claim_amount")
        
        if not case_type:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": "case_type is required"}, indent=2))]
            )
        
        court_jurisdiction = {
            "ny-civ-ct": {"name": "NYC Civil Court", "limit": 25000, "filing_fee": "$20-45"},
            "ny-dist-ct-nassau": {"name": "Nassau District Court", "limit": 15000, "filing_fee": "$15-30"},
            "ny-dist-ct-suffolk": {"name": "Suffolk District Court", "limit": 15000, "filing_fee": "$15-30"},
            "ny-supreme-ct": {"name": "NY Supreme Court", "limit": None, "filing_fee": "$210+"}
        }
        
        selected_court = court_jurisdiction.get(court, court_jurisdiction["ny-civ-ct"])
        jurisdiction_check = (
            claim_amount <= selected_court["limit"]
            if claim_amount and selected_court["limit"]
            else True
        )
        
        try:
            search_params = {
                "q": f'"{case_type}" AND (procedure OR filing OR requirement)',
                "court": court,
                "type": "o", 
                "page_size": 10,
                "fields": "id,case_name,date_filed,snippet"
            }
            
            response = await self.http_client.get("/search/", params=search_params)
            response.raise_for_status()
            procedural_cases = response.json().get("results", [])[:5]
            
            requirements = {
                "court_info": {
                    "court_name": selected_court["name"],
                    "jurisdiction_limit": selected_court["limit"],
                    "estimated_filing_fee": selected_court["filing_fee"],
                    "jurisdiction_appropriate": jurisdiction_check
                },
                "case_type_analysis": case_type,
                "procedural_insights": [
                    {
                        "case_name": case.get("case_name"),
                        "date": case.get("date_filed"),
                        "procedural_note": self.truncate_text(case.get("snippet"), 150)
                    }
                    for case in procedural_cases
                ],
                "general_requirements": [
                    "File complaint with proper court",
                    "Pay required filing fees", 
                    "Serve defendants properly",
                    "Include all required documentation",
                    "Meet statute of limitations"
                ],
                "recommended_actions": [
                    (f"✓ {selected_court['name']} has jurisdiction for this claim amount"
                     if jurisdiction_check
                     else f"⚠ Consider {'higher' if selected_court['limit'] else 'lower'} court for this claim amount"),
                    "Review recent similar cases for procedural precedents",
                    "Ensure all documentary evidence is properly prepared", 
                    "Consider mediation or settlement before filing"
                ]
            }
            
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(requirements, indent=2))])
            
        except Exception as error:
            error_data = {
                "case_type": case_type,
                "court": selected_court["name"],
                "error": f"Could not retrieve specific procedural requirements: {str(error)}",
                "general_guidance": {
                    "filing_fee": selected_court["filing_fee"],
                    "jurisdiction_limit": selected_court["limit"],
                    "basic_steps": ["Prepare complaint", "Pay fees", "Serve defendants", "Await response"]
                }
            }
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(error_data, indent=2))])

    async def track_legal_trends(self, args: Dict[str, Any]) -> CallToolResult:
        """Identify recent trends in similar cases for strategic advantage."""
        legal_area = args.get("legal_area")
        time_period = args.get("time_period", "last-year")
        trend_type = args.get("trend_type", "outcomes")
        
        if not legal_area:
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps({"error": "legal_area is required"}, indent=2))]
            )
        
        area_queries = {
            "consumer-protection": "consumer protection OR warranty OR defective",
            "small-claims": "small claims OR monetary damages",
            "landlord-tenant": "landlord tenant OR eviction OR rent",
            "contract-disputes": "breach of contract OR agreement", 
            "warranty-claims": "warranty OR merchantability OR fitness"
        }
        
        search_query = area_queries.get(legal_area, legal_area)
        
        try:
            current_date = datetime.now()
            params = {
                "q": search_query,
                "type": "o" if trend_type == "new-precedents" else "r",
                "page_size": 50,
                "order_by": "-date_filed",
                "fields": "id,case_name,court,date_filed,date_terminated,citation_count"
            }
            
            if time_period == "last-6months":
                params["filed_after"] = (current_date - timedelta(days=180)).strftime("%Y-%m-%d")
            elif time_period == "last-year":
                params["filed_after"] = (current_date - timedelta(days=365)).strftime("%Y-%m-%d")
            elif time_period == "last-2years":
                params["filed_after"] = (current_date - timedelta(days=730)).strftime("%Y-%m-%d")
            
            ny_courts = self.get_ny_courts()
            params["court"] = ",".join(ny_courts["primary"] + ny_courts["secondary"])
            
            response = await self.http_client.get("/search/", params=params)
            response.raise_for_status()
            cases = response.json().get("results", [])
            
            trends = {
                "analysis_period": time_period,
                "legal_area": legal_area,
                "total_cases_found": len(cases),
                "trend_analysis": {},
                "court_activity": {},
                "monthly_filing_pattern": {},
                "key_trends": []
            }
            
            for case in cases:
                court = case.get("court", "unknown")
                trends["court_activity"][court] = trends["court_activity"].get(court, 0) + 1
                if case.get("date_filed"):
                    month = case["date_filed"][:7]
                    trends["monthly_filing_pattern"][month] = trends["monthly_filing_pattern"].get(month, 0) + 1
            
            if trend_type == "outcomes":
                terminated = len([c for c in cases if c.get("date_terminated")])
                ongoing = len(cases) - terminated
                resolution_rate = round((terminated / len(cases)) * 100) if cases else 0
                
                trends["trend_analysis"] = {
                    "case_resolution_rate": f"{resolution_rate}%",
                    "active_vs_closed": {"terminated": terminated, "ongoing": ongoing}
                }
                trends["key_trends"].extend([
                    "High case resolution rate" if terminated > ongoing else "Many cases still pending",
                    f"Peak filing activity in court: {max(trends['court_activity'], key=trends['court_activity'].get) if trends['court_activity'] else 'none'}"
                ])
                
            elif trend_type == "new-precedents":
                high_citation = [c for c in cases if (c.get("citation_count", 0) > 2)]
                trends["trend_analysis"] = {
                    "potentially_precedential": len(high_citation),
                    "emerging_authority": [c.get("case_name") for c in high_citation[:3]]
                }
                trends["key_trends"].extend([
                    f"{len(high_citation)} cases gaining precedential status" if high_citation else "No strong precedents emerging",
                    "Monitor these cases for legal developments"
                ])
            
            if trends["monthly_filing_pattern"]:
                most_active_months = sorted(trends["monthly_filing_pattern"].items(), key=lambda x: x[1], reverse=True)[:3]
                active_periods = [f"{month}: {count} cases" for month, count in most_active_months]
                trends["key_trends"].append(f"Most active filing periods: {', '.join(active_periods)}")
            
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(trends, indent=2))])
            
        except Exception as error:
            error_data = {
                "legal_area": legal_area,
                "time_period": time_period,
                "trend_type": trend_type,
                "error": f"Trend analysis failed: {str(error)}",
                "suggestion": "Try a different legal area or extend the time period for more data"
            }
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(error_data, indent=2))])

    def setup_handlers(self):
        """Set up MCP request handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="search_cases_by_problem",
                        description="Find relevant cases using LLM-generated search keywords. The LLM should extract legal keywords from the problem description and provide them for precise case law search.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "search_keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of legal search terms extracted by LLM from problem description (e.g., [\"breach of warranty\", \"consumer protection\", \"defective product\"])",
                                    "minItems": 1,
                                    "maxItems": 10
                                },
                                "problem_summary": {
                                    "type": "string",
                                    "description": "Brief summary of the legal problem for context (1-2 sentences)",
                                    "maxLength": 500
                                },
                                "case_type": {
                                    "type": "string",
                                    "description": "Type of consumer issue",
                                    "enum": ["consumer", "small-claims", "landlord-tenant", "contract", "warranty", "debt-collection", "auto", "employment"]
                                },
                                "date_range": {
                                    "type": "string",
                                    "description": "Time range preference for cases",
                                    "enum": ["recent-2years", "established-precedent", "all-time"],
                                    "default": "recent-2years"
                                },
                                "limit": {
                                    "type": "number",
                                    "description": "Number of cases to return (1-20)",
                                    "minimum": 1,
                                    "maximum": 20,
                                    "default": 10
                                }
                            },
                            "required": ["search_keywords"]
                        }
                    ),
                    Tool(
                        name="get_case_details",
                        description="Deep dive into specific case for precedent analysis with full legal reasoning",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "case_id": {
                                    "type": "string",
                                    "description": "Case ID from search results (cluster ID or docket ID)"
                                },
                                "include_full_text": {
                                    "type": "boolean",
                                    "description": "Include full opinion text (may be large)",
                                    "default": False
                                }
                            },
                            "required": ["case_id"]
                        }
                    ),
                    Tool(
                        name="find_similar_precedents",
                        description="Find cases with similar legal reasoning or outcomes to a reference case",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "reference_case_id": {
                                    "type": "string",
                                    "description": "ID of base case to find similar cases"
                                },
                                "legal_concepts": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Key legal concepts to match (e.g., [\"breach of warranty\", \"consumer protection\"])"
                                },
                                "citation_threshold": {
                                    "type": "number",
                                    "description": "Minimum citation count for authoritative cases",
                                    "default": 1
                                },
                                "limit": {
                                    "type": "number",
                                    "description": "Number of similar cases to return (1-15)",
                                    "minimum": 1,
                                    "maximum": 15,
                                    "default": 8
                                }
                            },
                            "required": ["reference_case_id"]
                        }
                    ),
                    Tool(
                        name="analyze_case_outcomes",
                        description="Analyze outcome patterns for similar cases to predict success likelihood",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "case_type": {
                                    "type": "string",
                                    "description": "Type of consumer issue to analyze"
                                },
                                "court_level": {
                                    "type": "string",
                                    "description": "Court level to analyze",
                                    "enum": ["trial", "appellate", "all"],
                                    "default": "all"
                                },
                                "date_range": {
                                    "type": "string",
                                    "description": "Time period for analysis",
                                    "enum": ["last-year", "last-2years", "last-5years"],
                                    "default": "last-2years"
                                }
                            },
                            "required": ["case_type"]
                        }
                    ),
                    Tool(
                        name="get_judge_analysis",
                        description="Analyze judge's typical rulings on similar issues for strategic positioning",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "judge_name": {
                                    "type": "string",
                                    "description": "Full name of the judge"
                                },
                                "case_type": {
                                    "type": "string",
                                    "description": "Area of law to analyze (e.g., consumer protection, small claims)"
                                },
                                "court": {
                                    "type": "string",
                                    "description": "Specific court identifier (optional)"
                                }
                            },
                            "required": ["judge_name", "case_type"]
                        }
                    ),
                    Tool(
                        name="validate_citations",
                        description="Verify and expand legal citations with related case discovery",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "citations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of citations to verify (e.g., [\"123 F.3d 456\", \"Smith v. Jones\"])"
                                },
                                "context_text": {
                                    "type": "string",
                                    "description": "Surrounding legal argument context for better validation"
                                }
                            },
                            "required": ["citations"]
                        }
                    ),
                    Tool(
                        name="get_procedural_requirements",
                        description="Find procedural rules and filing requirements for case type in NY courts",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "case_type": {
                                    "type": "string",
                                    "description": "Type of consumer complaint"
                                },
                                "court": {
                                    "type": "string",
                                    "description": "Target court for filing (NY court identifier)",
                                    "default": "ny-civ-ct"
                                },
                                "claim_amount": {
                                    "type": "number",
                                    "description": "Dollar amount of dispute (influences court jurisdiction)"
                                }
                            },
                            "required": ["case_type"]
                        }
                    ),
                    Tool(
                        name="track_legal_trends",
                        description="Identify recent trends in similar cases for strategic advantage",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "legal_area": {
                                    "type": "string",
                                    "description": "Area of law to analyze trends",
                                    "enum": ["consumer-protection", "small-claims", "landlord-tenant", "contract-disputes", "warranty-claims"]
                                },
                                "time_period": {
                                    "type": "string",
                                    "description": "Time period for trend analysis",
                                    "enum": ["last-6months", "last-year", "last-2years"],
                                    "default": "last-year"
                                },
                                "trend_type": {
                                    "type": "string",
                                    "description": "Type of trend to analyze",
                                    "enum": ["outcomes", "filing-patterns", "new-precedents", "settlement-rates"],
                                    "default": "outcomes"
                                }
                            },
                            "required": ["legal_area"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls."""
            try:
                if request.params.name == "search_cases_by_problem":
                    return await self.search_cases_by_problem(request.params.arguments or {})
                elif request.params.name == "get_case_details":
                    return await self.get_case_details(request.params.arguments or {})
                elif request.params.name == "find_similar_precedents":
                    return await self.find_similar_precedents(request.params.arguments or {})
                elif request.params.name == "analyze_case_outcomes":
                    return await self.analyze_case_outcomes(request.params.arguments or {})
                elif request.params.name == "get_judge_analysis":
                    return await self.get_judge_analysis(request.params.arguments or {})
                elif request.params.name == "validate_citations":
                    return await self.validate_citations(request.params.arguments or {})
                elif request.params.name == "get_procedural_requirements":
                    return await self.get_procedural_requirements(request.params.arguments or {})
                elif request.params.name == "track_legal_trends":
                    return await self.track_legal_trends(request.params.arguments or {})
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {request.params.name}")]
                    )
            except Exception as error:
                print(f"Error in tool {request.params.name}: {error}", file=sys.stderr)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error executing {request.params.name}: {str(error)}. Please check your parameters and try again.")]
                )

async def main():
    """Main server entry point."""
    async with CourtListenerMCPServer() as server:
        server.setup_handlers()
        
        async with stdio_server() as (read_stream, write_stream):
            print("CourtListener Legal Research MCP Server running...", file=sys.stderr)
            await server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="courtlistener-mcp",
                    server_version="2.0.0",
                    capabilities=server.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

if __name__ == "__main__":
    asyncio.run(main())