# Research Paper Workflow — Reporting Module
# Phase report generation, output audit, completeness checking.
#
# Provides:
#   PhaseReporter  — generates PHASE_REPORT.md with standardized sections
#   audit_outputs  — counts figures, tables, scripts, logs in a run directory
#   check_completeness — compares planned vs completed analysis steps
#
# Usage:
#   from paper_workflow.reporting import PhaseReporter
#   reporter = PhaseReporter()
#   report_path = reporter.generate_report(run_dir, work_log_path, error_log_path)
