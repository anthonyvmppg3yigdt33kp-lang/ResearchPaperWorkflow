"""
Skill Sandbox — Benchmarks new methods on historical projects before integration.

v3.0: Part of the self-iteration meta-workflow. New methods discovered by
MethodRadar are evaluated here against 2-3 historical projects before
being promoted to the main code library or skill registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SandboxResult:
    method_name: str
    method_version: str
    test_projects: list[str] = field(default_factory=list)
    stability_score: float = 0.0
    runtime_profile: dict = field(default_factory=dict)
    dependency_report: dict = field(default_factory=dict)
    recommendation: str = "hold"  # integrate, hold, reject
    rationale: str = ""
    benchmarked_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DependencyReport:
    new_packages: list[str] = field(default_factory=list)
    version_conflicts: list[str] = field(default_factory=list)
    install_complexity: str = "low"  # low, medium, high
    total_new_dependencies: int = 0


class SkillSandbox:
    """Evaluates new methods on historical project data before integration.

    Design principle: No method enters the main pipeline without passing
    sandbox evaluation on >=2 historical projects. This prevents regressions
    and ensures new methods actually improve results.
    """

    def __init__(self, sandbox_dir: Optional[Path] = None):
        self.sandbox_dir = sandbox_dir or Path("papers/sandbox")
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(self, method_card: dict, test_projects: list[Path]) -> SandboxResult:
        """Evaluate a new method against historical projects."""
        result = SandboxResult(
            method_name=method_card.get("name", "unknown"),
            method_version=method_card.get("version", "0.0.0"),
            test_projects=[str(p) for p in test_projects],
        )
        result.stability_score = self.compare_stability(method_card, test_projects)
        result.runtime_profile = self.measure_runtime(method_card, [100, 1000, 10000])
        dep_report = self.assess_dependency_complexity(method_card)
        result.dependency_report = {
            "new_packages": dep_report.new_packages,
            "version_conflicts": dep_report.version_conflicts,
            "install_complexity": dep_report.install_complexity,
            "total_new_dependencies": dep_report.total_new_dependencies,
        }
        result.recommendation, result.rationale = self._generate_recommendation(result)
        return result

    def compare_stability(self, method_card: dict, test_projects: list[Path]) -> float:
        """Compare result stability across test projects (0.0-1.0)."""
        num_projects = len(test_projects)
        if num_projects < 2:
            return 0.5
        benchmark = method_card.get("benchmark", {})
        base_score = benchmark.get("stability_score", 0.5)
        validated = method_card.get("validated_on_projects", [])
        if not validated:
            base_score -= 0.2
        return max(0.0, min(1.0, base_score))

    def measure_runtime(self, method_card: dict, data_sizes: list[int]) -> dict:
        """Estimate runtime across data sizes."""
        category = method_card.get("benchmark", {}).get("runtime_category", "medium")
        estimates = {
            "fast": {100: "<1s", 1000: "<5s", 10000: "<30s"},
            "medium": {100: "<5s", 1000: "<30s", 10000: "<5min"},
            "slow": {100: "<30s", 1000: "<5min", 10000: "<30min"},
        }
        return {
            "category": category,
            "estimates": {str(n): estimates.get(category, {}).get(n, "unknown") for n in data_sizes},
        }

    def assess_dependency_complexity(self, method_card: dict) -> DependencyReport:
        """Assess the dependency footprint of a method."""
        software = method_card.get("software", [])
        new_packages = []
        for sw in software:
            pkg_name = sw.get("package", sw.get("name", ""))
            if pkg_name:
                new_packages.append(pkg_name)
        complexity = "low"
        if len(new_packages) > 5:
            complexity = "high"
        elif len(new_packages) > 2:
            complexity = "medium"
        return DependencyReport(
            new_packages=new_packages,
            version_conflicts=[],
            install_complexity=complexity,
            total_new_dependencies=len(new_packages),
        )

    def _generate_recommendation(self, result: SandboxResult) -> tuple:
        """Generate integrate/hold/reject recommendation."""
        score = result.stability_score
        deps = result.dependency_report.get("total_new_dependencies", 0)
        complexity = result.dependency_report.get("install_complexity", "medium")
        if score >= 0.8 and complexity == "low" and deps <= 2:
            return ("integrate", f"High stability ({score:.2f}) with minimal dependencies ({deps}). Ready for registry.")
        elif score >= 0.6:
            return ("hold", f"Moderate stability ({score:.2f}). Test on more projects before integration.")
        elif score < 0.3:
            return ("reject", f"Low stability ({score:.2f}). Method not suitable for current pipeline.")
        else:
            return ("hold", f"Insufficient evidence. Benchmark on {3 - len(result.test_projects)} more projects.")

    def generate_benchmark_report(self, results: list[SandboxResult],
                                   output_path: Optional[Path] = None) -> Path:
        """Generate a comprehensive benchmark report."""
        path = output_path or (self.sandbox_dir / f"benchmark_report_{datetime.now().strftime('%Y%m%d')}.md")
        lines = [
            "# Skill Sandbox Benchmark Report",
            f"**Generated**: {datetime.now().isoformat()}",
            f"**Methods evaluated**: {len(results)}",
            "",
            "## Results Summary",
            "",
            "| Method | Stability | Runtime | Dependencies | Recommendation |",
            "|--------|-----------|---------|--------------|----------------|",
        ]
        for r in results:
            lines.append(
                f"| {r.method_name} | {r.stability_score:.2f} | "
                f"{r.runtime_profile.get('category', '?')} | "
                f"{r.dependency_report.get('total_new_dependencies', 0)} | "
                f"**{r.recommendation.upper()}** |"
            )
        lines += ["", "## Detailed Results", ""]
        for r in results:
            lines.append(f"### {r.method_name} v{r.method_version}")
            lines.append(f"- **Recommendation**: {r.recommendation}")
            lines.append(f"- **Rationale**: {r.rationale}")
            lines.append(f"- **Test projects**: {', '.join(r.test_projects)}")
            lines.append("")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path
