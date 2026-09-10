from pathlib import Path
from collections import Counter
import hashlib,json,re,datetime,subprocess
ROOT=Path(r"C:\STOCKS"); REPO=ROOT/"stocks-predictor"; WORK=ROOT/"work/markdown-review-20260909"
before=json.loads((WORK/"before.json").read_text(encoding="utf-8-sig"))
changed=json.loads((WORK/"changed.json").read_text(encoding="utf-8"))
changed_md={str(Path(p)) for p in changed if p.endswith(".md")}
context_docs={"HANDOFF.md","STOCKS_CURRENT_STATE.md","docs/AGENT_CHARTER.md","docs/RUNBOOK_H18.md","docs/continuation/SESSION_CONTEXT.md","docs/continuation/MIGRACAO_MAIN.md","docs/research/2026-09-09-h21-results.md"}
frozen={"RESEARCH_FREEZE.md","docs/DESIGN.md","docs/RJ_DESIGN.md"}
original_names={"instructions/STOCKS_PREDICTOR_PROMPT_FINAL_20260909.md","stocks-predictor/docs/continuation/MANDATO_20260909.md","stocks-predictor/docs/continuation/INITIAL_REQUEST.md"}
rows=[]
for entry in before:
    p=Path(entry["path"]); root_rel=p.relative_to(ROOT).as_posix()
    repo_rel=p.relative_to(REPO).as_posix() if p.is_relative_to(REPO) else None
    text=p.read_text(encoding="utf-8-sig")
    if str(p) in changed_md:
        status="ATUAL_COM_HISTORICO" if repo_rel in context_docs else "ATUAL"
    elif root_rel=="AGENTS.md":
        status="ATUAL"
    elif root_rel in original_names:
        status="MANDATO_ORIGINAL_VIGENTE" if "20260909" in root_rel else "PEDIDO_ORIGINAL_HISTORICO"
    elif root_rel.startswith("FONTES_WEB_ORIGINAIS/") or root_rel.startswith("outputs/"):
        status="ORIGINAL_PRESERVADO"
    elif repo_rel in frozen:
        status="PROTOCOLO_HISTORICO_CONGELADO"
    else:
        status="REGISTRO_HISTORICO"
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    rows.append(dict(path=root_rel,repository_path=repo_rel,status=status,bytes_before=entry["bytes"],
        sha256_before=entry["sha256"],sha256_after=digest,modified=digest!=entry["sha256"],
        lines=len(text.splitlines()),heading=next((x for x in text.splitlines() if x.startswith("#")),""),
        legacy_path_mentions=len(re.findall(r"Superleo13|Claude-projetos|crie-uma-imagem-de-2|STOCKS_MIGRACAO_MAIN_20260908",text)),
        stale_state_mentions=len(re.findall(r"nunca rodaram|nunca rodou|H17.{0,20}não executad|777 testes|374 testes|592 testes",text,re.I))))
counts=Counter(r["status"] for r in rows)
text=r"""# Índice documental — revisão de 09/09/2026

A revisão inventariou e varreu os **94 Markdown existentes em C:\STOCKS**:
caminhos, referências locais, estado da pesquisa, runtime, contagens de testes
e instruções conflitantes. Este índice é um arquivo novo, além dos 94 iniciais.
Não é nova auditoria científica ou recertificação de afirmações históricas.

## Leitura vigente

1. [AGENTS](../AGENTS.md) e [README](../README.md).
2. Início de [STOCKS_CURRENT_STATE](../STOCKS_CURRENT_STATE.md) e [HANDOFF](../HANDOFF.md).
3. [Mandato original vigente](continuation/MANDATO_20260909.md) e
   [prompt de continuidade atualizado](continuation/PROMPT_NOVO_CHAT.md).
4. [Relatório H21 com complemento final](research/2026-09-09-h21-results.md) e
   [reprodução H21](../research/session-20260909/h21/README.md).
5. [Mapa local](continuation/LOCAL_PATHS_20260909.json).

A raiz local única é `C:\STOCKS`; código em `stocks-predictor`, pesquisa/logs em
`work`, entregas em `outputs`. Não usar antigos destinos em Superleo13 ou no chat.
Runtime instalado do Codex e GitHub são recursos externos do ambiente/remoto.

A referência integrada H21 é `4a85d43`, com CI184: 782 testes regulares,
Python 3.13.15/Core 3.2.0 no Linux, cobertura 78%; 17 testes arquivados excluídos.
O SHA e a CI de uma revisão posterior devem ser conferidos separadamente.
A H21 continua inconclusiva para lucro executável, e seu plano futuro está
registrado, sem observações. H20 fica estacionada para reconstrução ampla.

## Como interpretar o acervo

- **ATUAL:** instruções corrigidas ou conferidas para este computador.
- **ATUAL_COM_HISTORICO:** o primeiro bloco é vigente; depois do separador,
  a narrativa e os comandos pertencem às respectivas versões.
- **MANDATO_ORIGINAL_VIGENTE:** prompt do usuário mantido byte a byte;
  seus dados de partida não substituem o estado verificado após a execução.
- **PROTOCOLO_HISTORICO_CONGELADO:** regras/lacres preservados. Descrições antigas
  de ambiente ou prontidão não significam estado operacional atual.
- **ORIGINAL_PRESERVADO / PEDIDO_ORIGINAL_HISTORICO / REGISTRO_HISTORICO:**
  evidência datada e proveniência, sem instrução automática de retomada.

O charter antigo e o runbook H18 receberam aviso de contexto. Os três guias
em `FONTES_WEB_ORIGINAIS` e o relatório lacrado em `outputs` mantêm os bytes
originais; os nomes “continuar”, “iniciar” ou “resultado” não os tornam vigentes.
O `COMECE_AQUI.md` da raiz agora aponta para os documentos atuais.

Não substituir em massa caminhos, contagens ou vereditos nos documentos datados:
isso apagaria o que foi feito em cada versão. Links históricos a pastas de outra
máquina ou artefatos não restaurados são registrados no recibo local, não promovidos
a links operacionais. O teste de links ativos exclui o corpo histórico após o aviso.

A documentação corrigiu caminhos, Python/Core, comandos de instalação Windows,
escopo de tipagem, contagens de CI por SHA, capital como cenário, estado H21/H20,
plano futuro já registrado e atraso da finalização. Nenhum resultado, parâmetro,
fonte bruta, banco, trial ou protocolo congelado foi alterado.

Inventário inicial, hashes antes/depois, cópias anteriores dos arquivos editados
e verificações estão em `C:\STOCKS\work\markdown-review-20260909`.
Arquivos locais da raiz/entrega não fazem parte do repositório Git.

## Inventário completo dos 94 arquivos iniciais

O caminho é relativo a `C:\STOCKS`. Cada arquivo aparece uma vez.

| Arquivo | Classificação | Ação |
|---|---|---|
"""
for row in sorted(rows,key=lambda r:r["path"].lower()):
    text+=f"| `{row['path']}` | {row['status']} | {'Atualizado' if row['modified'] else 'Preservado/conferido'} |\n"
text=text.replace("`","`") # Markdown delimiter substituted before this script runs.
(REPO/"docs/DOCUMENTATION_INDEX.md").write_text(text,encoding="utf-8",newline="\n")
current_paths=[ROOT/r["path"] for r in rows if r["status"] in ("ATUAL","ATUAL_COM_HISTORICO")]
current_paths.append(REPO/"docs/DOCUMENTATION_INDEX.md")
broken_active=[]; broken_historical=[]; active_links=0
pattern=re.compile(r"\[[^\]\n]*\]\(([^)\n]+)\)")
def check_links(p,content,active):
    global active_links
    # Only actual Markdown links outside code fences; fragments and remote URLs are not local paths.
    content=re.sub(r"```[\s\S]*?```","",content)
    for match in pattern.finditer(content):
        target=match.group(1).strip().strip("<>")
        if re.match(r"(?i)(https?://|mailto:|app:|codex:|#)",target): continue
        target=target.split("#",1)[0]
        if not target: continue
        dest=(p.parent/target).resolve()
        if active: active_links+=1
        if not dest.exists():
            (broken_active if active else broken_historical).append({"document":str(p.relative_to(ROOT)),"target":target})
for row in rows:
    p=ROOT/row["path"]; content=p.read_text(encoding="utf-8-sig")
    if p in current_paths:
        if row["status"]=="ATUAL_COM_HISTORICO":
            current_part,history=content.split("\n---\n",1)
            check_links(p,current_part,True);check_links(p,history,False)
        else: check_links(p,content,True)
    else: check_links(p,content,False)
check_links(REPO/"docs/DOCUMENTATION_INDEX.md",text,True)
protected=[r for r in rows if r["status"] not in ("ATUAL","ATUAL_COM_HISTORICO")]
unexpected=[r["path"] for r in protected if r["modified"]]
receipt={"reviewed_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"initial_markdown_count":len(rows),"new_index_files":1,"updated_initial_markdown_count":sum(r["modified"] for r in rows),
"classifications":dict(counts),"current_local_links_checked":active_links,"broken_current_local_links":broken_active,
"historical_missing_link_targets":broken_historical,"protected_originals_and_historical_files":len(protected),
"unexpected_protected_changes":unexpected,"files":rows,
"scope":"All 94 initial Markdown files inventoried, decoded and scanned. Operational documents reviewed and corrected. Historical documents classified/preserved; their scientific results and remote URLs not re-audited."}
(WORK/"audit.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:receipt[k] for k in receipt if k not in ("files","historical_missing_link_targets")},ensure_ascii=False))
print("Historical unresolved local links:",len(broken_historical))
if broken_active or unexpected: raise SystemExit(2)

