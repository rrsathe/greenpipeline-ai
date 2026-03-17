"""Carbon Estimator — estimate CI/CD pipeline carbon emissions.

Directly imports from the local ``codecarbon/`` repository:
  - ``codecarbon.OfflineEmissionsTracker`` for hardware-based estimation
  - ``codecarbon.core.units.Energy`` for energy unit conversions
  - ``codecarbon.core.emissions.Emissions`` for carbon-intensity lookups
  - ``codecarbon.input.DataSource`` for emission-factor data

Falls back to a physics-based model when CodeCarbon cannot initialise
(e.g. unsupported hardware).
"""

from __future__ import annotations

import logging
import time
from typing import Any, cast

import greenpipeline._paths  # noqa: F401 — activate local repo paths
from greenpipeline import CarbonReport, PipelineDAG

logger = logging.getLogger(__name__)
_codecarbon_logger = logging.getLogger("codecarbon")
_codecarbon_logger.setLevel(logging.ERROR)
_codecarbon_logger.propagate = False
_codecarbon_logger.disabled = True
logging.getLogger("codecarbon.emissions_tracker").setLevel(logging.ERROR)
OfflineEmissionsTracker = cast(Any, None)
Energy = cast(Any, None)
EmissionsPerKWh = cast(Any, None)
Emissions = cast(Any, None)
DataSource = cast(Any, None)

# ---- Local CodeCarbon imports ----
try:
    from codecarbon import OfflineEmissionsTracker  # local repo
    from codecarbon.core.emissions import Emissions
    from codecarbon.core.units import EmissionsPerKWh, Energy
    from codecarbon.input import DataSource

    _HAS_CODECARBON = True
except Exception as _err:
    logger.warning("Could not import local codecarbon: %s", _err)
    _HAS_CODECARBON = False

# Default assumptions
_DEFAULT_COUNTRY = "USA"
_BASE_POWER_WATTS = 50.0
_FALLBACK_CARBON_INTENSITY = 0.42  # kg CO2 / kWh — US average


# ---------------------------------------------------------------------------
# Internal estimators
# ---------------------------------------------------------------------------


def _try_codecarbon_estimate(
    duration_min: float, country: str = _DEFAULT_COUNTRY
) -> dict:
    """Use the local CodeCarbon ``OfflineEmissionsTracker`` for estimation.

    Returns dict with ``emissions_kg`` and ``energy_kwh``, or empty dict
    on failure.
    """
    if not _HAS_CODECARBON:
        return {}

    try:
        tracker = OfflineEmissionsTracker(
            country_iso_code=country,
            project_name="greenpipeline_estimate",
            log_level="error",
            save_to_file=False,
            save_to_api=False,
            measure_power_secs=1,
            allow_multiple_runs=False,
        )
        tracker.start()

        # Scale: 1 pipeline-minute → 0.1s real-time CPU simulation, cap at 1.5s for snappy UI
        sim_secs = min(duration_min * 0.1, 1.5)
        _simulate_cpu_work(sim_secs)

        emissions_kg: float = tracker.stop() or 0.0

        # Scale emissions proportionally to full pipeline duration
        scale_factor = (duration_min * 60.0) / sim_secs if sim_secs > 0 else 1.0

        # Get the Energy object that CodeCarbon tracked
        total_energy = getattr(tracker, "_total_energy", None)
        energy_kwh = float(getattr(total_energy, "kWh", 0.0))

        return {
            "emissions_kg": emissions_kg * scale_factor,
            "energy_kwh": energy_kwh * scale_factor,
        }
    except Exception as e:
        logger.warning("CodeCarbon tracker failed, using fallback: %s", e)
        return {}


def _codecarbon_data_estimate(
    duration_min: float, country: str = _DEFAULT_COUNTRY
) -> dict:
    """Use CodeCarbon's ``Emissions`` + ``DataSource`` for emission-factor
    lookup *without* spinning up the full hardware tracker.

    This is the lightweight approach — we compute energy from assumed
    power draw and then apply CodeCarbon's country-level carbon intensity.
    """
    if not _HAS_CODECARBON:
        return {}

    try:
        hours = duration_min / 60.0
        energy = Energy.from_energy(kWh=(_BASE_POWER_WATTS / 1000.0) * hours)

        data_source = DataSource()
        Emissions(data_source)

        # Use CodeCarbon's global energy-mix data for the country
        energy_mix = data_source.get_global_energy_mix_data()
        if country in energy_mix:
            country_mix = energy_mix[country]
            eps = Emissions._global_energy_mix_to_emissions_rate(country_mix)
            emissions_kg = eps.kgs_per_kWh * energy.kWh
        else:
            # Fallback to world average from CodeCarbon's data
            ci_data = data_source.get_carbon_intensity_per_source_data()
            world_avg = ci_data.get("world_average", 475)  # g CO2/kWh
            eps = EmissionsPerKWh.from_g_per_kWh(world_avg)
            emissions_kg = eps.kgs_per_kWh * energy.kWh

        return {
            "emissions_kg": emissions_kg,
            "energy_kwh": energy.kWh,
        }
    except Exception as e:
        logger.warning("CodeCarbon data-based estimate failed: %s", e)
        return {}


def _fallback_estimate(duration_min: float) -> dict:
    """Simple physics-based fallback when CodeCarbon is unavailable."""
    hours = duration_min / 60.0
    energy_kwh = (_BASE_POWER_WATTS / 1000.0) * hours
    emissions_kg = energy_kwh * _FALLBACK_CARBON_INTENSITY
    return {"emissions_kg": emissions_kg, "energy_kwh": energy_kwh}


def _simulate_cpu_work(seconds: float) -> None:
    """Lightweight CPU work to give CodeCarbon something to measure."""
    end = time.monotonic() + seconds
    x = 0.0
    while time.monotonic() < end:
        for _ in range(10_000):
            x += 1.0
        x = 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def estimate_emissions(
    dag: PipelineDAG,
    optimized_runtime_min: float | None = None,
    country: str = _DEFAULT_COUNTRY,
) -> CarbonReport:
    """Estimate carbon emissions for the current and optimised pipeline.

    Estimation strategy (ordered by preference):
        1. CodeCarbon ``OfflineEmissionsTracker`` — real hardware measurement
        2. CodeCarbon ``DataSource`` + ``Emissions`` — data-file lookup
        3. Physics fallback — constant power draw × grid average

    Args:
        dag: The pipeline DAG with runtime estimates.
        optimized_runtime_min: Optimised critical-path runtime.
        country: ISO 3166-1 alpha-3 country code for carbon intensity.

    Returns:
        :class:`CarbonReport` with current and optimised emissions.
    """
    current_runtime = dag.critical_path_min
    opt_runtime = (
        optimized_runtime_min if optimized_runtime_min is not None else current_runtime
    )

    # Try each estimator in order of preference
    current_est = _try_codecarbon_estimate(current_runtime, country)
    if not current_est:
        current_est = _codecarbon_data_estimate(current_runtime, country)
    if not current_est:
        current_est = _fallback_estimate(current_runtime)

    # Scale optimised estimate proportionally
    ratio = opt_runtime / current_runtime if current_runtime > 0 else 1.0
    opt_emissions_kg = current_est["emissions_kg"] * ratio
    opt_energy_kwh = current_est["energy_kwh"] * ratio

    return compute_carbon_delta(
        current_emissions_kg=current_est["emissions_kg"],
        optimized_emissions_kg=opt_emissions_kg,
        current_energy_kwh=float(current_est["energy_kwh"]),
        optimized_energy_kwh=float(opt_energy_kwh),
    )


def compute_carbon_delta(
    current_emissions_kg: float,
    optimized_emissions_kg: float,
    current_energy_kwh: float = 0.0,
    optimized_energy_kwh: float = 0.0,
) -> CarbonReport:
    """Compute the delta between current and optimised emissions.

    Args:
        current_emissions_kg: Current pipeline emissions in kg CO₂.
        optimized_emissions_kg: Optimised pipeline emissions in kg CO₂.
        current_energy_kwh: Current energy consumption.
        optimized_energy_kwh: Optimised energy consumption.

    Returns:
        :class:`CarbonReport`.
    """
    delta = current_emissions_kg - optimized_emissions_kg
    pct = (delta / current_emissions_kg * 100.0) if current_emissions_kg > 0 else 0.0

    return CarbonReport(
        current_emissions_kg=round(current_emissions_kg, 6),
        optimized_emissions_kg=round(optimized_emissions_kg, 6),
        delta_emissions_kg=round(delta, 6),
        reduction_pct=round(pct, 1),
        current_energy_kwh=round(current_energy_kwh, 6),
        optimized_energy_kwh=round(optimized_energy_kwh, 6),
    )
