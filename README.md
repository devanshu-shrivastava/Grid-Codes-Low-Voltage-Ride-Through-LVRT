# LVRT Compliance Checker

A small power-systems tool that checks whether a generator is required to
**ride through** a grid voltage dip, according to a grid code's
**Low Voltage Ride-Through (LVRT)** requirement.

**Author:** Devanshu Shrivastava
MEng Energy Systems
Rutgers University, New Brunswick, NJ
**Date:** June 9, 2026

## Background

A *grid code* is the set of technical rules a power plant must follow to
connect to the electrical grid. One key rule is **LVRT**: during a short
voltage dip caused by a fault, generators must **stay connected** for a
defined time rather than tripping off. If many plants disconnected at once
during a dip, the grid could lose enough generation to cascade into a
blackout — a real concern as wind and solar (whose early inverters tripped
easily) became a large share of generation.

The requirement is defined as a **voltage-vs-time envelope**:

- Voltage **on or above** the envelope → the generator **must stay connected**.
- Voltage **below** the envelope → the generator **may disconnect**.

## What this does

1. Defines a representative LVRT envelope (collapse allowed briefly → ramped
   recovery → hold near nominal voltage).
2. Simulates the voltage seen at the plant during a fault.
3. Checks, at every instant, whether the voltage is inside the
   must-ride-through region and prints a verdict.
4. Plots the envelope, the two regions, and the voltage trace.

## Run it

```bash
pip install numpy matplotlib
python lvrt_checker.py
```

This prints the compliance verdict and saves `lvrt_compliance.png`.

## Try it yourself

Edit the fault in `main()` to make it more severe and watch the verdict flip:

```python
v = fault_voltage(t, dip_to=0.05, fault_clear=0.30, recovered=2.0)
```

A deeper, longer dip pushes the voltage **below** the envelope, so the
generator is then permitted to disconnect.

## Notes

Voltages are in **per unit (pu)**: 1.0 = nominal, 0.0 = full collapse.
The envelope shape is illustrative; exact numbers vary by code (e.g. Germany's
VDE-AR-N 4120, the GB Grid Code, Spain's P.O. 12.3), but the shape is universal.

## Possible extensions

- Load a real envelope from a published grid code.
- Read a recorded voltage trace (CSV) instead of a simulated one.
- Add the **reactive-current injection** requirement (plants must feed
  reactive current during the dip to help the grid recover).
- Add **High Voltage Ride-Through (HVRT)** for over-voltage events.
