"""SkillSense Hermes native plugin entry point (pre-alpha).

The pre-LLM hook intentionally returns None until safe skill discovery,
native eligibility checks and acceptance tests are implemented.
This version never reads skills, calls a model, or injects prompt content.
"""

__version__ = "0.1.0"


def _pre_llm_call(**kwargs):
    """Observer hook: leave Hermes inference and discovery unchanged."""
    return None


def _cli_handler(args):
    subcommand = getattr(args, "skillsense_command", None)
    if subcommand in (None, "status"):
        print("SkillSense 0.1.0 (pre-alpha): plugin scaffold active.")
        print("Skill injection: disabled. Metadata Clean: not implemented.")
    elif subcommand == "doctor":
        print("SkillSense registration loaded. Run: hermes plugins doctor . --ci")
    else:
        print("Unknown command. Use: hermes skillrouter status|doctor")


def _setup_cli(parser):
    sub = parser.add_subparsers(dest="skillsense_command")
    sub.add_parser("status", help="Show current SkillSense scaffold status")
    sub.add_parser("doctor", help="Show native plugin diagnostics guidance")
    parser.set_defaults(func=_cli_handler)


def _slash_command(raw_args: str) -> str:
    action = (raw_args or "").strip().lower()
    if action in ("", "status", "help"):
        return (
            "SkillSense 0.1.0 (pre-alpha). Skill routing and Metadata Clean "
            "are not implemented. No context is injected. "
            "Try: /skillrouter status"
        )
    if action == "doctor":
        return "Run 'hermes plugins doctor . --ci' from the SkillSense directory."
    return "Unknown action. Available: status, doctor, help."


def register(ctx):
    """Register supported native Hermes surfaces without side effects."""
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_cli_command(
        name="skillrouter",
        help="SkillSense (pre-alpha): status and diagnostics",
        setup_fn=_setup_cli,
        handler_fn=_cli_handler,
    )
    ctx.register_command(
        "skillrouter",
        handler=_slash_command,
        description="SkillSense (pre-alpha) status",
        args_hint="[status|doctor]",
    )
