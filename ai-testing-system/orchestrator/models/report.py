#!/usr/bin/env python3
"""
Report Data Models
Pydantic schemas for validation reports
"""

from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic.types import constr
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
from enum import Enum


class ReportFormat(str, Enum):
    JSON = "json"
    HTML = "html"
    PDF = "pdf"


class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssuesSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0


class ModelAnalysis(BaseModel):
    """Analysis from a single AI model"""
    model_name: str
    detected: bool
    confidence: float  # 0.0-1.0
    reason: str
    category: Optional[str] = None


class ConsensusIssue(BaseModel):
    """
    Issue flagged by consensus engine.
    
    P1-5: Strengthened validation with constrained types.
    """
    issue_id: Annotated[str, Field(min_length=1, max_length=100)]
    screenshot_url: Annotated[str, Field(max_length=500)]
    screenshot_key: Annotated[str, Field(max_length=500)]
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(min_length=1, max_length=5000)]
    severity: IssueSeverity
    triage_url: Optional[Annotated[str, Field(max_length=500)]] = None
    consensus_details: Annotated[List[ModelAnalysis], Field(max_length=10)] = []
    bounding_box: Optional[Dict[str, int]] = None  # {x, y, width, height}
    
    @field_validator('bounding_box')
    @classmethod
    def validate_bounding_box(cls, v):
        """Validate bounding box has required fields."""
        if v is not None:
            required = {'x', 'y', 'width', 'height'}
            if not all(k in v for k in required):
                raise ValueError(f"Bounding box must contain: {required}")
            # Validate positive dimensions
            if v['width'] <= 0 or v['height'] <= 0:
                raise ValueError("Bounding box dimensions must be positive")
        return v


class TestResult(BaseModel):
    """Individual test result from a capture"""
    capture_id: str
    event_type: str
    timestamp: str
    status: str  # passed, failed, flagged
    screenshot_url: str
    telemetry_url: str
    models_analyzed: List[str] = []
    issue: Optional[ConsensusIssue] = None


class CostBreakdown(BaseModel):
    """Cost tracking for the test run"""
    gemini_calls: int = 0
    gemini_cost_usd: float = 0.0
    gpt5_calls: int = 0
    gpt5_cost_usd: float = 0.0
    claude_calls: int = 0
    claude_cost_usd: float = 0.0
    storage_cost_usd: float = 0.0
    total_cost_usd: float = 0.0


class PerformanceMetrics(BaseModel):
    """Performance metrics for the test run"""
    total_processing_time_seconds: float
    average_time_per_screenshot_seconds: float
    model_latency_gemini_avg: Optional[float] = None
    model_latency_gpt5_avg: Optional[float] = None
    model_latency_claude_avg: Optional[float] = None
    consensus_evaluation_time_seconds: Optional[float] = None


class ReportMetadata(BaseModel):
    """
    Metadata about the test run and report.
    
    P1-5: Strengthened validation with constrained types.
    """
    report_id: Annotated[str, Field(pattern=r'^rep_[a-zA-Z0-9_]{8,20}$')]
    test_run_id: Annotated[str, Field(min_length=3, max_length=100)]
    game_title: Annotated[str, Field(min_length=1, max_length=200)]
    game_version: Optional[Annotated[str, Field(max_length=50)]] = None
    test_environment: Annotated[str, Field(min_length=1, max_length=200)]
    timestamp_generated_utc: datetime = Field(default_factory=datetime.utcnow)
    status: Annotated[str, Field(pattern=r'^(PASS|FAIL|WARNING)$')]
    ai_models: Annotated[List[str], Field(min_length=1, max_length=10)] = ["Gemini 2.5 Pro", "GPT-5", "Claude Sonnet 4.5"]
    consensus_logic: Annotated[str, Field(max_length=200)] = ">=2 models agree with >0.85 confidence"
    executor: Annotated[str, Field(max_length=100)] = "QA Orchestrator"
    
    @field_validator('timestamp_generated_utc')
    @classmethod
    def timestamp_not_future(cls, v):
        """Validate timestamp is not in the future."""
        if v > datetime.utcnow():
            raise ValueError('Timestamp cannot be in the future')
        return v


class ReportSummary(BaseModel):
    """High-level summary statistics"""
    total_screenshots: int
    screenshots_with_issues: int
    screenshots_passed: int
    pass_rate: float  # 0.0-100.0
    issues_by_severity: IssuesSummary
    total_analysis_time_seconds: float


class ReportData(BaseModel):
    """
    Complete report data structure.
    
    P1-5: Strengthened validation with constrained types.
    """
    metadata: ReportMetadata
    summary: ReportSummary
    consensus_issues: Annotated[List[ConsensusIssue], Field(max_length=10000)] = []
    test_results: Annotated[List[TestResult], Field(max_length=10000)] = []
    costs: CostBreakdown
    performance: PerformanceMetrics
    recommendations: Optional[Annotated[str, Field(max_length=5000)]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "report_id": "rep_abc123",
                    "test_run_id": "run_marvel_001",
                    "game_title": "Marvel Rivals",
                    "status": "FAIL"
                }
            }
        }


class Report(BaseModel):
    """Database model for report metadata"""
    id: str
    test_run_id: str
    game_title: str
    format: ReportFormat
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    file_size_bytes: int = 0
    status: str  # generating, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    data: Optional[ReportData] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "rep_abc123",
                "test_run_id": "run_xyz789",
                "format": "pdf",
                "s3_key": "reports/marvel-rivals/run_xyz789/report.pdf",
                "status": "completed"
            }
        }


class ReportGenerationRequest(BaseModel):
    """
    Request to generate a report.
    
    P1-5: Strengthened validation with constrained types.
    """
    test_run_id: Annotated[str, Field(min_length=3, max_length=100)]
    format: ReportFormat = ReportFormat.HTML
    include_screenshots: bool = True
    include_individual_model_analysis: bool = True
    
    @field_validator('test_run_id')
    @classmethod
    def validate_test_run_id(cls, v):
        """Validate test run ID format."""
        if not v or v.isspace():
            raise ValueError('test_run_id cannot be empty or whitespace')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_run_id": "run_marvel_001",
                "format": "html"
            }
        }

