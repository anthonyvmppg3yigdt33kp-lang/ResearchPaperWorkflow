# External DE Table Standardizer

This module transforms an imported differential-expression table into a
standard ranked-gene table. It does not re-run the upstream statistical model
and does not validate the biological replicate unit, contrast design, covariates
or FDR provenance.

Dry-run:

```bash
python code_library/modules/external/lung_master/de_table_standardizer/main.py \
  --dry-run \
  --out tmp/external_de_standardizer \
  --run-id external_de_standardizer
```

Output `tables/ranked_gene_statistic.csv` can be used as an enrichment input
only after the upstream DE provenance is reviewed.
