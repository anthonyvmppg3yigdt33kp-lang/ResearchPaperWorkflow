# Seurat FindMarkers Group DE

This module runs a parameterized Seurat `FindMarkers` comparison between two
identity values from a declared metadata column. It is designed as a reusable
method asset for marker screening and cell-level exploratory differential
expression, not as replicate-aware disease inference. The module writes
standardized result columns, group-size/sample-mapping diagnostics, source maps,
parameters, and session information under the node output directory.

Promotion of adapted literature-code variants must keep disease labels, author
paths, and project object names in provenance only.
