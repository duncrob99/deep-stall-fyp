#!/usr/bin/env python
from math import sqrt, pi, log
from numpy import linspace, geomspace, loadtxt
import numpy as np
import matplotlib.pyplot as plt

def get_airfoil_area(airfoil: str):
    # with open(f"{airfoil}_XYZ.csv") as file:
    x, y, z = loadtxt(f"{airfoil}_XYZ.csv", unpack=True, delimiter=",")
    area = 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))
    cord = np.max(x) - np.min(x)
    return area / cord
       

def get_wing_weight(S):
    area_per_cord = get_airfoil_area("NACA2318")  # of airfoil [m^2/m]
    volume = area_per_cord * S
    density = 20 # kg / m^3
    
    return volume * density


def main():
    # Deep Stall Sizing Calculator
    # Author: Adam Mercuri
    # FYP: Deep Stall Year


    # ---- INPUTS ----
    # Known component masses
    m_electronics = 0.038 + 0.050     # Pixhawk board = 0.038 [kg]
    m_motor = lambda pwr: 0.07 if pwr > 444 else 0.056     # batteries [kg]
    m_battery = lambda cap: cap/(27.514*log(cap) + 38.165) # Weight of battery, from correlation of energy density [kg]
    m_prop = lambda diam: diam * 0.1   # [kg]

    # Structural mass model
    struct_frac = 0.3    # structure fraction of total mass (initial guess)

    # Flight conditions
    V_DS   = 4.5          # deep stall trim speed [m/s]
    CL_DS  = 2         # CL at deep stall
    Vs     = 10.0         # normal stall speed [m/s]
    CLmax  = 1.6          # CLmax normal flight
    rho    = 1.225        # air density [kg/m^3]
    duration = 1/6        # Flight duration [hr]

    # Geometry
    AR     = 5.0          # aspect ratio for wing   (might need to change)
    St     = 0.25         # tail area [m^2] (initial guess)
    xw     = 0.05         # wing AC to CG [m]
    xt     = 0.50         # tail AC to CG [m]
    zT     = 0.05         # thrust line offset [m]
    chi    = 0.7          # fraction of lift on wing

    # Propeller
    D_range      = geomspace(0.08, 0.8, 30)         # diameter [m]
    eta    = 0.6          # efficiency

    # Air properties
    nu     = 1.5e-5       # kinematic viscosity [m^2/s]

    def calculate_results(D):
        # ---- ITERATION ----
        m_guess = m_electronics + m_motor(300) + m_battery(1) + 0.3 # initial guess with ~0.3 kg structure
        tol = 1e-3       # convergence tolerance
        diff = 1.0
        iter = 0

        while diff > tol and iter < 100:
            iter = iter + 1
            W = m_guess*9.81

            # Required wing area from deep stall
            S_DS = W / (rho*(V_DS**2)*CL_DS)
            # Normal stall check
            S_stall = W / (0.5*rho*Vs**2*CLmax)
            S = max(S_DS, S_stall)

            # Estimate structural mass as fraction of total
            m_struct = struct_frac * m_guess

            # Propulsion
            W = m_guess*9.81
            T = W/sqrt(2)
            A = pi*(D**2)/4
            vi = sqrt(T/(2*rho*A))
            P_induced = T*vi
            P_elec = P_induced/eta
            bat_capacity = P_elec * duration

            # New total mass = known + structure
            m_new = m_electronics + m_motor(P_elec) + m_battery(bat_capacity) + m_prop(D) + m_struct + get_wing_weight(S)

            # Convergence check
            diff = abs(m_new - m_guess)
            m_guess = 0.5*(m_new + m_guess) # relaxation
        
        # Geometry
        b = sqrt(AR*S)
        c = S/b


        m = m_guess
        return locals()
        

    m_results = []
    for D in D_range:
        results = calculate_results(D)

        m_results.append(results["m"])

    D = D_range[np.argmin(m_results)]

    # ---- FINAL CALCULATIONS ----
    results = calculate_results(D)
    m = results["m"]
    W = m*9.81

    # Dynamic pressure
    q = 0.5*rho*V_DS**2

    # Lift
    L_total = W/2
    Lw = chi*L_total
    Lt = (1-chi)*L_total

    # Lift coeffs
    CL_total = W/(rho*V_DS**2*results["S"])
    CLw = Lw/(q*results["S"])
    CLt = Lt/(q*St)

    # Thrust requirement
    T = W/sqrt(2)

    # Moment balance
    M_CG = Lw*xw - Lt*xt - T*zT # assuming no zero-lift moments

    # Reynolds
    Re_DS = V_DS*results["c"]/nu
    Re_cruise = 15*results["c"]/nu

    # ---- OUTPUT ----
    print('\n--- Self-Sized Deep-Stall Aircraft ---')
    print('Iterations to converge: %d' % results["iter"])
    print('Total Mass m           = %.3f kg' % results["m"])
    print('Weight W               = %.2f N' % W)
    print('Wing Area S            = %.3f m^2' % results["S"])
    print('Span b                 = %.3f m' % results["b"])
    print('Chord c                = %.3f m' % results["c"])
    print('Wing Loading W/S       = %.2f N/m^2' % (W/results["S"]))
    print('Re @ V_DS=%.1f m/s     = %.2e' % (V_DS, Re_DS))
    print('Re @ 15 m/s            = %.2e' % Re_cruise)

    print('\n--- Lift & Thrust ---')
    print('Required Thrust T      = %.2f N' % results["T"])
    print('Propeller diameter     = %.3f m' % D)
    print('Wing Lift Lw           = %.2f N , CLw = %.2f' % (Lw, CLw))
    print('Tail Lift Lt           = %.2f N , CLt = %.2f' % (Lt, CLt))

    print('\n--- Pitching Moment ---')
    print('Net M_CG               = %.2f N·m (nose-up +)' % M_CG)

    print('\n--- Propulsion Power ---')
    print('Induced Velocity vi    = %.2f m/s' % results["vi"])
    print('Induced Power          = %.2f W' % results["P_induced"])
    print('Electrical Power       = %.2f W' % results["P_elec"])
    print('Battery capacity       = %.2f Wh' % results["bat_capacity"])
    print('Battery weight         = %.2f kg' % m_battery(results["bat_capacity"]))


    fig, ax = plt.subplots()
    ax.plot(D_range, m_results)
    plt.show()



if __name__ == "__main__":
    main()
