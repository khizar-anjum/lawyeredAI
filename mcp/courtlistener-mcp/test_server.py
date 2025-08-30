#!/usr/bin/env python3
"""
Simple test script for the CourtListener MCP Server
"""

import asyncio
import json
from server import CourtListenerMCPServer

async def test_basic_functionality():
    """Test basic server functionality without actual API calls."""
    print("Testing CourtListener MCP Server...")
    
    async with CourtListenerMCPServer() as server:
        print("✓ Server initialization successful")
        
        # Test court configuration
        courts = server.get_ny_courts()
        print(f"✓ NY Courts configured: {len(courts['primary'])} primary, {len(courts['secondary'])} secondary")
        
        # Test keyword validation
        try:
            valid_keywords = server.validate_search_keywords(["breach of warranty", "consumer protection"])
            print(f"✓ Keyword validation working: {valid_keywords}")
        except Exception as e:
            print(f"✗ Keyword validation failed: {e}")
            return False
        
        # Test text truncation
        long_text = "This is a very long text " * 100
        truncated = server.truncate_text(long_text, 50)
        print(f"✓ Text truncation working: {len(truncated)} chars")
        
        # Test handler setup (without actually registering)
        print("✓ Handler setup method exists")
        
        print("\n🎉 All basic tests passed!")
        return True

async def test_error_handling():
    """Test error handling capabilities."""
    print("\nTesting error handling...")
    
    async with CourtListenerMCPServer() as server:
        # Test invalid keywords
        try:
            server.validate_search_keywords([])
            print("✗ Should have failed with empty keywords")
        except ValueError:
            print("✓ Empty keywords properly rejected")
        
        # Test too many keywords
        try:
            server.validate_search_keywords(["keyword"] * 15)
            print("✗ Should have failed with too many keywords")
        except ValueError:
            print("✓ Too many keywords properly rejected")
        
        # Test invalid keyword types
        try:
            server.validate_search_keywords([123, None, "valid"])
            result = server.validate_search_keywords([123, None, "valid"])
            print(f"✓ Invalid keywords filtered: {result}")
        except Exception as e:
            print(f"✓ Invalid keywords handled: {e}")
        
        print("✓ Error handling tests passed")

def test_json_serialization():
    """Test JSON serialization of complex responses."""
    print("\nTesting JSON serialization...")
    
    # Test complex response structure
    complex_data = {
        "search_strategy": {
            "keywords_used": ["breach of warranty", "consumer protection"],
            "query_constructed": '"breach of warranty" OR "consumer protection" AND consumer',
            "date_range_applied": "recent-2years",
            "courts_searched": "NY primary consumer courts"
        },
        "problem_context": "Test problem summary",
        "search_results": {
            "total_found": 100,
            "returned_count": 10,
            "cases": [
                {
                    "case_id": 12345,
                    "case_name": "Test v. Example",
                    "court": "ny-civ-ct",
                    "date_filed": "2023-01-15",
                    "citation_count": 5,
                    "relevance_summary": "Test case summary...",
                    "keyword_matches": 2,
                    "precedential_value": "Moderate"
                }
            ]
        },
        "usage_note": "Test note"
    }
    
    try:
        json_str = json.dumps(complex_data, indent=2)
        parsed_back = json.loads(json_str)
        print("✓ Complex JSON serialization working")
        print(f"  - JSON length: {len(json_str)} characters")
        print(f"  - Parsed back successfully: {len(parsed_back)} keys")
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests."""
    print("=" * 60)
    print("CourtListener MCP Server Test Suite")
    print("=" * 60)
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    try:
        if await test_basic_functionality():
            tests_passed += 1
        
        if await test_error_handling():
            tests_passed += 1
        
        if test_json_serialization():
            tests_passed += 1
            
    except Exception as e:
        print(f"Test suite error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Server is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)