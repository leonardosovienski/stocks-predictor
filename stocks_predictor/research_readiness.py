"""External Intelligence readiness axes (read from the frozen readiness matrix).

Eligibility for a trial comes ONLY from the ``readiness`` field of an entry of
``eligible_families``; being listed under that key grants nothing. The effective PIT state
is ``protocol_effective_PIT`` when the matrix records one (it may downgrade a declared
``PIT_STRICT`` to ``HISTORICAL_ONLY``); the database-declared state is informative only.

Each family is classified on independent axes; one ready axis never promotes another
(collected != PIT_STRICT != eligible != used by the model != usable by the contract).
"""

from __future__ import annotations

AXES = (
    "ingestion",
    "pit_storage",
    "qa",
    "capacity",
    "continuous_collection",
    "trial_eligibility",
    "model_use",
    "contract_use",
)
MATRIX_VERSION_PREFIX = "external-intelligence-trial-readiness-matrix/"


class ReadinessError(ValueError):
    pass


def _pit_counts(entry: dict) -> tuple[dict, dict, str]:
    """(declared, effective, basis) PIT counts of an eligible-family entry."""
    top = {k: entry[k] for k in ("PIT_STRICT", "PIT_RECONSTRUCTED", "HISTORICAL_ONLY") if k in entry}
    declared = entry.get("database_declared_PIT") or (top if len(top) == 3 else None)
    effective_raw = entry.get("protocol_effective_PIT")
    if effective_raw is not None:
        effective = {k: effective_raw.get(k) for k in ("PIT_STRICT", "PIT_RECONSTRUCTED", "HISTORICAL_ONLY")}
        basis = "protocol_effective_PIT"
    elif len(top) == 3:
        effective, basis = dict(top), "declared_without_downgrade"
    else:
        raise ReadinessError(f"{entry.get('source')}: no PIT state in the matrix")
    for counts in (declared, effective):
        if counts is None or any(type(v) is not int or v < 0 for v in counts.values()):
            raise ReadinessError(f"{entry.get('source')}: malformed PIT counts")
    return declared, effective, basis


def _fraction(counts: dict, key: str) -> float:
    total = sum(counts.values())
    return counts[key] / total if total else 0.0


def classify(matrix: dict, *, model_bindings: tuple[str, ...] = ()) -> dict:
    """Per-family axes. `model_bindings` = families the admitted model declares it uses."""
    if type(matrix) is not dict or not str(matrix.get("matrix_version", "")).startswith(MATRIX_VERSION_PREFIX):
        raise ReadinessError("not an External Intelligence readiness matrix")
    thresholds = matrix.get("thresholds")
    if type(thresholds) is not dict:
        raise ReadinessError("thresholds")
    families: dict[str, dict] = {}
    for entry in matrix.get("eligible_families", []):
        source = entry["source"]
        declared, effective, basis = _pit_counts(entry)
        strict_fraction = _fraction(effective, "PIT_STRICT")
        dominant = max(effective, key=lambda k: (effective[k], k)) if sum(effective.values()) else "NONE"
        missing = entry.get("missingness", {}).get("fraction")
        identity = entry.get("identity_coverage", {}).get("fraction")
        days = entry.get("date_range", {}).get("calendar_days")
        cohorts = entry.get("independent_periods_or_cohorts")
        readiness = entry.get("readiness")
        qa_ok = (
            isinstance(missing, (int, float)) and missing <= thresholds["maximum_missingness_fraction"]
            and isinstance(identity, (int, float)) and identity >= thresholds["minimum_identity_fraction"]
        )
        capacity_ok = (
            isinstance(days, int) and days >= thresholds["minimum_temporal_coverage_days"]
            and isinstance(cohorts, int) and cohorts >= thresholds["minimum_independent_cohorts"]
        )
        families[source] = {
            "role": "ELIGIBLE_CANDIDATE_FAMILY",
            "readiness_field": readiness,
            "declared_PIT": declared,
            "effective_PIT": effective,
            "effective_PIT_basis": basis,
            "downgraded_from_declared": declared.get("PIT_STRICT", 0) > effective["PIT_STRICT"],
            "axes": {
                "ingestion": "COLLECTED" if entry.get("observations", 0) else "NOT_COLLECTED",
                "pit_storage": "PIT_STRICT" if strict_fraction >= thresholds["minimum_PIT_STRICT_fraction"]
                else f"{dominant}_EFFECTIVE",
                "qa": "PASS" if qa_ok else "FAIL",
                "capacity": "MEETS_THRESHOLDS" if capacity_ok else "INSUFFICIENT",
                "continuous_collection": "NOT_DEMONSTRATED",
                "trial_eligibility": "READY" if readiness == "READY" else "NOT_READY",
                "model_use": "BOUND" if source in model_bindings else "NOT_BOUND",
                "contract_use": "TRIAL_CONSUMPTION_PERMITTED"
                if readiness == "READY" and strict_fraction >= thresholds["minimum_PIT_STRICT_fraction"]
                else "COLLECTION_ONLY",
            },
            "effective_PIT_STRICT_fraction": strict_fraction,
        }
    for key, role, eligibility in (
        ("supporting_families", "SUPPORT_ONLY", "NOT_ELIGIBLE_SUPPORT_ROLE"),
        ("ineligible_families", "INELIGIBLE", "NOT_ELIGIBLE"),
    ):
        for entry in matrix.get(key, []):
            families[entry["source"]] = {
                "role": role,
                "readiness_field": entry.get("readiness"),
                "axes": {
                    "ingestion": "COLLECTED" if entry.get("observations") or entry.get("security_links") else "NOT_COLLECTED",
                    "pit_storage": "NOT_ASSESSED_FOR_TRIAL",
                    "qa": "NOT_ASSESSED_FOR_TRIAL",
                    "capacity": "NOT_ASSESSED_FOR_TRIAL",
                    "continuous_collection": "NOT_DEMONSTRATED",
                    "trial_eligibility": eligibility,
                    "model_use": "BOUND" if entry["source"] in model_bindings else "NOT_BOUND",
                    "contract_use": "COLLECTION_ONLY",
                },
            }
    return {"thresholds": thresholds, "families": families,
            "ready_families": sorted(f for f, v in families.items() if v["axes"]["trial_eligibility"] == "READY")}


def consumption_decision(axes: dict, family: str) -> tuple[bool, str]:
    """Whether a backtest may CONSUME `family` data for a trial, with the reason."""
    entry = axes["families"].get(family)
    if entry is None:
        return False, "FAMILY_UNKNOWN_TO_READINESS_MATRIX"
    a = entry["axes"]
    if a["trial_eligibility"] != "READY":
        return False, f"FAMILY_NOT_READY ({a['trial_eligibility']}, readiness={entry['readiness_field']!r})"
    if a["contract_use"] != "TRIAL_CONSUMPTION_PERMITTED":
        return False, f"FAMILY_EFFECTIVE_PIT_BELOW_THRESHOLD ({a['pit_storage']})"
    if a["model_use"] != "BOUND":
        return False, "FAMILY_NOT_BOUND_TO_MODEL"
    return False, "MODEL_USE_NOT_IMPLEMENTED: no admitted model consumes External Intelligence features"


__all__ = ["AXES", "ReadinessError", "classify", "consumption_decision"]
