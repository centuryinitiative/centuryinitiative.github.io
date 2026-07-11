# =============================================================================
# Canada Pop — Makefile
# =============================================================================
# Usage:
#   make              — run everything (coarse + fine-grain + bar races + report)
#   make plots        — coarse static PNGs only
#   make fg_plots     — fine-grain static PNGs only
#   make bar_race     — coarse bar-chart-race MP4s  (bcr1–4)
#   make fg_bar_race  — fine-grain bar-chart-race MP4s  (fg_bcr1–6)
#   make indigenous   — Indigenous share PNGs + MP4s  (IND01–04, IND_bcr1–2)
#   make french       — French (_fr) copies of every figure + video
#   make web-data     — export site/src/data/canada.json from the simulation
#   make web          — build the interactive website (needs: cd site && npm i)
#   make report       — compile LaTeX PDF (requires coarse plots)
#   make clean        — remove all generated outputs
#   make clean-plots  — remove PNGs and MP4s only
#   make clean-report — remove LaTeX build artefacts only
#
# Output prefixes:
#   (none) / bcr*    — coarse simulation (canada_sim.py)
#   fg* / fg_bcr*    — fine-grain simulation (fg_sim.py)
#
# Stamp files in plots/.stamps/ track completed scripts so make only
# re-runs a script when its source or data dependencies change.
# =============================================================================

PYTHON   := python3
PDFLATEX := pdflatex -interaction=nonstopmode

DATA     := $(wildcard data/*.csv)
CORE     := canada_sim.py loaders.py

STAMP_DIR := plots/.stamps
STAMPS := \
	$(STAMP_DIR)/sim \
	$(STAMP_DIR)/qc_share \
	$(STAMP_DIR)/roc_scenarios \
	$(STAMP_DIR)/imm_fr_share \
	$(STAMP_DIR)/extra \
	$(STAMP_DIR)/bar_race \
	$(STAMP_DIR)/fg_sim \
	$(STAMP_DIR)/fg_bar_race \
	$(STAMP_DIR)/indigenous

# -----------------------------------------------------------------------------
# Top-level targets
# -----------------------------------------------------------------------------

.PHONY: all plots fg_plots bar_race fg_sim fg_bar_race indigenous french web-data web report clean clean-plots clean-report

all: plots fg_plots bar_race fg_bar_race indigenous report

## plots — coarse static PNGs (no bar-race, no PDF)
plots: \
	$(STAMP_DIR)/sim \
	$(STAMP_DIR)/qc_share \
	$(STAMP_DIR)/roc_scenarios \
	$(STAMP_DIR)/imm_fr_share \
	$(STAMP_DIR)/extra

## fg_plots — fine-grain static PNGs only
fg_plots: $(STAMP_DIR)/fg_sim

## bar_race — coarse MP4 animations (bcr1–4)
bar_race: $(STAMP_DIR)/bar_race

## fg_sim — fine-grain simulation + static plots (~10–25 min)
fg_sim: $(STAMP_DIR)/fg_sim

## fg_bar_race — fine-grain bar chart race MP4s (fg_bcr1–6)
fg_bar_race: $(STAMP_DIR)/fg_bar_race

## indigenous — Indigenous share PNGs + bar-race MP4s (IND01–04, IND_bcr1–2)
indigenous: $(STAMP_DIR)/indigenous

## french — render French (_fr) copies of every figure + video.
## Monkeypatches matplotlib (see make_french.py + french_i18n.py); the plotting
## scripts are not modified. fg_sim must precede fg_bar_race. Not part of `all`
## (it re-runs every simulation) — invoke explicitly.
FR_SCRIPTS := canada_sim.py plot_qc_share.py plot_roc_scenarios.py \
              plot_imm_fr_share.py plot_extra.py plot_qc_roc_immigration.py \
              plot_bar_race.py plot_indigenous.py fg_sim.py fg_bar_race.py

french: make_french.py french_i18n.py
	@for s in $(FR_SCRIPTS); do echo ">> French: $$s"; $(PYTHON) make_french.py $$s || exit 1; done

## web-data — regenerate the website's JSON data bundle from the simulation
web-data: export_web_data.py $(CORE) $(DATA)
	$(PYTHON) export_web_data.py

## web — build the static interactive site into site/dist (deploy that folder).
## First time: cd site && npm install
web: web-data
	cd site && npm run build

## report — compile LaTeX to PDF (two passes for TOC/cross-refs)
report: canada_pop_report.pdf

# -----------------------------------------------------------------------------
# Directory setup
# -----------------------------------------------------------------------------

plots/:
	mkdir -p plots

$(STAMP_DIR): | plots/
	mkdir -p $(STAMP_DIR)

# -----------------------------------------------------------------------------
# Simulation + main plots  (01–10, P01–P09)
# -----------------------------------------------------------------------------

$(STAMP_DIR)/sim: $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) canada_sim.py
	@touch $@

# -----------------------------------------------------------------------------
# Standalone plot scripts
# -----------------------------------------------------------------------------

$(STAMP_DIR)/qc_share: plot_qc_share.py $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) plot_qc_share.py
	@touch $@

$(STAMP_DIR)/roc_scenarios: plot_roc_scenarios.py $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) plot_roc_scenarios.py
	@touch $@

$(STAMP_DIR)/imm_fr_share: plot_imm_fr_share.py $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) plot_imm_fr_share.py
	@touch $@

$(STAMP_DIR)/extra: plot_extra.py $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) plot_extra.py
	@touch $@

# -----------------------------------------------------------------------------
# Bar-chart races  (~10 min — rendered last)
# -----------------------------------------------------------------------------

$(STAMP_DIR)/bar_race: plot_bar_race.py $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) plot_bar_race.py
	@touch $@

# -----------------------------------------------------------------------------
# Indigenous overlay  (static PNGs + 2 bar-race MP4s, ~2–3 min)
# -----------------------------------------------------------------------------

$(STAMP_DIR)/indigenous: plot_indigenous.py $(CORE) $(DATA) | $(STAMP_DIR)
	$(PYTHON) plot_indigenous.py
	@touch $@

# -----------------------------------------------------------------------------
# Fine-grain simulation  (~10–25 min depending on FG_SCALE)
# -----------------------------------------------------------------------------

FG_DATA := $(wildcard data/fg_*.csv)

$(STAMP_DIR)/fg_sim: fg_sim.py loaders.py $(DATA) $(FG_DATA) | $(STAMP_DIR)
	$(PYTHON) fg_sim.py
	@touch $@

$(STAMP_DIR)/fg_bar_race: fg_bar_race.py $(STAMP_DIR)/fg_sim | $(STAMP_DIR)
	$(PYTHON) fg_bar_race.py
	@touch $@

# -----------------------------------------------------------------------------
# LaTeX report  (two passes to resolve TOC + cross-references)
# -----------------------------------------------------------------------------

canada_pop_report.pdf: canada_pop_report.tex $(STAMP_DIR)/sim $(STAMP_DIR)/extra
	$(PDFLATEX) canada_pop_report.tex
	$(PDFLATEX) canada_pop_report.tex

# -----------------------------------------------------------------------------
# Clean targets
# -----------------------------------------------------------------------------

clean: clean-plots clean-report

clean-plots:
	rm -rf plots/

clean-report:
	rm -f canada_pop_report.pdf \
	      canada_pop_report.aux \
	      canada_pop_report.log \
	      canada_pop_report.out \
	      canada_pop_report.toc
