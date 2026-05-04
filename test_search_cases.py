#!/usr/bin/env python3
"""
Test script for the search-cases endpoint
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock
from typing import List

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

async def test_search_cases_endpoint():
    """Test the search cases endpoint logic"""
    # Import the function we want to test
    from app.api.v1.search_cases import search_cases
    from app.schemas.model_case import ModelCase
    from app.schemas.case_data import Cases
    
    # Mock database session and result
    mock_db = AsyncMock()
    mock_result = MagicMock()
    # Mock a single result row
    from datetime import datetime
    mock_dt = datetime(2022, 1, 1, 12, 0, 0)
    mock_rows = [
        (
            1,                                    # case_info_id (index 0)
            mock_dt,                              # activated_datetime (index 1)
            mock_dt,                              # created_datetime (index 2)
            None,                                 # trigger_at_datetime (index 3)
            mock_dt,                              # last_updated_datetime (index 4)
            mock_dt,                              # last_successful_datetime (index 5)
            mock_dt,                              # case_started_running_datetime (index 6)
            'Adams',                              # family_name (index 7)
            'Patch',                              # given1_name (index 8)
            None,                                 # given2_name (index 9)
            'Male',                               # gender_concept_name (index 10)
            1980,                                 # year_of_birth (index 11)
            5,                                    # month_of_birth (index 12)
            15,                                   # day_of_birth (index 13)
            '555-1234',                           # contact_point1 (index 14)
            '555-5678',                           # contact_point2 (index 15)
            None,                                 # contact_point3 (index 16)
            '123 Main St',                        # address_1 (index 17)
            'Apt 4B',                             # address_2 (index 18)
            'Torrance',                           # city (index 19)
            'GA',                                 # state (index 20)
            '30043',                              # zip (index 21)
            'RUNNING'                              # status (index 22)
        )
    ]
    mock_result.fetchall.return_value = mock_rows
    mock_db.execute.return_value = mock_result
    
    # Mock auth (not used in our logic but required by the function signature)
    mock_auth = {"user": "test"}
    
    try:
        # Test with valid parameters
        result = await search_cases(
            registry="syphilis",  # Assuming this is DATA_SCHEMA
            terms="Patch,Adams",
            fields="given1_name,family_name",
            db=mock_db,
            auth=mock_auth
        )
        
        # Verify the result
        print(f"DEBUG: Result type: {type(result)}")
        print(f"DEBUG: Result case type: {type(result.case)}")
        print(f"DEBUG: Result case length: {len(result.case)}")
        if len(result.case) > 0:
            print(f"DEBUG: First case type: {type(result.case[0])}")
            print(f"DEBUG: First case: {result.case[0]}")
            print(f"DEBUG: First case lastName: {result.case[0].lastName} (type: {type(result.case[0].lastName)})")
            print(f"DEBUG: First case firstName: {result.case[0].firstName} (type: {type(result.case[0].firstName)})")
        assert isinstance(result, Cases)
        assert isinstance(result.case, list)
        assert len(result.case) == 1
        assert isinstance(result.case[0], ModelCase)
        assert result.case[0].caseId == 1
        assert result.case[0].firstName == "Patch"
        assert result.case[0].lastName == "Adams"
        assert result.case[0].city == "Torrance"
        assert result.case[0].state == "GA"
        assert result.case[0].zip == "30043"
        assert result.case[0].street == "123 Main St Apt 4B"
        assert result.case[0].phone == "555-1234"
        assert result.count == 1
        
        print("✓ Search cases endpoint test passed: Valid parameters")
        
        # Test with no terms (should return all results)
        result = await search_cases(
            registry="syphilis",
            terms=None,
            fields=None,
            db=mock_db,
            auth=mock_auth
        )
        
        assert isinstance(result, Cases)
        assert len(result.case) == 1
        assert result.count == 1
        print("✓ Search cases endpoint test passed: No terms (returns all)")
        
        # Test with empty terms
        result = await search_cases(
            registry="syphilis",
            terms="",
            fields="",
            db=mock_db,
            auth=mock_auth
        )
        
        assert isinstance(result, Cases)
        assert len(result.case) == 1
        assert result.count == 1
        print("✓ Search cases endpoint test passed: Empty terms")
        
        # Test with invalid registry
        try:
            await search_cases(
                registry="invalid_schema",
                terms="test",
                db=mock_db,
                auth=mock_auth
            )
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 400
            assert e.detail["code"] == 400
            assert "invalid registry name" in e.detail["message"]
            print("✓ Search cases endpoint test passed: Invalid registry")
            
        return True
        
    except Exception as e:
        print(f"✗ Search cases endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    try:
        result = asyncio.run(test_search_cases_endpoint())
        if result:
            print("\n✓ All search cases endpoint tests passed!")
        else:
            print("\n✗ Some search cases endpoint tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Search cases endpoint test failed with exception: {e}")
        sys.exit(1)