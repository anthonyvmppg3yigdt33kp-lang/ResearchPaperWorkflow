# Phase Report: {project_title}
**Run ID**: {run_id}
**Generated**: {timestamp}
**Auditor**: Objective audit — automated agent (read-only exploration of all output files)
**Work Log Match**: Entry #{entry_start} ({phase_name}) + Entry #{entry_end} ({phase_name_end})

---

## 1. Executive Summary

{one_paragraph_summary_of_all_phases_completed}

---

## 2. Analysis Methods & Parameters

### 2.1 {step_1_name}
- **Method**: {method_description}
- **Parameters**: {key_parameters}
- **Code**: `{script_paths}`
- **Key outputs**: `{output_files}`
- **Key result**: {primary_finding}

### 2.2 {step_2_name}
- **Method**: {method_description}
- **Parameters**: {key_parameters}
- **Code**: `{script_paths}`
- **Key outputs**: `{output_files}`
- **Key result**: {primary_finding}

<!-- Repeat for each analysis step -->

---

## 3. Results Inventory

### 3.1 Generated Figures ({figure_count} total)

| # | Figure | Description |
|---|--------|-------------|
| 1 | `{figure_file}` | {description} |

### 3.2 Generated Tables ({table_count} total)

| # | Table | Rows | Description |
|---|-------|------|-------------|
| 1 | `{table_file}` | {row_count} | {description} |

### 3.3 Analysis Scripts ({script_count} total)

| # | Script | Language | Status |
|---|--------|----------|--------|
| 1 | `{script_file}` | {language} | {status} |

---

## 4. Key Biological Findings

1. **{finding_title}**: {description}. {confidence} confidence.

2. **{finding_title}**: {description}. {confidence} confidence.

<!-- One entry per key finding; include confidence level (HIGH/MODERATE/LOW) -->

---

## 5. Analysis Completeness Audit

### 5.1 COMPLETED
| Analysis | Output Count |
|----------|-------------|
| {analysis_name} | {count} |

### 5.2 NOT COMPLETED / DEFERRED

| Analysis | Blocker | Mitigation |
|----------|---------|------------|
| {analysis_name} | {blocker_description} | {mitigation_applied} |

### 5.3 Errors & Abnormal Results

| ID | Description | Severity | Resolution |
|----|-------------|----------|------------|
| ERR-001 | {description} | {severity} | {resolution_status} |

---

## 6. Task Continuity

| Step | Status | Timestamp | Work Log Entry |
|------|--------|-----------|---------------|
| {step_name} | {status_icon} | {timestamp} | Entry #{entry_number} |

**Next**: {next_step_description}

---

## 7. Parameters Quick Reference

| Parameter | Value | Used In |
|-----------|-------|---------|
| {parameter_name} | {value} | {phase_id} |

---

## 8. Timestamp

- **Analysis started**: {start_timestamp}
- **{phase_1_name} completed**: {phase_1_timestamp}
- **{phase_2_name} completed**: {phase_2_timestamp}
- **Phase Report**: {report_timestamp}
- **Total files**: {total_file_count} ({figure_count} figures + {table_count} tables + {script_count} scripts + {log_count} logs + {metadata_count} metadata)
- **Total errors**: {error_count} ({resolved_count} resolved, {deferred_count} deferred)
- **Completion**: ~{completion_pct}% ({deferred_pct}% deferred due to {deferral_reason})
