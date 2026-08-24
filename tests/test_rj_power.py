"""Testes do módulo de poder prospectivo (rj_power).

Não re-testam o judge (isso é do power gate) — testam que a FERRAMENTA de
análise de poder se comporta: monotonicidade (efeito maior => poder maior),
MDE coerente com o grid, e determinismo por seed.
"""
import copy
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import rj_power


def _fast_cfg():
    with open(ROOT / "config_rj.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg = copy.deepcopy(cfg)
    cfg["judge"]["n_boot"] = 200
    return cfg


def test_power_is_monotone_in_effect_size():
    cfg = _fast_cfg()
    p_small = rj_power.simulate_power(cfg, n_companies=30, planted_effect=0.5,
                                      n_reps=10, seed=5)
    p_large = rj_power.simulate_power(cfg, n_companies=30, planted_effect=2.5,
                                      n_reps=10, seed=5)
    assert p_large >= p_small
    assert p_large >= 0.5   # efeito de 2.5sd em N=30 tem que aparecer


def test_simulate_power_is_deterministic():
    cfg = _fast_cfg()
    a = rj_power.simulate_power(cfg, n_companies=20, planted_effect=1.0,
                                n_reps=8, seed=42)
    b = rj_power.simulate_power(cfg, n_companies=20, planted_effect=1.0,
                                n_reps=8, seed=42)
    assert a == b


def test_minimum_detectable_effect_reads_grid():
    grid = {(20, 0.5): 0.2, (20, 1.0): 0.6, (20, 1.5): 0.85, (20, 2.0): 0.95,
            (40, 0.5): 0.5, (40, 1.0): 0.9}
    assert rj_power.minimum_detectable_effect(grid, 20) == 1.5
    assert rj_power.minimum_detectable_effect(grid, 40) == 1.0
    assert rj_power.minimum_detectable_effect(grid, 99) is None


def test_format_grid_renders_all_cells():
    grid = {(20, 1.0): 0.5, (20, 2.0): 0.9, (40, 1.0): 0.7, (40, 2.0): 1.0}
    text = rj_power.format_grid(grid, [20, 40], [1.0, 2.0])
    assert "50%" in text and "100%" in text
