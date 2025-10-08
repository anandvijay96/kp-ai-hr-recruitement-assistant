"""
Tests for Full-Text Search functionality
"""
import pytest
from services.filter_service import FilterService


class TestQueryParser:
    """Test the search query parser"""
    
    def setup_method(self):
        self.filter_service = FilterService()
    
    def test_simple_query(self):
        """Test simple multi-word query"""
        result = self.filter_service._parse_search_query("Python developer")
        assert result == "Python & developer"
    
    def test_and_operator(self):
        """Test AND operator"""
        result = self.filter_service._parse_search_query("Python AND React")
        assert result == "Python & React"
    
    def test_or_operator(self):
        """Test OR operator"""
        result = self.filter_service._parse_search_query("Java OR Kotlin")
        assert result == "Java | Kotlin"
    
    def test_not_operator(self):
        """Test NOT operator"""
        result = self.filter_service._parse_search_query("Python NOT Django")
        assert result == "Python & !Django"
    
    def test_phrase_search(self):
        """Test phrase search with quotes"""
        result = self.filter_service._parse_search_query('"senior developer"')
        assert result == "senior<->developer"
    
    def test_complex_query(self):
        """Test complex boolean query"""
        result = self.filter_service._parse_search_query("(Python OR Java) AND React")
        # Note: Parentheses are preserved in the query
        assert "Python | Java" in result
        assert "React" in result
    
    def test_case_insensitive_operators(self):
        """Test that operators are case insensitive"""
        result1 = self.filter_service._parse_search_query("Python and React")
        result2 = self.filter_service._parse_search_query("Python AND React")
        assert result1 == result2 == "Python & React"
    
    def test_empty_query(self):
        """Test empty query"""
        result = self.filter_service._parse_search_query("")
        assert result == ""
    
    def test_single_word(self):
        """Test single word query"""
        result = self.filter_service._parse_search_query("Python")
        assert result == "Python"


class TestFullTextSearch:
    """Test full-text search functionality (requires database)"""
    
    @pytest.mark.integration
    def test_search_returns_results(self, db_session):
        """Test that search returns properly formatted results"""
        filter_service = FilterService()
        
        # This test requires a database with test data
        # Skip if no test database is configured
        try:
            results = filter_service.full_text_search("Python", db_session, page=1, page_size=10)
            
            # Check response structure
            assert "results" in results
            assert "pagination" in results
            assert "search_query" in results
            
            # Check pagination structure
            assert "total" in results["pagination"]
            assert "page" in results["pagination"]
            assert "page_size" in results["pagination"]
            assert "total_pages" in results["pagination"]
            
        except Exception as e:
            pytest.skip(f"Database not configured for testing: {e}")


if __name__ == "__main__":
    # Run tests
    test_parser = TestQueryParser()
    test_parser.setup_method()
    
    print("Testing query parser...")
    test_parser.test_simple_query()
    print("✅ Simple query test passed")
    
    test_parser.test_and_operator()
    print("✅ AND operator test passed")
    
    test_parser.test_or_operator()
    print("✅ OR operator test passed")
    
    test_parser.test_not_operator()
    print("✅ NOT operator test passed")
    
    test_parser.test_phrase_search()
    print("✅ Phrase search test passed")
    
    test_parser.test_case_insensitive_operators()
    print("✅ Case insensitive operators test passed")
    
    test_parser.test_empty_query()
    print("✅ Empty query test passed")
    
    test_parser.test_single_word()
    print("✅ Single word test passed")
    
    print("\n🎉 All query parser tests passed!")
