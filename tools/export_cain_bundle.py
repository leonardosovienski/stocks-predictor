"""Producer-owned exact source-version provenance from a pinned existing receipt.

Default path opens no database. An opt-in bounded DatasetSelection reads a pinned backup. Original
source versions remain reference-only because redistribution is not certified.
"""

import argparse
import sys
from pathlib import Path

from research_bundle import digest, loads
from research_bundle.export import Builder, admitted_sources

sys.path.insert(0, str(Path(__file__).resolve().parent))

SOURCE = "docs/engineering/2026-09-11-architecture/evidence/real-v020.json"


def export(root, expected, destination, exported_at, *, selection=None, backup_sha=None):
    revision, sources = admitted_sources(root, expected, {SOURCE})
    if (selection is None) != (backup_sha is None):
        raise ValueError("Selection and backup SHA must be supplied together")
    selection_receipt = None
    if selection is not None:
        from cain_bundle_selection import select_metadata

        selection_receipt = select_metadata(root, backup_sha, selection)
    receipt = loads(sources[SOURCE])
    if not isinstance(receipt.get("inspection", {}).get("sources"), list):
        raise ValueError("Unsupported catalog receipt")
    builder = Builder(
        "stocks",
        revision,
        "sha256:"
        + digest(
            Path(__file__).read_bytes() + (Path(__file__).parent / "cain_bundle_selection.py").read_bytes()
        ),
        dict(expected),
        exported_at,
    )
    artifact = builder.resource(
        SOURCE,
        "producer:" + SOURCE,
        known_sha=digest(sources[SOURCE]),
        size=len(sources[SOURCE]),
        role="report",
        metadata={
            "redistribution": "UNKNOWN",
            "scope": "Source-version metadata only; raw receipt not transferred",
        },
    )
    report = builder.entity(
        "catalog-measurement:" + digest(sources[SOURCE]),
        "measurement",
        receipt["status"],
        {
            "scope": receipt["scope"],
            "capital_enabled": receipt["capital_enabled"],
            "source_sha256": receipt["source_sha256"],
            "rows": receipt["rows"],
        },
        SOURCE,
        axis="operational",
        identity_basis="content_hash",
    )
    builder.relation(report, "SUPPORTED_BY", artifact)
    for source in receipt["inspection"]["sources"]:
        # Preserve exact existing metadata including source_id vs source-file hash.
        node = builder.entity(
            source["source_id"],
            "dataset",
            "UNKNOWN",
            dict(source),
            SOURCE,
            axis="availability",
            recorded_at=source["observed_at"],
        )
        resource = builder.resource(
            "source:" + source["source_id"],
            source["source_url"],
            known_sha=source["sha256"],
            media_type="application/zip",
            role="dataset_slice",
            metadata={
                "redistribution": "UNKNOWN",
                "representation": "full source reference",
                "historical_publication_certified": receipt["inspection"]["historical_publication_certified"],
            },
        )
        builder.relation(report, "USES_DATASET", node)
        builder.relation(node, "REPRESENTED_BY", resource)
    if selection_receipt is not None:
        from cain_bundle_selection import BACKUP

        builder.body["origin"]["inputs"][BACKUP] = backup_sha
        builder.body["coverage"]["included"].append(BACKUP)
        selection_node = builder.entity(
            "selection:" + selection_receipt["selection_sha256"],
            "dataset_selection",
            "AVAILABLE_INTERNAL",
            selection_receipt,
            BACKUP,
            axis="availability",
            identity_basis="content_hash",
        )
        selection_reference = builder.resource(
            "selection:" + selection_receipt["selection_sha256"],
            "producer:" + BACKUP + "#selection=" + selection_receipt["selection_sha256"],
            role="dataset_slice",
            metadata={
                "redistribution": "UNKNOWN",
                "selection": selection_receipt["selection"],
                "selection_sha256": selection_receipt["selection_sha256"],
                "hash_semantics": "domain selection manifest; not artifact bytes",
            },
        )
        builder.relation(selection_node, "REPRESENTED_BY", selection_reference)
        builder.relation(selection_node, "REFERENCES", artifact)
        source_nodes = {e["entity_id"]: e for e in builder.body["entities"] if e["entity_type"] == "dataset"}
        from research_bundle import endpoint

        for source_id in selection_receipt["selection"]["source_ids"]:
            if source_id not in source_nodes:
                raise ValueError("Selected source not admitted in catalog receipt")
            node = source_nodes[source_id]
            builder.relation(
                selection_node,
                "USES_DATASET",
                endpoint("entity", builder.body["origin"], source_id, node["revision"]),
            )
        builder.body["coverage"]["limitations"].append(
            "Selection is for this export only; not linked to historical experiment use"
        )
    builder.body["coverage"]["missing"] = [
        *([] if selection_receipt is not None else ["No DatasetSelection export selection requested"]),
        "No licensed price slice transferred",
    ]
    builder.body["coverage"]["limitations"].append(
        "Exact source versions from existing catalog receipt; catalog observed_at is not historical public availability"
    )
    return builder.publish(root, destination, sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--backup-sha")
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--observed-before")
    parser.add_argument("--session-date")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--exported-at", required=True)
    args = parser.parse_args()
    selection = None
    if any((args.backup_sha, args.source_id, args.observed_before, args.session_date)):
        if not all((args.backup_sha, args.source_id, args.observed_before, args.session_date)):
            parser.error(
                "Selection requires backup SHA, explicit source IDs, observation cutoff and one session date"
            )
        selection = dict(
            source_ids=args.source_id,
            observed_before=args.observed_before,
            start=args.session_date,
            end=args.session_date,
        )
    print(
        export(
            args.root,
            {SOURCE: args.expected_sha},
            args.destination,
            args.exported_at,
            selection=selection,
            backup_sha=args.backup_sha,
        )["bundle_id"]
    )


if __name__ == "__main__":
    main()
