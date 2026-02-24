#!/usr/bin/env python3
"""
Internal Cost Model Analysis
Calculates the fully-loaded cost of district employees vs. contractor rates
to determine the "Lost Efficiency" (premium paid to staffing agencies).
"""

# --- CONSTANTS (2024-2025 Rates) ---

# Benefit Rates
SEBB_MONTHLY_RATE = 1178.00     # Employer contribution
DRS_RETIREMENT_RATE = 0.0911    # 9.11% for PERS/TRS
FICA_MEDICARE_RATE = 0.0765     # 7.65% standard standard FICA
WORKERS_COMP_UI_EST = 0.01      # 1% standard estimate

# Contract Assumptions
CONTRACT_DAYS = 180
HOURS_PER_DAY = 7.5
ANNUAL_HOURS = CONTRACT_DAYS * HOURS_PER_DAY  # 1,350 hours/year
MONTHS_PAID = 12

# Base Hourly Rates (From CBA/Salary Schedules)
# SLP/RN (Certificated, MA+0 Step 5 estimate)
SLP_BASE_HOURLY = 49.63
# Special Program Paraeducator (VAESP, Step 3 estimate)
PARA_BASE_HOURLY = 25.40

# Reported Vendor Rates (From Investigation)
VENDOR_RATE_SLP_LOW = 100.00
VENDOR_RATE_SLP_HIGH = 150.00
VENDOR_RATE_PARA_LOW = 50.00
VENDOR_RATE_PARA_HIGH = 75.00
# Sourced from general contracts / Amergis standard rates

def calculate_fully_loaded_hourly(base_hourly):
    """Calculates fully loaded hourly rate including all overhead."""
    annual_base_salary = base_hourly * ANNUAL_HOURS
    
    # Overhead Costs
    annual_sebb = SEBB_MONTHLY_RATE * MONTHS_PAID
    annual_drs = annual_base_salary * DRS_RETIREMENT_RATE
    annual_fica = annual_base_salary * FICA_MEDICARE_RATE
    annual_wc = annual_base_salary * WORKERS_COMP_UI_EST
    
    total_annual_cost = annual_base_salary + annual_sebb + annual_drs + annual_fica + annual_wc
    fully_loaded_hourly = total_annual_cost / ANNUAL_HOURS
    
    return {
        "base_hourly": base_hourly,
        "annual_salary": annual_base_salary,
        "annual_benefits": annual_sebb + annual_drs + annual_fica + annual_wc,
        "total_annual_cost": total_annual_cost,
        "fully_loaded_hourly": fully_loaded_hourly,
        "benefit_multiplier": fully_loaded_hourly / base_hourly
    }

def print_comparison(role_name, loaded_data, vendor_low, vendor_high):
    print(f"=== {role_name.upper()} COST COMPARISON ===")
    print(f"District Base Rate:       ${loaded_data['base_hourly']:.2f} / hr")
    print(f"District Fully Loaded:    ${loaded_data['fully_loaded_hourly']:.2f} / hr (Mult: {loaded_data['benefit_multiplier']:.2f}x)")
    print(f"Vendor Rate Range:        ${vendor_low:.2f} - ${vendor_high:.2f} / hr")
    
    # Efficiency calculations
    premium_low = vendor_low - loaded_data['fully_loaded_hourly']
    premium_high = vendor_high - loaded_data['fully_loaded_hourly']
    
    pct_premium_low = (premium_low / loaded_data['fully_loaded_hourly']) * 100
    pct_premium_high = (premium_high / loaded_data['fully_loaded_hourly']) * 100
    
    print(f"Lost Efficiency (Premium paid per hour):")
    print(f"  Conservative: +${premium_low:.2f}/hr (+{pct_premium_low:.1f}%)")
    print(f"  Aggressive:   +${premium_high:.2f}/hr (+{pct_premium_high:.1f}%)")
    
    print(f"Annualized Lost Efficiency (per 1 FTE @ {ANNUAL_HOURS} hrs):")
    print(f"  Conservative: ${premium_low * ANNUAL_HOURS:,.2f} lost to agency overhead")
    print(f"  Aggressive:   ${premium_high * ANNUAL_HOURS:,.2f} lost to agency overhead")
    print()

def main():
    print("--- INTERNAL COST MODEL (FY 24-25 ESTIMATES) ---\n")
    
    slp_loaded = calculate_fully_loaded_hourly(SLP_BASE_HOURLY)
    para_loaded = calculate_fully_loaded_hourly(PARA_BASE_HOURLY)
    
    print_comparison("Specialized Certificated (e.g. SLP/RN, MA+0 Step 5)", slp_loaded, VENDOR_RATE_SLP_LOW, VENDOR_RATE_SLP_HIGH)
    print_comparison("Special Program Paraeducator (Step 3)", para_loaded, VENDOR_RATE_PARA_LOW, VENDOR_RATE_PARA_HIGH)

if __name__ == "__main__":
    main()
