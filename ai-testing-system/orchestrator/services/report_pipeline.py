#!/usr/bin/env python3
"""
Report Generation Pipeline
Orchestrates the complete report generation process
"""

from typing import Dict, List, Any, Protocol
from abc import ABC, abstractmethod
import logging
import uuid
from datetime import datetime

from models.report import (
    ReportData, ReportMetadata, ReportSummary, IssuesSummary,
    CostBreakdown, PerformanceMetrics, ConsensusIssue, TestResult,
    Report, ReportFormat, ModelAnalysis
)
from services.report_generator import ReportGenerator
from services.storage_service import S3StorageService

logger = logging.getLogger(__name__)


class ReportStep(ABC):
    """Base class for pipeline steps"""
    
    @abstractmethod
    async def process(self, context: dict) -> dict:
        """Process this step and return updated context"""
        pass


class DataCollectionStep(ReportStep):
    """Collect test run data from orchestrator storage"""
    
    def __init__(self, captures_db: dict, consensus_results_db: list, analysis_results_db: dict):
        self.captures_db = captures_db
        self.consensus_results_db = consensus_results_db
        self.analysis_results_db = analysis_results_db
    
    async def process(self, context: dict) -> dict:
        logger.info(f"Collecting data for test run: {context.get('game_title', 'Unknown')}")
        
        # Get all captures for this test run
        all_captures = list(self.captures_db.values())
        
        # Filter captures for this test run (if test_run_id is specified)
        test_run_id = context.get('test_run_id')
        game_title = context.get('game_title', 'Unknown Game')
        
        # For now, we'll use all captures (in production, filter by test_run_id)
        captures = all_captures
        
        # Get consensus results
        consensus_issues = [c for c in self.consensus_results_db if c.get('issue_flagged', False)]
        
        context['raw_captures'] = captures
        context['raw_consensus'] = consensus_issues
        context['raw_analysis'] = self.analysis_results_db
        
        logger.info(f"Collected {len(captures)} captures, {len(consensus_issues)} consensus issues")
        return context


class DataTransformationStep(ReportStep):
    """Transform raw data into report structure"""
    
    async def process(self, context: dict) -> dict:
        logger.info("Transforming data into report structure")
        
        raw_captures = context['raw_captures']
        raw_consensus = context['raw_consensus']
        raw_analysis = context['raw_analysis']
        
        # Calculate summary statistics
        total_screenshots = len(raw_captures)
        screenshots_with_issues = len(raw_consensus)
        screenshots_passed = total_screenshots - screenshots_with_issues
        pass_rate = (screenshots_passed / total_screenshots * 100) if total_screenshots > 0 else 0
        
        # Analyze issues by severity
        issues_by_severity = self._count_issues_by_severity(raw_consensus)
        
        # Transform consensus issues
        consensus_issues = self._transform_consensus_issues(raw_consensus, raw_analysis)
        
        # Transform test results
        test_results = self._transform_test_results(raw_captures, raw_consensus)
        
        # Calculate costs
        costs = self._calculate_costs(raw_analysis)
        
        # Calculate performance metrics
        performance = self._calculate_performance(raw_captures, raw_analysis)
        
        # Generate AI recommendations
        recommendations = self._generate_recommendations(consensus_issues, issues_by_severity)
        
        # Create report data
        report_data = ReportData(
            metadata=ReportMetadata(
                report_id=context['report_id'],
                test_run_id=context.get('test_run_id', f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
                game_title=context.get('game_title', 'Unknown Game'),
                game_version=context.get('game_version'),
                test_environment=context.get('test_environment', 'Unknown Environment'),
                timestamp_generated_utc=datetime.utcnow(),
                status=self._determine_status(pass_rate, issues_by_severity)
            ),
            summary=ReportSummary(
                total_screenshots=total_screenshots,
                screenshots_with_issues=screenshots_with_issues,
                screenshots_passed=screenshots_passed,
                pass_rate=pass_rate,
                issues_by_severity=issues_by_severity,
                total_analysis_time_seconds=performance.total_processing_time_seconds
            ),
            consensus_issues=consensus_issues,
            test_results=test_results,
            costs=costs,
            performance=performance,
            recommendations=recommendations
        )
        
        context['report_data'] = report_data
        logger.info(f"Data transformation complete: {total_screenshots} screenshots, {screenshots_with_issues} issues")
        return context
    
    def _count_issues_by_severity(self, consensus_issues: List[dict]) -> IssuesSummary:
        """Count issues by severity"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for issue in consensus_issues:
            severity = issue.get('category', 'medium')  # Use category as severity for now
            if severity in counts:
                counts[severity] += 1
        
        return IssuesSummary(
            critical=counts['critical'],
            high=counts['high'],
            medium=counts['medium'],
            low=counts['low'],
            total=len(consensus_issues)
        )
    
    def _transform_consensus_issues(self, consensus_issues: List[dict], analysis_results: dict) -> List[ConsensusIssue]:
        """Transform consensus issues into report format"""
        transformed = []
        
        for idx, issue in enumerate(consensus_issues):
            capture_id = issue.get('capture_id', '')
            
            # Get analysis details for this capture
            analyses = analysis_results.get(capture_id, [])
            consensus_details = []
            
            for analysis in analyses:
                consensus_details.append(ModelAnalysis(
                    model_name=analysis.get('model_name', 'Unknown'),
                    detected=analysis.get('is_issue', False),
                    confidence=analysis.get('confidence', 0.0),
                    reason=analysis.get('description', 'No details provided'),
                    category=analysis.get('category')
                ))
            
            transformed.append(ConsensusIssue(
                issue_id=f"issue_{idx+1:03d}",
                screenshot_url=f"https://s3.amazonaws.com/body-broker-qa-captures/{capture_id}.png",
                screenshot_key=f"{capture_id}.png",
                title=issue.get('description', 'Issue Detected')[:100],
                description=issue.get('description', 'No description available'),
                severity=self._determine_severity(issue.get('average_confidence', 0.5)),
                consensus_details=consensus_details
            ))
        
        return transformed
    
    def _determine_severity(self, confidence: float) -> str:
        """Determine severity based on confidence"""
        if confidence >= 0.95:
            return 'critical'
        elif confidence >= 0.90:
            return 'high'
        elif confidence >= 0.85:
            return 'medium'
        else:
            return 'low'
    
    def _transform_test_results(self, captures: List[dict], consensus_issues: List[dict]) -> List[TestResult]:
        """Transform captures into test results"""
        results = []
        issue_capture_ids = {issue['capture_id'] for issue in consensus_issues}
        
        for capture in captures:
            capture_id = capture.get('capture_id', '')
            results.append(TestResult(
                capture_id=capture_id,
                event_type=capture.get('event_type', 'Unknown'),
                timestamp=capture.get('timestamp', datetime.utcnow().isoformat()),
                status='flagged' if capture_id in issue_capture_ids else 'passed',
                screenshot_url=f"https://s3.amazonaws.com/body-broker-qa-captures/{capture.get('screenshot_key', '')}",
                telemetry_url=f"https://s3.amazonaws.com/body-broker-qa-captures/{capture.get('telemetry_key', '')}",
                models_analyzed=['Gemini 2.5 Pro', 'GPT-5', 'Claude Sonnet 4.5']
            ))
        
        return results
    
    def _calculate_costs(self, analysis_results: dict) -> CostBreakdown:
        """Calculate costs for the test run"""
        # Estimate costs based on analysis calls
        total_analyses = sum(len(analyses) for analyses in analysis_results.values())
        
        # Rough cost estimates (adjust based on actual pricing)
        cost_per_analysis = 0.01  # $0.01 per analysis call
        
        return CostBreakdown(
            gemini_calls=total_analyses // 3,
            gemini_cost_usd=total_analyses / 3 * cost_per_analysis,
            gpt5_calls=total_analyses // 3,
            gpt5_cost_usd=total_analyses / 3 * cost_per_analysis,
            claude_calls=total_analyses // 3,
            claude_cost_usd=total_analyses / 3 * cost_per_analysis,
            storage_cost_usd=0.001,
            total_cost_usd=total_analyses * cost_per_analysis + 0.001
        )
    
    def _calculate_performance(self, captures: List[dict], analysis_results: dict) -> PerformanceMetrics:
        """Calculate performance metrics"""
        total_captures = len(captures)
        
        # Estimate processing time (adjust based on actual timing data)
        avg_time_per_screenshot = 12.0  # seconds
        total_time = total_captures * avg_time_per_screenshot
        
        return PerformanceMetrics(
            total_processing_time_seconds=total_time,
            average_time_per_screenshot_seconds=avg_time_per_screenshot,
            model_latency_gemini_avg=1.2,
            model_latency_gpt5_avg=1.5,
            model_latency_claude_avg=1.1,
            consensus_evaluation_time_seconds=0.5
        )
    
    def _determine_status(self, pass_rate: float, issues: IssuesSummary) -> str:
        """Determine overall test status"""
        if issues.critical > 0:
            return 'FAIL'
        elif issues.high > 0 or pass_rate < 80:
            return 'WARNING'
        else:
            return 'PASS'
    
    def _generate_recommendations(self, issues: List[ConsensusIssue], summary: IssuesSummary) -> str:
        """Generate AI recommendations based on issues"""
        if summary.total == 0:
            return "All screenshots passed AI analysis. No issues detected. System is performing well."
        
        recs = []
        
        if summary.critical > 0:
            recs.append(f"{summary.critical} critical issue(s) require immediate attention.")
        
        if summary.high > 0:
            recs.append(f"{summary.high} high-priority issue(s) should be reviewed by the development team.")
        
        # Identify common patterns
        categories = {}
        for issue in issues:
            for analysis in issue.consensus_details:
                if analysis.category:
                    categories[analysis.category] = categories.get(analysis.category, 0) + 1
        
        if categories:
            top_category = max(categories, key=categories.get)
            recs.append(f"Most common issue category: {top_category}. Consider focused testing in this area.")
        
        return " ".join(recs) if recs else "Review flagged issues for potential improvements."


class ReportGenerationStep(ReportStep):
    """Generate report in requested format"""
    
    def __init__(self, generator: ReportGenerator):
        self.generator = generator
    
    async def process(self, context: dict) -> dict:
        report_format = context['format']
        logger.info(f"Generating {report_format} report")
        
        report_data = context['report_data']
        
        # CRITICAL FIX: Make this async-aware for PDF generation
        content = await self.generator.generate_report(report_data, report_format)
        
        # Determine content type
        content_type_map = {
            ReportFormat.JSON: 'application/json',
            ReportFormat.HTML: 'text/html',
            ReportFormat.PDF: 'application/pdf'
        }
        
        context['content'] = content
        context['content_type'] = content_type_map[report_format]
        context['file_size'] = len(content)
        
        logger.info(f"Report generated: {context['file_size']} bytes")
        return context


class StorageStep(ReportStep):
    """Store report to S3"""
    
    def __init__(self, storage_service: S3StorageService):
        self.storage_service = storage_service
    
    async def process(self, context: dict) -> dict:
        logger.info("Storing report to S3")
        
        report_id = context['report_id']
        game_title = context.get('game_title', 'unknown').lower().replace(' ', '-')
        test_run_id = context.get('test_run_id', 'unknown')
        report_format = context['format']
        content = context['content']
        content_type = context['content_type']
        
        # Generate S3 key with structured path
        timestamp = datetime.utcnow().strftime('%Y/%m')
        s3_key = f"reports/{game_title}/{test_run_id}/{report_id}.{report_format.value}"
        
        # Upload to S3
        s3_url = await self.storage_service.upload(s3_key, content, content_type)
        
        context['s3_key'] = s3_key
        context['s3_url'] = s3_url
        
        logger.info(f"Report stored: {s3_url}")
        return context


class ReportPipeline:
    """Orchestrates report generation pipeline"""
    
    def __init__(self, steps: List[ReportStep]):
        self.steps = steps
    
    async def execute(self, initial_context: dict) -> dict:
        """Execute all steps in sequence"""
        context = initial_context.copy()
        
        logger.info(f"Starting report pipeline with {len(self.steps)} steps")
        
        for idx, step in enumerate(self.steps, 1):
            try:
                logger.info(f"Executing step {idx}/{len(self.steps)}: {step.__class__.__name__}")
                context = await step.process(context)
            except Exception as e:
                logger.error(f"Pipeline step failed: {step.__class__.__name__}: {e}", exc_info=True)
                context['error'] = str(e)
                context['failed_step'] = step.__class__.__name__
                raise
        
        logger.info("Report pipeline completed successfully")
        return context


def create_report_pipeline(
    captures_db: dict,
    consensus_results_db: list,
    analysis_results_db: dict,
    storage_service: S3StorageService
) -> ReportPipeline:
    """Create configured report pipeline"""
    
    generator = ReportGenerator()
    
    steps = [
        DataCollectionStep(captures_db, consensus_results_db, analysis_results_db),
        DataTransformationStep(),
        ReportGenerationStep(generator),
        StorageStep(storage_service)
    ]
    
    return ReportPipeline(steps)

