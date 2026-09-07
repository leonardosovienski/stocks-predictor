"""Owner attribution across CVM consolidated statement layouts."""

import unicodedata


def normalized(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def owner_accounts(bpp, dre):
    """Select explicit parent attribution; unknown NCI is never assumed zero."""
    owners = [r for code, r in dre.items() if len(code) == 7 and
              "empresa controladora" in normalized(r["description"]) and
              "atribu" in normalized(r["description"])]
    earnings = owners[0] if len(owners) == 1 else None
    if earnings:
        parent = dre.get(earnings["account"][:4])
        if not parent or not any(x in normalized(parent["description"]) for x in ("lucro", "preju")):
            earnings = None
    roots = [r for code, r in bpp.items() if len(code) == 4 and
             normalized(r["description"]).startswith("patrimonio liquido")]
    equity, evidence = None, []
    if len(roots) == 1:
        total = roots[0]
        nci = [r for code, r in bpp.items() if code.startswith(total["account"]+".") and len(code) == 7
               and "nao controlad" in normalized(r["description"])]
        if len(nci) == 1:
            equity = total["value_brl"]-nci[0]["value_brl"]
            evidence = [total, nci[0]]
    return {"owner_earnings_brl": earnings["value_brl"] if earnings else None,
            "owner_equity_brl": equity, "earnings_source": earnings, "equity_sources": evidence,
            "issues": (["NO_CONSOLIDATED_OWNER_EARNINGS"] if earnings is None else []) +
                      (["NO_UNAMBIGUOUS_OWNER_EQUITY"] if equity is None else [])}
