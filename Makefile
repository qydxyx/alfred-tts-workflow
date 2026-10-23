.PHONY: dev-setup lint test smoke build icons

UV ?= uv

dev-setup:
	$(UV) sync --extra dev

icons:
	$(UV) run --with pillow python scripts/generate_icons.py

lint:
	$(UV) run ruff check src tests scripts

test:
	$(UV) run pytest -v tests/

smoke:
	alfred_workflow_data="/tmp/alfred-tts-smoke/data" \
	alfred_workflow_cache="/tmp/alfred-tts-smoke/cache" \
	$(UV) run python -m alfred_tts filter "你好，欢迎使用 Alfred TTS"

build:
	python3 scripts/generate_info_plist.py
	rm -rf build/workflow dist
	mkdir -p dist build/workflow/python build/workflow/scripts build/workflow/icons
	cp -R src/alfred_tts build/workflow/python/
	find build/workflow -type d -name '__pycache__' -prune -exec rm -rf {} +
	find build/workflow -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete
	cp workflow/info.plist build/workflow/info.plist
	cp workflow/scripts/bootstrap.sh build/workflow/scripts/bootstrap.sh
	cp workflow/icons/*.png build/workflow/icons/ 2>/dev/null || true
	cp workflow/icon.png build/workflow/icon.png 2>/dev/null || true
	chmod +x build/workflow/scripts/bootstrap.sh
	cd build/workflow && zip -qry ../../dist/Alfred-TTS.alfredworkflow .
	plutil -lint workflow/info.plist
	@echo "Built dist/Alfred-TTS.alfredworkflow"
