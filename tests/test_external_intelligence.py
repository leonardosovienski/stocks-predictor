"""Contract tests for research-only EXTERNAL_INTELLIGENCE_V1 staging."""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import UTC, datetime
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch
import zipfile

from stocks_predictor import external_intelligence as external


STAMP = "2026-09-19T15:00:00Z"
CNPJ = "33.000.167/0001-01"
CNPJ_DIGITS = "33000167000101"


def acquired(payload: bytes, stamp: str = STAMP) -> dict:
    return {
        "payload": payload,
        "fetched_at": stamp,
        "first_seen_at": stamp,
        "request_started_at": None,
        "collector_received_at": stamp,
        "response_http_date": None,
        "etag": None,
        "last_modified": None,
    }


def csv_zip(files: dict[str, tuple[tuple[str, ...], list[list[str]]]]) -> bytes:
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, (columns, rows) in files.items():
            text = ";".join(columns) + "\n"
            text += "".join(";".join(row) + "\n" for row in rows)
            archive.writestr(name, text.encode("latin-1"))
    return result.getvalue()


def ipe_zip(
    year: int = 2026, *, subject: str = "Aviso", protocol: str = "12345", duplicate: bool = False,
    reference: str = "2026-09-18",
) -> bytes:
    row = [
        CNPJ, "PETROLEO BRASILEIRO S.A. PETROBRAS", "9512", reference, "Aviso aos Acionistas",
        "Outros", "", subject, "2026-09-18", "AP", protocol, "1", "https://example.invalid/doc",
    ]
    return csv_zip({f"ipe_cia_aberta_{year}.csv": (external.IPE_COLUMNS, [row, row] if duplicate else [row])})


def vlmo_zip(year: int = 2026) -> bytes:
    main = [
        CNPJ, "PETROBRAS", "2026-08-31", "1", "9512", "VLMO", "Mensal", "2026-09-10",
        "AP", "", "VLMO-1", "https://example.invalid/vlmo",
    ]
    detail = [
        CNPJ, "PETROBRAS", "2026-08-31", "1", "Administrador", "PESSOA", "Diretor",
        "Saldo Inicial", "Posicao", "Compra", "Acoes", "PN", "BANCO", "2026-08-29",
        "10", "25,50", "255,00",
    ]
    return csv_zip({
        f"vlmo_cia_aberta_{year}.csv": (external.VLMO_MAIN, [main]),
        f"vlmo_cia_aberta_con_{year}.csv": (external.VLMO_DETAIL, [detail]),
    })


def buyback_zip(*, include_bad: bool = False) -> bytes:
    main = [
        "P-1", CNPJ, "PETROBRAS", "2026-09-01", "2027-03-01", "Ativo", "Compra",
        "Tesouraria", "Permanencia", "100", "200",
    ]
    intermediary = ["P-1", "60.746.948/0001-12", "BANCO BRADESCO S.A."]
    quantity = ["P-1", "Preferencial", "PN", "1000", "200"]
    rows = [main]
    if include_bad:
        rows.append([
            "P-BAD", CNPJ, "PETROBRAS", "2026-09-10", "2026-09-01", "Encerrado", "Compra",
            "", "", "", "",
        ])
    return csv_zip({
        "cia_aberta_recompra_acoes.csv": (external.BUYBACK_MAIN, rows),
        "cia_aberta_recompra_acoes_intermediarios.csv": (
            external.BUYBACK_INTERMEDIARIES, [intermediary]
        ),
        "cia_aberta_recompra_acoes_quantidades.csv": (external.BUYBACK_QUANTITIES, [quantity]),
    })


def b3_payload(table_name: str) -> bytes:
    expected = external.B3_TABLES[table_name][1]
    if table_name == "BTBLendingOpenPosition":
        values = ["2026-09-18", "2026-09-18", "PETR4", "BRPETRACNPR6", "PETROBRAS", "PN", "VISTA", 10, 25.5, 255]
    else:
        values = [
            "2026-09-18", "2026-09-18", "PETR4", "BRPETRACNPR6", "PETROBRAS", "VISTA",
            2, 100, 0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 100, None, None,
        ]
    return json.dumps({
        "status": 4,
        "table": {"name": table_name, "pageCount": 1,
                  "version": 1, "columns": [{"name": name} for name in expected], "values": [values]},
    }).encode()


class ExternalIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = __import__("tempfile").TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.raw = self.root / "raw"
        self.conn = external.connect(self.root / "external.sqlite")

    def tearDown(self):
        self.conn.close()
        self.temporary.cleanup()

    def test_content_addressing_idempotency_and_republication_are_immutable(self):
        first = external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip()), [])
        replay = external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip()), [])
        changed = external.ingest_ipe(
            self.conn, self.raw, 2026, acquired(ipe_zip(subject="Aviso republicado"), "2026-09-20T15:00:00Z"), []
        )
        self.assertEqual(first["rows_persisted"], 1)
        self.assertEqual(replay["rows_persisted"], 0)
        self.assertEqual(changed["rows_persisted"], 1)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_raw_objects").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_source_versions").fetchone()[0], 2)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_observations").fetchone()[0], 2)
        chain = self.conn.execute(
            "SELECT COUNT(*) FROM external_source_versions WHERE supersedes_source_version_id IS NOT NULL"
        ).fetchone()[0]
        self.assertEqual(chain, 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("UPDATE external_source_versions SET dataset='X'")

    def test_schema_drift_rolls_back_database_changes(self):
        broken = csv_zip({"ipe_cia_aberta_2026.csv": (external.IPE_COLUMNS[:-1], [[""] * 12])})
        with self.assertRaises(external.SchemaDriftError):
            external.ingest_ipe(self.conn, self.raw, 2026, acquired(broken), [])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_source_versions").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_observations").fetchone()[0], 0)

    def test_schema_reorder_addition_and_removal_all_fail_closed(self):
        columns = list(external.IPE_COLUMNS)
        variants = (
            tuple(reversed(columns)),
            tuple(columns + ["Unexpected"]),
            tuple(columns[:-1]),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                broken = csv_zip({"ipe_cia_aberta_2026.csv": (variant, [[""] * len(variant)])})
                with self.assertRaises(external.SchemaDriftError):
                    external.ingest_ipe(self.conn, self.raw, 2026, acquired(broken), [])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_source_versions").fetchone()[0], 0)

    def test_raw_conflict_and_partial_b3_pagination_fail_without_database_commit(self):
        raw = external.preserve_raw(self.raw, b"first", STAMP)
        path = self.raw / raw["relative_path"]
        path.write_bytes(b"conflict")
        with self.assertRaises(external.ExternalIntelligenceError):
            external.preserve_raw(self.raw, b"first", STAMP)

        document = json.loads(b3_payload("BTBLendingOpenPosition"))
        document["table"]["pageCount"] = 2
        incomplete = acquired(json.dumps(document).encode())
        with self.assertRaises(external.SchemaDriftError):
            external.ingest_b3_lending(
                self.conn, self.raw, "2026-09-18", {"BTBLendingOpenPosition": [incomplete]}, []
            )
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_source_versions").fetchone()[0], 0)

    def test_temporal_boundary_uses_first_later_observed_session_and_fails_closed(self):
        # Friday 23:00 UTC is Friday 20:00 in Sao Paulo; Monday is intentionally absent (holiday).
        self.assertEqual(
            external.resolve_tradable_session("2026-09-18T23:00:00Z", ["2026-09-18", "2026-09-22"]),
            ("2026-09-22", "FIRST_SUBSEQUENT_OBSERVED_B3_SESSION"),
        )
        self.assertEqual(
            external.resolve_tradable_session("2026-09-18T23:00:00Z", []),
            (None, "NO_SUBSEQUENT_OBSERVED_B3_SESSION"),
        )
        self.assertTrue(external._observation(
            self.conn, source_version_id=self._source_version_for_temporal_test(),
            family="future-event", natural_key="future", payload={}, available_at=STAMP,
            sessions=[], reference_at="2026-10-01",
        ))
        with self.assertRaises(external.TemporalError):
            external.ingest_ipe(
                self.conn, self.raw, 2026, acquired(ipe_zip(), "2026-09-17T15:00:00Z"), []
            )

    def test_live_first_seen_uses_collector_clock_and_http_date_is_metadata(self):
        class Response:
            def __init__(self, http_date):
                self.headers = {} if http_date is None else {"Date": http_date}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return b"official-bytes"

        started = datetime(2026, 9, 21, 1, 0, tzinfo=UTC)
        received = datetime(2026, 9, 21, 1, 0, 2, tzinfo=UTC)
        for http_date, expected in (
            ("Sat, 19 Sep 2026 00:00:00 GMT", "2026-09-19T00:00:00Z"),
            ("Tue, 22 Sep 2026 00:00:00 GMT", "2026-09-22T00:00:00Z"),
            (None, None),
        ):
            ticks = iter((started, received))
            with self.subTest(http_date=http_date), patch.object(
                external, "urlopen", return_value=Response(http_date)
            ):
                result = external.fetch_bytes(
                    "https://example.invalid/source", clock=lambda: next(ticks)
                )
            self.assertEqual(result["request_started_at"], "2026-09-21T01:00:00Z")
            self.assertEqual(result["collector_received_at"], "2026-09-21T01:00:02Z")
            self.assertEqual(result["first_seen_at"], "2026-09-21T01:00:02Z")
            self.assertEqual(result["fetched_at"], "2026-09-21T01:00:02Z")
            self.assertEqual(result["response_http_date"], expected)

    def test_collector_clock_fails_closed_and_offline_observation_is_explicit(self):
        class Response:
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return b"official-bytes"

        ticks = iter((
            datetime(2026, 9, 21, 1, 0, 2, tzinfo=UTC),
            datetime(2026, 9, 21, 1, 0, tzinfo=UTC),
        ))
        with patch.object(external, "urlopen", return_value=Response()):
            with self.assertRaises(external.TemporalError):
                external.fetch_bytes("https://example.invalid/source", clock=lambda: next(ticks))
        source = self.root / "source.zip"
        source.write_bytes(b"offline")
        offline = external.source_file(source, "2026-09-21T02:00:00-03:00")
        self.assertEqual(offline["first_seen_at"], "2026-09-21T05:00:00Z")
        self.assertIsNone(offline["response_http_date"])

    def _source_version_for_temporal_test(self) -> str:
        source_id, _ = external._source_version(
            self.conn, self.raw, acquired(b"temporal-test"), publisher="TEST", dataset="TEMPORAL",
            logical_period="2026", source_url="https://example.invalid/source",
            parser_version="test/1",
        )
        return source_id

    def test_all_four_source_families_parse_with_explicit_lineage(self):
        b3 = {name: acquired(b3_payload(name)) for name in external.B3_TABLES}
        b3_result = external.ingest_b3_lending(
            self.conn, self.raw, "2026-09-18", b3, ["2026-09-22"]
        )
        vlmo_result = external.ingest_vlmo(self.conn, self.raw, 2026, acquired(vlmo_zip()), [])
        buyback_result = external.ingest_buyback(
            self.conn, self.raw, acquired(buyback_zip(include_bad=True)), []
        )
        ipe_result = external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip()), [])
        self.assertEqual(b3_result["rows_read"], 2)
        self.assertEqual(vlmo_result["rows_read"], 1)
        self.assertEqual(buyback_result["rows_read"], 2)
        self.assertEqual(buyback_result["rows_rejected"], 1)
        self.assertEqual(ipe_result["rows_read"], 1)
        direct = self.conn.execute(
            "SELECT COUNT(*) FROM external_observations WHERE identity_status='DIRECT_B3_TICKER_ISIN'"
        ).fetchone()[0]
        self.assertEqual(direct, 2)
        self.assertEqual(external.verify(self.conn, self.raw)["status"], "SUCCESS")

    def test_fca_identity_is_available_only_after_filing_and_links_by_interval(self):
        year = 2026
        metadata_columns = ("ID_DOC", "CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB")
        detail_columns = (
            "ID_Documento", "CNPJ_Companhia", "Data_Referencia", "Versao", "Codigo_Negociacao",
            "Valor_Mobiliario", "Data_Inicio_Negociacao", "Data_Fim_Negociacao", "Composicao_BDR_Unit",
        )
        fca = csv_zip({
            f"fca_cia_aberta_{year}.csv": (
                metadata_columns, [["D1", CNPJ, "2026-01-01", "1", "2026-03-01"]]
            ),
            f"fca_cia_aberta_valor_mobiliario_{year}.csv": (
                detail_columns,
                [["D1", CNPJ, "2026-01-01", "1", "PETR4", "Acoes PN", "2026-01-01", "", ""]],
            ),
        })
        external.ingest_fca_identity(self.conn, self.raw, year, acquired(fca))
        link = self.conn.execute(
            "SELECT company_cnpj,ticker,information_available_date FROM external_security_links"
        ).fetchone()
        self.assertEqual(tuple(link), (CNPJ_DIGITS, "PETR4", "2026-03-02"))
        external.ingest_ipe(
            self.conn, self.raw, year, acquired(ipe_zip(), "2026-09-19T16:00:00Z"), []
        )
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM external_observation_securities").fetchone()[0], 1
        )

    def test_status_verify_and_cli_contract_keep_staging_non_scientific(self):
        external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip()), [])
        report = external.status(self.conn)
        self.assertEqual(report["sources"][0]["source"], "IPE_METADATA")
        self.assertEqual(external.verify(self.conn, self.raw)["staging_is_factor_input"], False)
        parser = __import__("stocks_predictor.operations", fromlist=["parser"]).parser()
        args = parser.parse_args([
            "external", "status", "--db", str(self.root / "other.sqlite")
        ])
        self.assertEqual((args.command, args.external_action), ("external", "status"))
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(__import__("stocks_predictor.operations", fromlist=["main"]).main([
                "external", "status", "--db", str(self.root / "cli.sqlite")
            ]), 0)
        cli = external.connect(self.root / "cli.sqlite")
        try:
            self.assertEqual(cli.execute("SELECT COUNT(*) FROM external_receipts").fetchone()[0], 1)
        finally:
            cli.close()

    def test_receipt_is_deterministic_and_cli_failure_is_nonzero(self):
        operations = __import__("stocks_predictor.operations", fromlist=["main"])
        receipt_one = self.root / "status-one.json"
        receipt_two = self.root / "status-two.json"
        for receipt in (receipt_one, receipt_two):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(operations.main([
                    "external", "status", "--db", str(self.root / "status.sqlite"),
                    "--receipt", str(receipt),
                ]), 0)
        first = json.loads(receipt_one.read_text(encoding="utf-8"))
        second = json.loads(receipt_two.read_text(encoding="utf-8"))
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        with redirect_stdout(io.StringIO()):
            exit_code = operations.main([
                "external", "collect", "cvm-ipe", "--db", str(self.root / "failure.sqlite"),
                "--raw-root", str(self.raw), "--receipt", str(self.root / "failure.json"),
                "--year", "2026", "--source-file", str(self.root / "missing.zip"),
            ])
        self.assertNotEqual(exit_code, 0)

    def test_ops_contract_publication_lineage_and_no_factor_isolation(self):
        repository = Path(__file__).resolve().parents[1]
        job = json.loads(
            (repository / "docs/external_intelligence/ops-job.example.json").read_text(encoding="utf-8")
        )
        serialized = json.dumps(job)
        self.assertIn("MARKET_COLLECTION", serialized)
        self.assertIn("external", serialized)
        self.assertIn("expected_artifact", serialized)
        external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip()), [])
        source_id, digest = self.conn.execute(
            "SELECT source_version_id,sha256 FROM external_source_versions"
        ).fetchone()
        self.assertTrue(source_id.startswith("sha256:"))
        self.assertEqual(len(digest), 64)
        for name in ("factor.py", "portfolio.py", "big_winner_v2.py", "big_winner_shadow.py"):
            source = (repository / "stocks_predictor" / name).read_text(encoding="utf-8")
            self.assertNotIn("external_intelligence", source)

    def test_source_url_rejects_credentials_and_secret_like_queries(self):
        for url in (
            "http://dados.cvm.gov.br/file.zip",
            "https://user:pass@dados.cvm.gov.br/file.zip",
            "https://dados.cvm.gov.br/file.zip?api_key=secret",
        ):
            with self.assertRaises(external.ExternalIntelligenceError):
                external.validate_source_url(url)

    def test_frozen_big_winner_v2_baseline_bytes_are_unchanged(self):
        repository = Path(__file__).resolve().parents[1]
        expected = {
            "experiments/BIG_WINNER_IMPROVEMENT_PROGRAM_V1/V2_FINAL_FREEZE.json":
                "14a3c51bbbfd8b806d6d7574a282f1ebe5b8768797947892ace3e47a5dfdb3b9",
            "experiments/BIG_WINNER_IMPROVEMENT_PROGRAM_V1/V2_SELECTION_FREEZE.yaml":
                "44277c6c61286e2d2dd0de034d57315703150b3f2b7fa2bb090f18df29d1259f",
            "experiments/BIG_WINNER_IMPROVEMENT_PROGRAM_V1/prospective/LEDGER_RECEIPT.json":
                "a2ade11ae19c16c4f6c32132902416b727458421ecd21f2f7a23a6950dba3644",
            "experiments/BIG_WINNER_IMPROVEMENT_PROGRAM_V1/prospective/PROSPECTIVE_BIG_WINNER_LEDGER.sqlite":
                "b8d3710be8b9ca68276f9cb41fc4391f9b6acd0fb1b9a371f155884eb2db9884",
            "stocks_predictor/big_winner_v2.py":
                "190b90e5a0939b5460b98db4c4d4dea357b282014d211e4f27620683d18547aa",
            "stocks_predictor/big_winner_shadow.py":
                "b8540d5a697aee2ee418b0f61e273d08cfcb4a2d83a602d06af6a8401b39f409",
            "stocks_predictor/prospective_big_winner.py":
                "081c6670fb81ef7826162847af52b52585719f82ca0d7a68b20d26dc9c1ce805",
        }
        observed = {}
        for name in expected:
            payload = (repository / name).read_bytes()
            if not name.endswith(".sqlite"):
                payload = payload.replace(b"\r\n", b"\n")
            observed[name] = hashlib.sha256(payload).hexdigest()
        self.assertEqual(observed, expected)

    def test_ipe_without_protocol_uses_explicit_official_composite_identity(self):
        result = external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip(protocol="")), [])
        self.assertEqual(result["rows_persisted"], 1)
        payload = json.loads(self.conn.execute(
            "SELECT payload_json FROM external_observations"
        ).fetchone()[0])
        self.assertIsNone(payload["document_id"])
        self.assertEqual(payload["document_identity_basis"], "OFFICIAL_METADATA_COMPOSITE_NO_PROTOCOL")

    def test_duplicate_source_rows_remain_in_the_rejection_denominator(self):
        result = external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip(duplicate=True)), [])
        self.assertEqual((result["rows_read"], result["rows_persisted"], result["rows_rejected"]), (2, 1, 1))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM external_rejections").fetchone()[0], 1)

    def test_implausibly_far_future_ipe_reference_is_preserved_as_rejection(self):
        result = external.ingest_ipe(
            self.conn, self.raw, 2026, acquired(ipe_zip(reference="3036-03-20")), []
        )
        self.assertEqual((result["rows_read"], result["rows_persisted"], result["rows_rejected"]), (1, 0, 1))


if __name__ == "__main__":
    unittest.main()
