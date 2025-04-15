from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime, timedelta
import os

# Config
start_date = datetime.strptime("2025/04/13", "%Y/%m/%d")
end_date = datetime.today()
data_file = "hkjc_results.csv"
log_file = "collected_dates.txt"

# Set up Selenium
options = Options()
# options.add_argument("--headless")  # Uncomment for headless mode
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Load previously collected dates
if os.path.exists(log_file):
    with open(log_file, "r") as f:
        collected_dates = set(f.read().splitlines())
else:
    collected_dates = set()

# Loop through dates
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime("%Y/%m/%d")
    log_str = current_date.strftime("%Y-%m-%d")
    all_results = []

    if log_str in collected_dates:
        current_date += timedelta(days=1)
        continue

    print(f"Processing {date_str}...")
    url = f"https://racing.hkjc.com/racing/information/Chinese/Racing/ResultsAll.aspx?RaceDate={date_str}"
    driver.get(url)

    try:
        # Wait for race table
        WebDriverWait(driver, 10).until(
            #EC.presence_of_element_located((By.XPATH, '//table[contains(@class, "table_bd") and contains(@class, "f_fs13")]'))
            EC.presence_of_element_located((By.XPATH, '//table[contains(@class, "f_fs13")]'))
            
        )

        # Now collect tables
        #race_tables = driver.find_elements(By.XPATH, '//table[@class="f_tac table_bd f_fs13"]')
        race_tables = driver.find_elements(By.XPATH, '//table[contains(@class, "f_fs13")]')

    except Exception as e:
        print(f"⚠️ Timeout or error: No race table found for {date_str} — {e}")
        current_date += timedelta(days=1)
        continue
    
    #race_headers = driver.find_elements(By.XPATH, '//div[@class="f_fs18 f_fwb"]')
    race_headers = driver.find_elements(By.XPATH, '//div[contains(@class, "f_fs18")]')
    

    try:
        if not race_tables:
            print(f"No data for {date_str}")
        else:
            for race_table in race_tables:
                rows = race_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 7:
                        result = {
                            "日期": log_str,
                            "名次": cols[0].text,
                            "馬號": cols[1].text,
                            "馬名": cols[2].text,
                            "騎師": cols[3].text,
                            "練馬師": cols[4].text,
                            "負磅": cols[5].text,
                            "檔位": cols[6].text,
                        }
                        all_results.append(result)

            # Save to CSV
            df = pd.DataFrame(all_results)
            if not df.empty:
                if not os.path.exists(data_file):
                    df.to_csv(data_file, index=False, encoding="utf-8-sig")
                else:
                    df.to_csv(data_file, mode='a', header=False, index=False, encoding="utf-8-sig")
                print(f"✔ Saved data for {log_str}")

    except Exception as e:
        print(f"❌ Error on {date_str}: {e}")

    # Mark as collected
    with open(log_file, "a") as f:
        f.write(log_str + "\n")

    collected_dates.add(log_str)
    current_date += timedelta(days=1)


    # Important: switch back to main page
    driver.switch_to.default_content()

# Done
driver.quit()
