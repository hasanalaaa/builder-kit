PYTHON ?= python3
RUFF ?= ruff

.PHONY: test lint check
test:  ## every self-test in the plugin
	@fail=0; for t in $$(find plugins -name 'test_*.py' | sort); do \
	  if out=$$($(PYTHON) "$$t" 2>&1); then echo "ok   $$t"; else echo "FAIL $$t"; echo "$$out" | tail -8; fail=1; fi; \
	done; exit $$fail

lint:  ## ruff (real bugs only) + shell syntax + manifest JSON
	$(RUFF) check .
	@for s in plugins/builder-kit/skills/*/scripts/*.sh; do bash -n "$$s" || exit 1; done
	@$(PYTHON) -c "import json,sys; [json.load(open(p)) for p in sys.argv[1:]]" \
	  .claude-plugin/marketplace.json plugins/builder-kit/.claude-plugin/plugin.json plugins/builder-kit/hooks/hooks.json

check:  ## the builder-kit gate on this repo
	$(PYTHON) plugins/builder-kit/skills/ship/scripts/ship_check.py .
