# Handoffs

Cross-machine continuity records, written by [NouGenRelay](https://github.com/who-visions/nougenrelay)
and carried by git. One file per leg, named `<UTC timestamp>__<machine>__<agent>`.

Machines are slugified the same way everywhere in the fleet — `NOUGEN_MACHINE`,
else the hostname, lowercased — so one grep finds a box's commits and its
handoffs.

```bash
relay check                                   # has another machine moved?
relay claim take -s visions/core -g "…"       # announce BEFORE you work
relay claim release -s visions/core
relay create -g "what you did" -m "where you left off"
```

`relay check` first, always. This repo had no registry until 2026-08-02, and
the cost was concrete: a GCP project move and a Gemini version bump sat
uncommitted in the working tree for months, buried under 285 files of
mode-only churn, while `visions/core/agent.py` could not be imported at all.
Nothing announced either, because nothing was watching.
