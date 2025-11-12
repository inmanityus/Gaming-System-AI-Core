#!/usr/bin/env python3
"""
Report Generator Service
Generates JSON, HTML, and PDF reports from test run data
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ProcessPoolExecutor
import platform

from models.report import ReportData, ReportFormat

logger = logging.getLogger(__name__)

# Conditional WeasyPrint import (only works on Linux or Windows with GTK)
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.warning(f"WeasyPrint not available: {e}")
    logger.warning("PDF generation will be disabled. Install GTK libraries or run in Linux Docker.")


def _generate_pdf_sync(html_content: str, css_path: str = None) -> bytes:
    """
    Generate PDF in separate process to avoid blocking event loop.
    This function MUST be at module level for ProcessPoolExecutor pickling.
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("WeasyPrint is not available. PDF generation requires GTK libraries.")
    
    from weasyprint import HTML, CSS
    from pathlib import Path
    
    try:
        if css_path and Path(css_path).exists():
            css = CSS(filename=css_path)
            return HTML(string=html_content).write_pdf(stylesheets=[css])
        else:
            return HTML(string=html_content).write_pdf()
    except Exception as e:
        # Log error and re-raise for proper handling
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"PDF generation failed in worker process: {e}", exc_info=True)
        raise


class ReportGenerator:
    """Generates reports in multiple formats"""
    
    def __init__(self, templates_dir: str = None, max_pdf_workers: int = 2):
        if templates_dir is None:
            # Default to templates folder relative to this file
            templates_dir = Path(__file__).parent.parent / "templates" / "reports"
        
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment with strict auto-escaping
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['json_pretty'] = lambda x: json.dumps(x, indent=2)
        self.env.filters['format_datetime'] = self._format_datetime
        self.env.filters['format_percentage'] = self._format_percentage
        
        # Initialize ProcessPoolExecutor for PDF generation (only if WeasyPrint available)
        # This prevents blocking the event loop with CPU-intensive PDF rendering
        if WEASYPRINT_AVAILABLE:
            self._pdf_executor = ProcessPoolExecutor(
                max_workers=max_pdf_workers,
                mp_context=None  # Use default (fork on Unix, spawn on Windows)
            )
            self._is_closed = False
            logger.info(f"PDF executor initialized with {max_pdf_workers} workers")
        else:
            self._pdf_executor = None
            self._is_closed = True
            logger.warning("PDF generation disabled (WeasyPrint not available)")
        
        logger.info(f"Report generator initialized with templates dir: {self.templates_dir}")
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display"""
        return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def _format_percentage(self, value: float) -> str:
        """Format percentage for display"""
        return f"{value:.1f}%"
    
    def generate_json(self, report_data: ReportData) -> str:
        """Generate JSON report"""
        logger.info(f"Generating JSON report for run: {report_data.metadata.test_run_id}")
        
        # Convert Pydantic model to dict and serialize
        data_dict = report_data.dict()
        
        # Custom JSON encoder for datetime
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        json_str = json.dumps(data_dict, indent=2, default=json_serializer)
        logger.info(f"JSON report generated: {len(json_str)} bytes")
        return json_str
    
    def generate_html(self, report_data: ReportData) -> str:
        """Generate HTML report"""
        logger.info(f"Generating HTML report for run: {report_data.metadata.test_run_id}")
        
        try:
            template = self.env.get_template('report.html')
            html_content = template.render(
                report=report_data.dict(),
                generated_at=datetime.utcnow(),
                report_data=report_data  # Also pass the Pydantic model for type safety
            )
            
            logger.info(f"HTML report generated: {len(html_content)} bytes")
            return html_content
            
        except Exception as e:
            logger.error(f"HTML generation failed: {e}", exc_info=True)
            raise
    
    async def generate_pdf(self, report_data: ReportData) -> bytes:
        """
        Generate PDF from HTML using separate process to avoid blocking event loop.
        
        CRITICAL FIX (P0-1): WeasyPrint is CPU-intensive and synchronous.
        Running it in the main event loop blocks ALL API requests.
        This implementation uses ProcessPoolExecutor to run PDF generation
        in a separate process, keeping the API responsive.
        
        Note: Requires WeasyPrint with GTK libraries (Linux) or GTK for Windows.
        """
        logger.info(f"Generating PDF report for run: {report_data.metadata.test_run_id}")
        
        if not WEASYPRINT_AVAILABLE:
            raise RuntimeError(
                "PDF generation unavailable: WeasyPrint requires GTK libraries. "
                "Install GTK or run in Linux Docker container."
            )
        
        if self._is_closed or self._pdf_executor is None:
            raise RuntimeError("ReportGenerator has been closed or PDF executor unavailable")
        
        try:
            # Generate HTML first (fast, no blocking)
            html_content = self.generate_html(report_data)
            
            # Prepare CSS path
            css_path = self.templates_dir / "styles.css"
            css_path_str = str(css_path) if css_path.exists() else None
            
            if not css_path_str:
                logger.warning(f"CSS file not found: {css_path}, generating PDF without custom styles")
            
            # Run PDF generation in separate process to avoid blocking
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(
                self._pdf_executor,
                _generate_pdf_sync,
                html_content,
                css_path_str
            )
            
            logger.info(f"PDF report generated: {len(pdf_bytes)} bytes")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise
    
    async def cleanup(self):
        """
        Cleanup resources, especially the ProcessPoolExecutor.
        MUST be called on application shutdown.
        """
        if not self._is_closed and self._pdf_executor is not None:
            logger.info("Shutting down PDF generation executor")
            self._pdf_executor.shutdown(wait=True)
            self._is_closed = True
            logger.info("Report generator cleanup complete")
        elif self._is_closed:
            logger.debug("Report generator already closed")
    
    async def generate_report(
        self,
        report_data: ReportData,
        format: ReportFormat
    ) -> bytes:
        """Generate report in specified format"""
        logger.info(f"Generating {format} report for run: {report_data.metadata.test_run_id}")
        
        if format == ReportFormat.JSON:
            content = self.generate_json(report_data)
            return content.encode('utf-8')
        elif format == ReportFormat.HTML:
            content = self.generate_html(report_data)
            return content.encode('utf-8')
        elif format == ReportFormat.PDF:
            return await self.generate_pdf(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

