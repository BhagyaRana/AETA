import datetime
import sys
from typing import Optional, Tuple, List
import os
import pandas as pd
import itertools
from aeta_function import aeta_function

ALL_COMPANIES = ["JPM", "MS", "BAC", "SF", "AMP", "RJF", "LPL", "UBS", "SCHW", "WFC"]
ALL_QUARTERS = ["1", "2", "3", "4"]

def get_user_input() -> Tuple[datetime.datetime, str, str]:
    # Date input
    while True:
        try:
            date_input = input("Enter the date (YYYY-MM-DD): ")
            year, month, day = map(int, date_input.split('-'))
            date = datetime.date(year, month, day)
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    # Time input
    while True:
        try:
            time_input = input("Enter the time in IST (HH:MM:SS): ")
            hour, minute, second = map(int, time_input.split(':'))
            time = datetime.time(hour, minute, second)
            break
        except ValueError:
            print("Invalid time format. Please use HH:MM:SS.")

    # Combine date and time
    schedule_time = datetime.datetime.combine(date, time)

    # Company input (optional)
    companies = ALL_COMPANIES + ["All"]
    company = input(f"Enter the company (optional, press Enter for 'All'): ")
    if company and company not in companies:
        print(f"Invalid company. Using 'All'. Valid options are: {', '.join(companies)}")
        company = "All"
    elif not company:
        company = "All"

    # Quarter input (optional)
    quarters = ALL_QUARTERS + ["All"]
    quarter = input(f"Enter the quarter (optional, press Enter for 'All'): ")
    if quarter and quarter not in quarters:
        print(f"Invalid quarter. Using 'All'. Valid options are: {', '.join(quarters)}")
        quarter = "All"
    elif not quarter:
        quarter = "All"

    return schedule_time, company, quarter

def save_to_excel(schedule_time: datetime.datetime, company: str, quarter: str):
    file_name = 'scheduler_inputs.xlsx'

    if company == "All":
        companies = ALL_COMPANIES
    else:
        companies = [company]

    if quarter == "All":
        quarters = ALL_QUARTERS
    else:
        quarters = [quarter]

    new_data = pd.DataFrame(list(itertools.product([schedule_time.date()], [schedule_time.time()], companies, quarters)),
                            columns=['Date', 'Time', 'Company', 'Quarter'])

    if os.path.exists(file_name):
        # If file exists, read it and append new data
        existing_data = pd.read_excel(file_name)
        updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    else:
        # If file doesn't exist, create new DataFrame
        updated_data = new_data

    # Save to Excel
    updated_data.to_excel(file_name, index=False)
    print(f"Input saved to {file_name}")

def aeta(companies: List[str], quarters: List[str], year: str):
    # This is a placeholder for the actual aeta function
    for company, quarter in itertools.product(companies, quarters):
        print(f"Running aeta function with company: {company}, year: {year} quarter: {quarter}")
        aeta_function(company, quarter, year)

def main():
    schedule_time, company, quarter = get_user_input()

    # Save inputs to Excel
    save_to_excel(schedule_time, company, quarter)

    # Calculate time difference
    now = datetime.datetime.now()
    time_diff = schedule_time - now

    if time_diff.total_seconds() < 0:
        print("The scheduled time is in the past. Please enter a future time.")
        sys.exit(1)

    print(f"Script scheduled to run at: {schedule_time}")
    print(f"Time until execution: {time_diff}")

    # Wait until the scheduled time
    while datetime.datetime.now() < schedule_time:
        pass

    # Execute the appropriate case
    companies = ALL_COMPANIES if company == "All" else [company]
    quarters = ALL_QUARTERS if quarter == "All" else [quarter]

    print(f"Executing aeta for companies: {companies} and quarters: {quarters}")
    year = datetime.datetime.now().year
    aeta(companies, quarters, year)

if __name__ == "__main__":
    main()