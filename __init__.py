"""Hermes SkillSense plugin: audited local skill routing and CLI.

No model is used by pre_llm_call. Metadata generation is explicit and is only
sent to a numeric loopback endpoint, with no redirects or proxy fallback.
"""
from __future__ import annotations

__version__ = "0.2.1"

def _root(args):
    from pathlib import Path
    import os
    return [Path(p).expanduser() for p in (getattr(args,"roots",None) or
        [str(Path(os.environ.get("HERMES_HOME",str(Path.home()/".hermes"))) / "skills")])]

def _status(enabled_setting: bool = False) -> str:
    from .store import open_db, rows, data_dir
    dbfile = data_dir() / "data.db"
    if not dbfile.is_file():
        return "SkillSense: no catalogue yet. Run 'hermes skillrouter rebuild'."
    conn = open_db()
    try:
        items = rows(conn)
        flags = {}
        for row in items:
            flags[row["status"]] = flags.get(row["status"],0)+1
        enabled = (data_dir()/"enabled.flag").exists() or enabled_setting
        return f"SkillSense {__version__}: {len(items)} skills, {flags}, routing {'enabled' if enabled else 'disabled'}."
    finally:
        conn.close()

def _rebuild(args) -> str:
    from .catalog import scan_skills
    from .store import open_db, sync, publish_index
    from .routing import clear_cache
    roots = _root(args)
    for root in roots:
        if not root.is_dir():
            raise ValueError(f"Skill root missing or not a directory: {root}")
    skills = scan_skills(roots)
    if not skills:
        raise ValueError("No eligible skills found; existing index preserved")
    conn = open_db()
    try:
        result = sync(conn, skills)
        publish_index(conn)
    finally:
        conn.close()
    clear_cache()
    return f"Rebuilt index: {result['total']} skills ({result['added']} new; {result['changed']} changed)."

def _clean(args) -> str:
    from pathlib import Path
    from .catalog import scan_skills
    from .store import open_db, sync, rows, stage, publish_index
    from .local_model import enrich, endpoint
    roots = _root(args)
    if any(not root.is_dir() for root in roots):
        raise ValueError("All supplied skill roots must be readable directories")
    # Verify destination BEFORE reading any skill source.
    with_model = getattr(args,"model", "none") == "aux"
    if with_model:
        endpoint(getattr(args,"endpoint","") or "")
        if not getattr(args,"model_id",None):
            raise ValueError("--model-id is required for strictly local auxiliary inference")
    skills = scan_skills(roots)
    if not skills:
        raise ValueError("No eligible skills found; no changes made")
    if getattr(args,"dry_run",False):
        empty = sum(not s.tags or not s.description for s in skills)
        return f"Dry run: {len(skills)} skills, {empty} with missing description or tags; no files or database changed."
    conn = open_db()
    counts = {"proposed":0,"skipped":0,"failed":0}
    try:
        sync(conn,skills)
        by_id = {r["id"]:r for r in rows(conn)}
        for s in skills:
            existing = by_id[s.identity]
            if not getattr(args,"force",False) and existing["status"] in ("pending","approved","rejected"):
                counts["skipped"] += 1
                continue
            if not with_model:
                counts["skipped"] += 1
                continue
            try:
                raw = Path(s.path).read_text(encoding="utf-8")
                import hashlib
                if hashlib.sha256(raw.encode("utf-8")).hexdigest() != s.sha256:
                    counts["failed"] += 1
                    continue
                proposal = enrich(raw[:12000],args.model_id,args.endpoint)
                counts["proposed"] += int(stage(conn,s.identity,s.sha256,proposal))
            except Exception:
                counts["failed"] += 1
        publish_index(conn)
    finally:
        conn.close()
    return (f"Audit completed: {len(skills)} scanned, {counts['proposed']} pending review, "
            f"{counts['skipped']} reused/skipped, {counts['failed']} failed. "
            "Original SKILL.md files unchanged.")

def _review(args) -> str:
    from .store import open_db, rows, decide, publish_index
    from .routing import clear_cache
    conn = open_db()
    try:
        action = getattr(args,"review_action","list")
        all_rows = rows(conn)
        if action == "list":
            relevant = [(r["id"],r["name"],r["pending"]) for r in all_rows if r["pending"]]
            if not relevant:
                return "No pending metadata proposals."
            return "\n".join(f"{name} | {identifier} | {str(proposal)[:220]}"
                             for identifier,name,proposal in relevant[:80])
        target = getattr(args,"skill",None)
        matches = [r for r in all_rows if r["id"] == target or r["name"] == target]
        if len(matches) != 1:
            raise ValueError(f"Expected one matching skill; found {len(matches)}")
        ok = decide(conn,matches[0]["id"],action=="approve")
        if not ok:
            return "No pending proposal for that skill."
        publish_index(conn)
        clear_cache()
        return f"{'Approved' if action == 'approve' else 'Rejected'} proposal for {matches[0]['name']}."
    finally:
        conn.close()

def _configure(args, ctx=None) -> str:
    from .store import data_dir
    from .routing import clear_cache
    root = data_dir()
    root.mkdir(parents=True,exist_ok=True)
    flag = root/"enabled.flag"
    if ctx is not None and hasattr(ctx,"set_config"):
        ctx.set_config("enabled", args.action == "enable")
        flag.unlink(missing_ok=True)
        return f"Routing {args.action}d in Hermes settings. Restart Hermes to apply."
    if args.action == "enable":
        if not (root/"index.json").exists():
            raise ValueError("Run 'hermes skillrouter rebuild' before enabling routing")
        flag.write_text("1\n",encoding="utf-8")
    else:
        flag.unlink(missing_ok=True)
    clear_cache()
    return f"Routing {args.action}d. Restart Hermes to apply to existing sessions."

def _cli(args, ctx=None):
    command = getattr(args,"skillsense_command",None)
    try:
        if command in (None,"status"):
            enabled_setting = bool(ctx.get_config("enabled",default=False)) if ctx is not None else False
            print(_status(enabled_setting))
        elif command == "rebuild":
            print(_rebuild(args))
        elif command == "clean":
            if ctx is not None:
                args.endpoint = getattr(args,"endpoint",None) or ctx.get_config("local_endpoint",default="")
                args.model_id = getattr(args,"model_id",None) or ctx.get_config("local_model_id",default="")
            print(_clean(args))
        elif command == "review":
            print(_review(args))
        elif command in ("enable","disable"):
            args.action=command
            print(_configure(args,ctx))
        elif command == "doctor":
            from .store import data_dir
            print(f"SkillSense {__version__}: data at {data_dir()}; native registration active.")
            print("Verify host with: hermes plugins doctor . --ci; hermes plugins validate .")
        else:
            print("Use: hermes skillrouter status|rebuild|clean|review|enable|disable|doctor")
    except Exception as exc:
        # Local operator CLI may display an actionable error; avoid skill body output.
        print(f"SkillSense error: {type(exc).__name__}: {exc}")
        raise SystemExit(2) from None

def _setup(parser):
    sub = parser.add_subparsers(dest="skillsense_command")
    sub.add_parser("status",help="Show approved/pending skill state")
    for name in ("rebuild","clean"):
        cmd = sub.add_parser(name,help="Read-only scan of trusted skill roots")
        cmd.add_argument("--root",dest="roots",action="append",help="Trusted skills directory")
        if name=="clean":
            cmd.add_argument("--audit",action="store_true",help="Audit existing and missing metadata")
            cmd.add_argument("--dry-run",action="store_true",help="No database writes or LLM calls")
            cmd.add_argument("--force",action="store_true",help="Regenerate previously reviewed metadata")
            cmd.add_argument("--model",choices=("none","aux"),default="none")
            cmd.add_argument("--endpoint",help="Explicit http://127.0.0.1:PORT/v1/chat/completions")
            cmd.add_argument("--model-id",help="Locally served model identifier")
    review = sub.add_parser("review",help="List, approve or reject proposals")
    review.add_argument("review_action",nargs="?",choices=("list","approve","reject"),default="list")
    review.add_argument("skill",nargs="?",help="Exact skill id or unambiguous name")
    sub.add_parser("enable",help="Enable runtime hints after restart")
    sub.add_parser("disable",help="Disable runtime hints after restart")
    sub.add_parser("doctor",help="Show local integration diagnostics")
    parser.set_defaults(func=_cli)

def _slash(args: str, ctx=None) -> str:
    # Slash commands can arrive from third-party gateways. Never run filesystem scans
    # or model requests from here without a documented authenticated permission check.
    action = (args or "").strip().lower()
    if action in ("","status","help"):
        return _status(bool(ctx.get_config("enabled",default=False)) if ctx is not None else False)
    return "For security, maintenance operations are CLI-only. Use: hermes skillrouter --help"

def register(ctx):
    from .routing import hint
    from .store import data_dir
    active = (data_dir()/"enabled.flag").exists() or bool(ctx.get_config("enabled",default=False))
    max_suggestions = max(1,min(3,int(ctx.get_config("max_suggestions",default=2))))
    def on_turn(user_message="",session_id="",**kwargs):
        return hint(user_message,max_suggestions=max_suggestions,session_id=session_id) if active else None
    ctx.register_hook("pre_llm_call",on_turn)
    ctx.register_cli_command(name="skillrouter",help="SkillSense local skill router",
                             setup_fn=_setup,handler_fn=lambda args: _cli(args,ctx))
    ctx.register_command("skillrouter",handler=lambda raw: _slash(raw,ctx),description="SkillSense status",
                         args_hint="[status]")
    ctx.register_auxiliary_task("skillrouter_tagger",display_name="SkillSense Metadata Tagger",
                                description="User-triggered local skill metadata enrichment")
