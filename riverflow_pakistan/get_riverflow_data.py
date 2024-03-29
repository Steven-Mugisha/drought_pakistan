""" 
    Author - Steven Mugisha Mizero 
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging
import pandas as pd

# from dotenv import load_dotenv

# the path to the folder:
# load_dotenv()
# path = os.getenv("path")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dataframe() -> pd.DataFrame:
    """
    Creates an empty dataframe with predefined columns.
    """

    column_names = [
        "Date",
        "LEVEL (FEET) INDUS AT TARBELA",
        "INFLOW INDUS AT TARBELA",
        "OUTFLOW INDUS AT TARBELA",
        "INFLOW KABUL AT NOWSHERA",
        "LEVEL (FEET) JEHLUM AT MANGLA",
        "INFLOW JEHLUM AT MANGLA",
        "OUTFLOW JEHLUM AT MANGLA",
        "INFLOW CHENAB AT MARALA",
        "CURRENT YEAR",
        "LAST YEAR",
        "AVG: Last 10-years",
    ]

    output_table = pd.DataFrame(columns=column_names)
    return output_table


def year_specific_dataframe(output_table: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Filters and transforms the dataframe for a specific year.
    """

    output_table_subset = output_table[
        [
            "Date",
            "INFLOW INDUS AT TARBELA",
            "INFLOW KABUL AT NOWSHERA",
            "INFLOW JEHLUM AT MANGLA",
            "INFLOW CHENAB AT MARALA",
        ]
    ]

    column_names = [
        "Date",
        "indus_at_tarbela (cfs)",
        "kabul_at_nowshera (cfs)",
        "jhelum_at_mangal (cfs)",
        "cheanab_at_marala (cfs)",
    ]

    output_table_subset.columns = column_names

    output_table_subset = output_table_subset.copy()
    output_table_subset["Date"] = output_table_subset["Date"].apply(
        lambda x: x.replace(" ", "-")
    )
    output_table_subset["Date"] = [
        f"{date_str}-{year}" for date_str in output_table_subset["Date"]
    ]
    output_table_subset["Date"] = pd.to_datetime(
        output_table_subset["Date"], format="%d-%b-%Y"
    ).dt.strftime("%Y-%m-%d")
    output_table_subset.set_index("Date", inplace=True)
    output_table_subset.index = pd.to_datetime(output_table_subset.index).strftime(
        "%Y-%m-%d"
    )
    out_put_year_df = output_table_subset.sort_index(ascending=True)

    return out_put_year_df


def get_year_riverflow_table(url, year) -> pd.DataFrame:
    """
    reads the data from the website and returns a dataframe for a specific year.
    """

    # defining selenium variables:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    # s = Service(f'{path}/chromedriver')
    with webdriver.Chrome(
        options=chrome_options, service=ChromeService(ChromeDriverManager().install())
    ) as driver:
        try:
            driver.get(url)
            # Use WebDriverWait to wait for the select element to be clickable
            select_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        ".MuiSelect-root.MuiSelect-select.MuiSelect-selectMenu.MuiSelect-outlined.MuiInputBase-input.MuiOutlinedInput-input",
                    )
                )
            )
            logger.info("Select element found.")

            # Click on the select element
            select_element.click()

            # Use WebDriverWait to wait for the year option to be clickable
            year_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[text()='{year}']"))
            )

            # Click on the year option
            year_option.click()
            logger.info(f"Selected the year: {year} option clicked")

            # Use WebDriverWait to wait for the table element to be present
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            logger.info("------------ Table found ------------")

            # list to contain the scraped table data:
            table_data = []
            for row in table.find_elements(By.TAG_NAME, "tr"):
                row_values = []
                for cell in row.find_elements(By.TAG_NAME, "td"):
                    row_values.append(cell.text.strip())
                if row_values:
                    table_data.append(row_values)

            # generate the dataframe for the scraped table data:
            output_table = create_dataframe()
            for row in table_data[:]:
                output_table.loc[len(output_table)] = row
                output_table = output_table.iloc[::-1]
            logger.info(f" The length of the table {len(output_table)}")

        except Exception as e:
            logger.error(f"------------Error: {e}------------")
            import traceback

            traceback.print_exc()

    return output_table


def custom_str_to_int(value):
    """
    Converts a string to an integer or float if possible on the scraped data.
    """
    try:
        parts = value.split(".")
        if len(parts) == 2:
            integer_part = int(parts[0])
            decimal_part = int(parts[1])
            return float(f"{integer_part}.{decimal_part}")
        else:
            return int(value)
    except ValueError:
        return value


def individual_year_data(url, threshold_days=60):
    """
    This function returns the data for the current year and the previous year.
    """
    # the years to be used:
    current_year = datetime.now().year
    previous_year = current_year - 1

    # to check which days missing from the dataframe:
    today = datetime.now()
    start_date = datetime(today.year, 1, 1)
    # The number of days since 1st of January:
    delta = today - start_date
    logger.info(
        f" ------------ The number of days since 1st of January: {delta.days} ------------ "
    )

    # the existing dataset:
    # recentYearsRiverFlow_df = pd.read_csv(f"{path}/riverflow.csv")
    recentYearsRiverFlow_df = pd.read_csv("riverflow.csv")

    # set the index to be the date column:
    recentYearsRiverFlow_df.set_index("Date", inplace=True)

    if current_year:
        current_year_table = get_year_riverflow_table(url, current_year)

        # if  (len(current_year_table) > threshold_days) & (len(current_year_table) == delta.days):
        if len(current_year_table) > threshold_days:
            current_year_table = year_specific_dataframe(
                current_year_table, current_year
            )
            # select the last index in the old and new dataframes:
            lastDate_newdata = current_year_table.index[-1]
            lastDate = recentYearsRiverFlow_df.index[-1]

            if lastDate != lastDate_newdata:
                before_threshold_day = pd.to_datetime(lastDate) - pd.Timedelta(
                    days=threshold_days
                )
                before_threshold_day = before_threshold_day.strftime("%Y-%m-%d")
                recentYearsRiverFlow_df = recentYearsRiverFlow_df[
                    recentYearsRiverFlow_df.index < before_threshold_day
                ]
                data_to_append = current_year_table[
                    current_year_table.index > before_threshold_day
                ]
                data_to_append = data_to_append.applymap(custom_str_to_int) * 1000
                data_to_append.index = pd.to_datetime(data_to_append.index)
                data_to_append["Year"] = data_to_append.index.year
                data_to_append.index = pd.to_datetime(data_to_append.index).strftime(
                    "%Y-%m-%d"
                )

                recentYearsRiverFlow_df = pd.concat(
                    [recentYearsRiverFlow_df, data_to_append], axis=0
                )
                logger.info(" ------------ Dataframes updated. ------------ ")

                # saving the data to csv:
                recentYearsRiverFlow_df.to_csv("riverflow.csv")
                logger.info(" ------------ Data saved to csv. ------------ ")

            # else:
            #     logger.info("Table data is not equal to the number of days since 1st of January")

        elif len((current_year_table) < threshold_days):
            logger.info(
                "Data available is less than the threshold days but equal to the number of days since 1st of January"
            )
            logger.info(f" The current year table length is: {len(current_year_table)}")
            logger.info("Get the previous year data to fill the gap")

            previous_year_table = get_year_riverflow_table(url, previous_year)
            previous_year_table = year_specific_dataframe(
                previous_year_table, previous_year
            )
            lastDate_newdata = previous_year_table.index[-1]
            logger.info(
                f" ------------------ Last date of new data is held here: {lastDate_newdata} ------------- "
            )

            days_to_get_from_previous_year = threshold_days - len(current_year_table)

            # get the last rows of the previous year table equal to the days_to_get_from_previous_year:
            logger.info(f" Reading the last year table to match the threshold days")
            previous_year_table = previous_year_table.tail(
                days_to_get_from_previous_year
            )

            # concat the two dataframes:
            combined_table = pd.concat(
                [previous_year_table, current_year_table], axis=0
            )
            # lastDate_combined_table = combined_table.index[-1]
            lastDate = recentYearsRiverFlow_df.index[-1]

            # Then get the last rows of the combined table equal to the threshold days:
            before_threshold_day = pd.to_datetime(lastDate) - pd.Timedelta(
                days=threshold_days
            )
            before_threshold_day = before_threshold_day.strftime("%Y-%m-%d")
            recentYearsRiverFlow_df = recentYearsRiverFlow_df[
                recentYearsRiverFlow_df.index < before_threshold_day
            ]
            data_to_append = combined_table[combined_table.index > before_threshold_day]
            data_to_append = data_to_append.applymap(custom_str_to_int) * 1000
            data_to_append.index = pd.to_datetime(data_to_append.index)
            data_to_append["Year"] = data_to_append.index.year
            data_to_append.index = pd.to_datetime(data_to_append.index).strftime(
                "%Y-%m-%d"
            )
            recentYearsRiverFlow_df = pd.concat(
                [recentYearsRiverFlow_df, data_to_append], axis=0
            )
            recentYearsRiverFlow_df["Year"] = recentYearsRiverFlow_df.index.year
            logger.info(" ------------ Dataframes updated. ------------ ")

            # saving the data to csv:
            recentYearsRiverFlow_df.to_csv("riverflow.csv")
            logger.info(" ------------ Data saved to csv. ------------ ")
        else:
            logger.info("No data at all")

    else:
        logger.info(" ------------ Current year not found. ----------- ")

    return current_year_table


if __name__ == "__main__":
    url = "https://www.wapda.gov.pk/river-flow"
    individual_year_data(url, threshold_days=60)
