# Provenance

- Module ID: `external.lung_master.de_table_standardizer.v1`
- Source route: local experience transformation from lung-master style DE table handling
- Execution evidence: toy real-run with Python stdlib CSV processing
- Production boundary: post-processing only
- Claim boundary: no biological claim until upstream model, replicate unit, contrast and FDR are reviewed

This module intentionally avoids hard-coded disease or group labels. It maps
observed source columns to a generic standardized DE schema.
