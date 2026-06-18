"""
Ensembl ID to Gene Symbol Conversion Solution

Problem: Converting Ensembl gene IDs to human-readable gene symbols.

Usage:
    from solutions.ensembl_to_symbol import EnsemblConverter

    converter = EnsemblConverter()
    symbols = converter.convert(["ENSG00000139618", "ENSG00000141510"])
"""
from __future__ import annotations

from typing import Optional
import requests
import time


class EnsemblConverter:
    """
    Convert Ensembl gene IDs to gene symbols using Ensembl REST API.

    Supports:
    - Human (GRCh38)
    - Mouse (GRCm38)
    - Batch conversion
    - Local cache for repeated queries
    """

    def __init__(self, species: str = "human"):
        self.species = species
        self.server = "https://rest.ensembl.org"
        self.cache: dict[str, str] = {}

    def convert(self, ensembl_ids: list[str]) -> dict[str, Optional[str]]:
        """
        Convert Ensembl IDs to gene symbols.

        Args:
            ensembl_ids: List of Ensembl gene IDs

        Returns:
            Dict mapping Ensembl ID -> Gene symbol (None if not found)
        """
        results = {}

        for eid in ensembl_ids:
            if eid in self.cache:
                results[eid] = self.cache[eid]
            else:
                symbol = self._fetch_symbol(eid)
                self.cache[eid] = symbol
                results[eid] = symbol
                time.sleep(0.1)  # Rate limiting

        return results

    def _fetch_symbol(self, ensembl_id: str) -> Optional[str]:
        """Fetch gene symbol from Ensembl API."""
        species_map = {"human": "homo_sapiens", "mouse": "mus_musculus"}
        sp = species_map.get(self.species, "homo_sapiens")

        ext = f"/lookup/symbol/{sp}/{ensembl_id}?content-type=application/json"

        try:
            response = requests.get(f"{self.server}{ext}", headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                data = response.json()
                return data.get("symbol")
        except Exception:
            pass

        return None


def quick_convert(ensembl_ids: list[str]) -> dict[str, str]:
    """Convenience function for quick conversion."""
    converter = EnsemblConverter()
    return converter.convert(ensembl_ids)
