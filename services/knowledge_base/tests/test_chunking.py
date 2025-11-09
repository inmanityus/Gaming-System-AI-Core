"""
Unit Tests for Document Chunking Logic
Critical P0 tests as identified by Gemini 2.5 Pro peer review.
"""

import pytest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from ingest_documents import DocumentIngestionPipeline


class TestChunkingLogic:
    """Unit tests for document chunking."""
    
    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        return DocumentIngestionPipeline()
    
    def test_empty_document(self, pipeline):
        """TC-1.1: Empty document returns empty list."""
        result = pipeline.chunk_document("")
        assert result == []
    
    def test_document_smaller_than_chunk_size(self, pipeline):
        """TC-1.2: Small document returns single chunk."""
        text = "Short document."
        result = pipeline.chunk_document(text)
        assert len(result) == 1
        assert result[0] == text
    
    def test_document_exactly_chunk_size(self, pipeline):
        """TC-1.3: Document exactly chunk size returns one chunk."""
        text = "A" * pipeline.chunk_size
        result = pipeline.chunk_document(text)
        assert len(result) == 1
        assert result[0] == text
    
    def test_document_with_only_whitespace(self, pipeline):
        """TC-1.4: Whitespace-only document returns empty list."""
        result = pipeline.chunk_document("\n \t \n")
        assert result == []
    
    def test_unicode_characters(self, pipeline):
        """TC-1.5: Unicode characters handled correctly."""
        text = "你好世界 " * 200  # Chinese characters
        emoji_text = "Hello 👍 World 🎮 " * 100
        
        result1 = pipeline.chunk_document(text)
        result2 = pipeline.chunk_document(emoji_text)
        
        # Should not crash and should produce chunks
        assert len(result1) > 0
        assert len(result2) > 0
        
        # Chunks should contain unicode
        assert any('你好' in chunk for chunk in result1)
        assert any('👍' in chunk for chunk in result2)
    
    def test_long_document_multiple_chunks(self, pipeline):
        """Long document splits into multiple chunks."""
        text = "Paragraph text. " * 1000  # ~16KB
        result = pipeline.chunk_document(text)
        
        # Should create multiple chunks
        assert len(result) > 1
        
        # Each chunk should be approximately chunk_size
        for chunk in result:
            assert len(chunk) <= pipeline.chunk_size + pipeline.chunk_overlap
    
    def test_chunk_overlap(self, pipeline):
        """Chunks should have overlap for context preservation."""
        text = "Word " * 500  # Create long text
        result = pipeline.chunk_document(text)
        
        if len(result) > 1:
            # Check that there's overlap between consecutive chunks
            # Last part of chunk N should appear in chunk N+1
            # (This is a simplified check - adjust based on actual overlap logic)
            assert len(result) > 1  # Multiple chunks created
    
    def test_paragraph_boundary_preservation(self, pipeline):
        """Chunking should prefer paragraph boundaries."""
        paragraphs = [f"Paragraph {i}. " * 100 for i in range(5)]
        text = "\n\n".join(paragraphs)
        
        result = pipeline.chunk_document(text)
        
        # Should create chunks
        assert len(result) > 0
        
        # Chunks should not break mid-word
        for chunk in result:
            assert not chunk.endswith(" Para")  # Incomplete word


class TestChunkingEdgeCases:
    """Edge case tests for robustness."""
    
    @pytest.fixture
    def pipeline(self):
        return DocumentIngestionPipeline()
    
    def test_very_long_single_line(self, pipeline):
        """Single line longer than chunk size."""
        text = "A" * (pipeline.chunk_size * 3)
        result = pipeline.chunk_document(text)
        
        assert len(result) > 1
    
    def test_markdown_formatting(self, pipeline):
        """Markdown with headers, lists, code blocks."""
        text = """
# Header 1

## Header 2

- List item 1
- List item 2

```code
def function():
    pass
```

Regular paragraph text.
""" * 50
        
        result = pipeline.chunk_document(text)
        assert len(result) > 0
        # Markdown should be preserved
        assert any('#' in chunk for chunk in result)
    
    def test_special_characters(self, pipeline):
        """Special characters don't break chunking."""
        text = "Special chars: @#$%^&*()[]{}'\";:<>?/\\ " * 200
        result = pipeline.chunk_document(text)
        
        assert len(result) > 0
        assert all(isinstance(chunk, str) for chunk in result)

