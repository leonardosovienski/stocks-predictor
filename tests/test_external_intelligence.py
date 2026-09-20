"""Contract tests for research-only EXTERNAL_INTELLIGENCE_V1 staging."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import unittest
import zipfile

from stocks_predictor import external_intelligence as external


STAMP = "2026-09-19T15:00:00Z"
CNPJ = "33.000.167/0001-01"
CNPJ_DIGITS = "33000167000101"


def acquired(payload: bytes, stamp: str = STAMP) -> dict:
    return {"payload": payload, "fetched_at": stamp, "etag": None, "last_modified": None}


def csv_zip(files: dict[str, tuple[tuple[str, ...], list[list[str]]]]) -> bytes:
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, (columns, rows) in files.items():
            text = ";".join(columns) + "\n"
            text += "".join(";".join(row) + "\n" for row in rows)
            archive.writestr(name, text.encode("latin-1"))
    return result.getvalue()


def ipe_zip(year: int = 2026, *, subject: str = "Aviso") -> bytes:
    row = [
        CNPJ, "PETROLEO BRASILEIRO S.A. PETROBRAS", "9512", "2026-09-18", "Aviso aos Acionistas",
        "Outros", "", subject, "2026-09-18", "AP", "12345", "1", "https://example.invalid/doc",
    ]
    return csv_zip({f"ipe_cia_aberta_{year}.csv": (external.IPE_COLUMNS, [row])})


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


def buyback_zip() -> bytes:
    main = [
        "P-1", CNPJ, "PETROBRAS", "2026-09-01", "2027-03-01", "Ativo", "Compra",
        "Tesouraria", "Permanencia", "100", "200",
    ]
    intermediary = ["P-1", "60.746.948/0001-12", "BANCO BRADESCO S.A."]
    quantity = ["P-1", "Preferencial", "PN", "1000", "200"]
    return csv_zip({
        "cia_aberta_recompra_acoes.csv": (external.BUYBACK_MAIN, [main]),
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
                  "columns": [{"name": name} for name in expected], "values": [values]},
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
        with self.assertRaises(external.TemporalError):
            external.ingest_ipe(
                self.conn, self.raw, 2026, acquired(ipe_zip(), "2026-09-17T15:00:00Z"), []
            )

    def test_all_four_source_families_parse_with_explicit_lineage(self):
        b3 = {name: acquired(b3_payload(name)) for name in external.B3_TABLES}
        b3_result = external.ingest_b3_lending(
            self.conn, self.raw, "2026-09-18", b3, ["2026-09-22"]
        )
        vlmo_result = external.ingest_vlmo(self.conn, self.raw, 2026, acquired(vlmo_zip()), [])
        buyback_result = external.ingest_buyback(self.conn, self.raw, acquired(buyback_zip()), [])
        ipe_result = external.ingest_ipe(self.conn, self.raw, 2026, acquired(ipe_zip()), [])
        self.assertEqual(b3_result["rows_read"], 2)
        self.assertEqual(vlmo_result["rows_read"], 1)
        self.assertEqual(buyback_result["rows_read"], 1)
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

    def test_source_url_rejects_credentials_and_secret_like_queries(self):
        for url in (
            "http://dados.cvm.gov.br/file.zip",
            "https://user:pass@dados.cvm.gov.br/file.zip",
            "https://dados.cvm.gov.br/file.zip?api_key=secret",
        ):
            with self.assertRaises(external.ExternalIntelligenceError):
                external.validate_source_url(url)


if __name__ == "__main__":
    unittest.main()
