"""
LVRT (Low Voltage Ride-Through) Compliance Checker
===================================================

Author : Devanshu Shrivastava
         MEng in Energy Systems, Rutgers University, New Brunswick, NJ
Date   : June 9, 2026

WHAT THIS IS
------------
Grid codes are the rulebook that any power plant must follow to connect to
the electrical grid. One of the most important rules is Low Voltage
Ride-Through (LVRT): when a fault on the grid causes a brief voltage dip,
generators (wind farms, solar plants, conventional units) must STAY CONNECTED
for a defined time instead of disconnecting. If every plant tripped off during
a dip, the grid would lose a huge chunk of generation at the worst possible
moment, which can cascade into a blackout.

The grid code defines this requirement as a voltage-vs-time ENVELOPE.
The rule is:
  * If the grid voltage stays ON or ABOVE the envelope -> the generator
    MUST remain connected (it must "ride through" the fault).
  * If the voltage drops BELOW the envelope -> the generator is PERMITTED
    to disconnect.

WHAT THIS SCRIPT DOES
---------------------
  1. Defines an LVRT envelope based on a representative grid code.
  2. Takes a measured/simulated voltage profile during a fault.
  3. Checks at every instant whether the voltage is inside the
     must-ride-through region, and prints an overall verdict.
  4. Plots the envelope, the two regions, and the voltage trace.

Voltage is expressed in PER UNIT (pu): 1.0 pu = nominal voltage,
0.0 pu = complete voltage collapse. Per unit is standard in power systems
because it lets you compare any voltage level on the same scale.
"""

import numpy as np
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# 1. THE GRID CODE: define the LVRT envelope
# ----------------------------------------------------------------------
# Each point is (time_seconds, minimum_voltage_pu). Together they form the
# lower boundary the voltage is allowed to follow during/after a fault.
# This shape is REPRESENTATIVE / illustrative -- the exact numbers differ
# between countries and codes (e.g. Germany's VDE-AR-N 4120, GB Grid Code,
# Spain's P.O. 12.3). The shape, however, is universal:
#   collapse allowed briefly -> ramped recovery -> hold near nominal.
LVRT_ENVELOPE = [
    (0.00, 0.00),   # fault inception: voltage may collapse all the way to 0
    (0.15, 0.00),   # must ride through 0 pu for the first 150 ms
    (1.50, 0.90),   # voltage must recover to 0.90 pu by 1.5 s (linear ramp)
    (10.0, 0.90),   # hold at 0.90 pu afterwards
]


def envelope_voltage(t):
    """Return the minimum required voltage (pu) at time t (s).

    Uses linear interpolation between the envelope points -- exactly how
    the boundary is read off the grid-code curve.
    """
    times = [p[0] for p in LVRT_ENVELOPE]
    volts = [p[1] for p in LVRT_ENVELOPE]
    return np.interp(t, times, volts)


# ----------------------------------------------------------------------
# 2. A FAULT SCENARIO: the voltage actually seen at the plant
# ----------------------------------------------------------------------
def fault_voltage(t, dip_to=0.20, fault_clear=0.12, recovered=0.60):
    """Simulate the per-unit voltage at the connection point during a fault.

    Parameters
    ----------
    dip_to      : voltage during the fault (pu)
    fault_clear : time the protection clears the fault (s)
    recovered   : time the voltage is fully restored (s)
    """
    v = np.ones_like(t)                      # 1.0 pu before the fault
    during = (t >= 0) & (t < fault_clear)
    v[during] = dip_to                       # collapsed during the fault
    recovering = (t >= fault_clear) & (t < recovered)
    # linear recovery from dip_to back up to 1.0 pu
    v[recovering] = dip_to + (1.0 - dip_to) * \
        (t[recovering] - fault_clear) / (recovered - fault_clear)
    v[t >= recovered] = 1.0
    return v


# ----------------------------------------------------------------------
# 3. THE COMPLIANCE CHECK
# ----------------------------------------------------------------------
def check_compliance(t, v):
    """Compare a voltage trace against the LVRT envelope.

    Returns
    -------
    must_ride : boolean array, True where voltage is in the
                must-stay-connected region (voltage >= envelope).
    verdict   : human-readable string.
    first_violation : time of the first dip below the envelope, or None.
    """
    required = envelope_voltage(t)
    must_ride = v >= required
    # only look at the fault window (t >= 0); before the fault is irrelevant
    window = t >= 0
    below = window & (v < required)
    if not below.any():
        return must_ride, ("COMPLIANT: voltage stays on/above the envelope "
                           "for the whole event -> the generator is REQUIRED "
                           "to ride through and must NOT trip."), None
    first_violation = float(t[below][0])
    return must_ride, (f"BELOW ENVELOPE at t = {first_violation:.3f} s -> the "
                       "generator is PERMITTED to disconnect from this point."), \
        first_violation


# ----------------------------------------------------------------------
# 4. RUN + PLOT
# ----------------------------------------------------------------------
def main():
    t = np.linspace(-0.2, 3.0, 2000)        # time axis, fault starts at t=0
    v = fault_voltage(t)
    must_ride, verdict, first_violation = check_compliance(t, v)

    print("=" * 64)
    print("LVRT COMPLIANCE CHECK")
    print("=" * 64)
    print(verdict)
    print(f"Lowest voltage seen : {v[t >= 0].min():.3f} pu")
    print(f"Envelope minimum    : {min(p[1] for p in LVRT_ENVELOPE):.3f} pu")
    print("=" * 64)

    # --- figure ---
    fig, ax = plt.subplots(figsize=(9, 5.5))

    # envelope as a dense line so we can shade above/below it
    t_env = np.linspace(0, 3.0, 1000)
    v_env = envelope_voltage(t_env)

    # shade the two regions
    ax.fill_between(t_env, v_env, 1.2, color="#cfe8d4", alpha=0.7,
                    label="Must stay connected (ride through)")
    ax.fill_between(t_env, 0.0, v_env, color="#f4cccc", alpha=0.7,
                    label="May disconnect")

    # the envelope boundary
    ax.plot(t_env, v_env, color="#333333", lw=2, ls="--",
            label="LVRT envelope (grid code)")

    # the measured voltage trace
    ax.plot(t, v, color="#1f5fa8", lw=2.5, label="Voltage at plant (fault)")

    # cosmetics
    ax.axvline(0, color="gray", lw=0.8, ls=":")
    ax.set_xlim(-0.2, 3.0)
    ax.set_ylim(0, 1.2)
    ax.set_xlabel("Time after fault inception (s)")
    ax.set_ylabel("Voltage (per unit)")
    status = "COMPLIANT" if first_violation is None else "BELOW ENVELOPE"
    ax.set_title(f"LVRT Compliance Checker  -  result: {status}")
    ax.legend(loc="lower right", framealpha=0.95)
    ax.grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig("lvrt_compliance.png", dpi=150)
    print("Plot saved to lvrt_compliance.png")


if __name__ == "__main__":
    main()
