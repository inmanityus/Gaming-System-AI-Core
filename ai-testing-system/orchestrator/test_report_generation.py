#!/usr/bin/env python3
"""
Test Report Generation Locally
Generates a sample report from Marvel Rivals data
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models.report import (
    ReportData, ReportMetadata, ReportSummary, IssuesSummary,
    CostBreakdown, PerformanceMetrics, ConsensusIssue, ModelAnalysis,
    ReportFormat
)
from services.report_generator import ReportGenerator
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def create_sample_marvel_rivals_report() -> ReportData:
    """Create sample report data from Marvel Rivals test."""
    
    # Sample consensus issues based on Marvel Rivals testing
    issues = [
        ConsensusIssue(
            issue_id="MR-001",
            screenshot_url="https://s3.amazonaws.com/body-broker-qa-captures/marvel-rivals/Baseline_0005.png",
            screenshot_key="marvel-rivals/Baseline_0005.png",
            title="UI Text Contrast Issue in Main Menu",
            description="The ability description text in the main menu lacks sufficient contrast against the background, making it difficult to read.",
            severity="medium",
            consensus_details=[
                ModelAnalysis(
                    model_name="Gemini 2.5 Pro",
                    detected=True,
                    confidence=0.92,
                    reason="UI text has insufficient contrast ratio (2.8:1, should be 4.5:1 minimum)",
                    category="ux"
                ),
                ModelAnalysis(
                    model_name="GPT-5",
                    detected=True,
                    confidence=0.88,
                    reason="Identified text readability issues in ability descriptions",
                    category="ux"
                ),
                ModelAnalysis(
                    model_name="Claude Sonnet 4.5",
                    detected=False,
                    confidence=0.41,
                    reason="Contrast appears acceptable in this context",
                    category="ux"
                )
            ]
        ),
        ConsensusIssue(
            issue_id="MR-002",
            screenshot_url="https://s3.amazonaws.com/body-broker-qa-captures/marvel-rivals/OnPlayerDamage_0003.png",
            screenshot_key="marvel-rivals/OnPlayerDamage_0003.png",
            title="Character Model Overlap with UI Elements",
            description="The player health bar in the top-left corner is partially obscured by the character selection portrait during combat.",
            severity="medium",
            consensus_details=[
                ModelAnalysis(
                    model_name="Gemini 2.5 Pro",
                    detected=True,
                    confidence=0.95,
                    reason="UI element overlap detected at bounding box [10,20,150,50]",
                    category="ux"
                ),
                ModelAnalysis(
                    model_name="GPT-5",
                    detected=True,
                    confidence=0.89,
                    reason="Identified overlapping graphical elements affecting gameplay visibility",
                    category="ux"
                ),
                ModelAnalysis(
                    model_name="Claude Sonnet 4.5",
                    detected=True,
                    confidence=0.87,
                    reason="Health bar obstruction confirmed, impacts player awareness",
                    category="ux"
                )
            ]
        ),
        ConsensusIssue(
            issue_id="MR-003",
            screenshot_url="https://s3.amazonaws.com/body-broker-qa-captures/marvel-rivals/Baseline_0008.png",
            screenshot_key="marvel-rivals/Baseline_0008.png",
            title="Menu Text Overflow on Narrow Displays",
            description="Character ability names overflow their containers when UI scaling is set to 125%, causing text truncation.",
            severity="medium",
            consensus_details=[
                ModelAnalysis(
                    model_name="Gemini 2.5 Pro",
                    detected=True,
                    confidence=0.90,
                    reason="Text overflow visible in ability selection menu",
                    category="ux"
                ),
                ModelAnalysis(
                    model_name="GPT-5",
                    detected=True,
                    confidence=0.86,
                    reason="Text container insufficient for scaled text",
                    category="ux"
                ),
                ModelAnalysis(
                    model_name="Claude Sonnet 4.5",
                    detected=False,
                    confidence=0.30,
                    reason="No significant text overflow detected",
                    category="ux"
                )
            ]
        )
    ]
    
    # Create report data
    report_data = ReportData(
        metadata=ReportMetadata(
            report_id="rep_marvel_001",
            test_run_id="run_marvel_rivals_2025_11_12",
            game_title="Marvel Rivals",
            game_version="0.8.1-beta",
            test_environment="PC - High Settings (1920x1080)",
            timestamp_generated_utc=datetime.utcnow(),
            status="FAIL"
        ),
        summary=ReportSummary(
            total_screenshots=10,
            screenshots_with_issues=3,
            screenshots_passed=7,
            pass_rate=70.0,
            issues_by_severity=IssuesSummary(
                critical=0,
                high=0,
                medium=3,
                low=0,
                total=3
            ),
            total_analysis_time_seconds=120.5
        ),
        consensus_issues=issues,
        test_results=[],  # Would include full test results in production
        costs=CostBreakdown(
            gemini_calls=10,
            gemini_cost_usd=0.015,
            gpt5_calls=10,
            gpt5_cost_usd=0.020,
            claude_calls=10,
            claude_cost_usd=0.018,
            storage_cost_usd=0.001,
            total_cost_usd=0.054
        ),
        performance=PerformanceMetrics(
            total_processing_time_seconds=120.5,
            average_time_per_screenshot_seconds=12.05,
            model_latency_gemini_avg=1.2,
            model_latency_gpt5_avg=1.5,
            model_latency_claude_avg=1.1,
            consensus_evaluation_time_seconds=0.5
        ),
        recommendations="Three medium-priority UI/UX issues detected in Marvel Rivals. All issues relate to text visibility and element positioning. Recommend: 1) Increase text contrast ratios to meet WCAG AA standards (4.5:1 minimum), 2) Adjust UI element layering to prevent health bar obstruction, 3) Implement responsive text containers with ellipsis for scaled displays."
    )
    
    return report_data


async def main():
    """Generate sample reports in all formats."""
    
    logger.info("=" * 70)
    logger.info("SAMPLE REPORT GENERATION - Marvel Rivals Test Data")
    logger.info("=" * 70)
    
    # Create sample data
    logger.info("Creating sample Marvel Rivals report data...")
    report_data = create_sample_marvel_rivals_report()
    
    logger.info(f"Report ID: {report_data.metadata.report_id}")
    logger.info(f"Test Run: {report_data.metadata.test_run_id}")
    logger.info(f"Game: {report_data.metadata.game_title}")
    logger.info(f"Screenshots: {report_data.summary.total_screenshots}")
    logger.info(f"Issues Found: {report_data.summary.screenshots_with_issues}")
    logger.info(f"Pass Rate: {report_data.summary.pass_rate}%")
    
    # Initialize generator
    generator = ReportGenerator()
    
    # Output directory
    output_dir = Path(__file__).parent / "sample_reports"
    output_dir.mkdir(exist_ok=True)
    
    logger.info(f"Output directory: {output_dir}")
    
    # Generate JSON
    logger.info("\nGenerating JSON report...")
    try:
        json_content = generator.generate_json(report_data)
        json_path = output_dir / "marvel-rivals-report.json"
        json_path.write_text(json_content, encoding='utf-8')
        logger.info(f"✅ JSON report saved: {json_path} ({len(json_content)} bytes)")
    except Exception as e:
        logger.error(f"❌ JSON generation failed: {e}", exc_info=True)
    
    # Generate HTML
    logger.info("\nGenerating HTML report...")
    try:
        html_content = generator.generate_html(report_data)
        html_path = output_dir / "marvel-rivals-report.html"
        html_path.write_text(html_content, encoding='utf-8')
        logger.info(f"✅ HTML report saved: {html_path} ({len(html_content)} bytes)")
    except Exception as e:
        logger.error(f"❌ HTML generation failed: {e}", exc_info=True)
    
    # Generate PDF (skip on Windows - WeasyPrint requires GTK libraries)
    logger.info("\nGenerating PDF report...")
    try:
        import platform
        if platform.system() == 'Windows':
            logger.warning("⚠️  PDF generation skipped on Windows (requires GTK libraries)")
            logger.warning("    PDF generation will work in Linux Docker containers (production)")
        else:
            pdf_bytes = await generator.generate_pdf(report_data)
            pdf_path = output_dir / "marvel-rivals-report.pdf"
            pdf_path.write_bytes(pdf_bytes)
            logger.info(f"✅ PDF report saved: {pdf_path} ({len(pdf_bytes)} bytes)")
    except Exception as e:
        logger.error(f"❌ PDF generation failed: {e}", exc_info=True)
        logger.info("    Note: This is expected on Windows without GTK. Works in Docker.")
    
    # Cleanup
    await generator.cleanup()
    
    logger.info("\n" + "=" * 70)
    logger.info("SAMPLE REPORT GENERATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nReports saved to: {output_dir.absolute()}")
    logger.info("\nFiles generated:")
    for file in output_dir.iterdir():
        logger.info(f"  - {file.name} ({file.stat().st_size:,} bytes)")


if __name__ == "__main__":
    import platform
    
    # Fix for Windows event loop
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())

