from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# Chrome 설정 (Headless 모드)
chrome_options = Options()
chrome_options.add_argument("--headless")  # GUI 없이 실행
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# ChromeDriver 실행
service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

# KBO 경기 일정 페이지 접속
url = "https://www.koreabaseball.com/Schedule/GameCenter/Main.aspx"
driver.get(url)

# 대기 (최대 10초)
wait = WebDriverWait(driver, 10)

# ✅ (1) 드롭다운에서 "정규시즌 일정" 선택
try:
    series_dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "ddlSeries"))))
    series_dropdown.select_by_value("0,9,6")  # 정규시즌 값 선택
    time.sleep(3)  # 페이지가 다시 로드될 시간을 줌
    print("✅ 정규시즌 일정 선택 완료!")
except Exception as e:
    print("❌ 정규시즌 선택 실패:", e)
    driver.quit()
    exit()

# ✅ (2) 월별 데이터 가져오기
schedule_data = []

for month in range(3, 11):  # 3월 ~ 10월 정규시즌
    try:
        # 월 변경 버튼 클릭 (월별로 넘어가기)
        month_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"#ui-datepicker-div a[data-month='{month-1}']")))
        month_button.click()
        time.sleep(3)  # 페이지 로딩 대기
        print(f"📅 {month}월 경기 일정 가져오는 중...")

        # ✅ 경기 일정 테이블 로드 대기
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".tbl-type06 table#tblScheduleList")))

        # ✅ 경기 일정 테이블 가져오기
        schedule_table = driver.find_element(By.CSS_SELECTOR, ".tbl-type06 table#tblScheduleList tbody")
        rows = schedule_table.find_elements(By.TAG_NAME, "tr")

        # ✅ 데이터 추출
        current_date = ""
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if not cols:
                continue

            # 날짜가 rowspan으로 묶여 있는 경우
            if "day" in cols[0].get_attribute("class"):
                current_date = cols[0].text.strip()
                game_time = cols[1].text.strip()
                game_info = cols[2]
            else:
                game_time = cols[0].text.strip()
                game_info = cols[1]

            # 팀 및 점수 가져오기
            team_spans = game_info.find_elements(By.TAG_NAME, "span")
            if len(team_spans) == 5:
                team1 = team_spans[0].text.strip()
                score1 = team_spans[1].text.strip()
                team2 = team_spans[4].text.strip()
                score2 = team_spans[3].text.strip()
            else:
                team1 = team_spans[0].text.strip()
                team2 = team_spans[1].text.strip()
                score1 = "미정"
                score2 = "미정"

            game_data = {
                "date": current_date,
                "time": game_time,
                "team1": team1,
                "score1": score1,
                "team2": team2,
                "score2": score2
            }
            schedule_data.append(game_data)

    except Exception as e:
        print(f"❌ {month}월 데이터 가져오기 실패:", e)

# ✅ CSV 파일로 저장
df = pd.DataFrame(schedule_data)
df.to_csv("kbo_regular_season_schedule.csv", index=False, encoding="utf-8-sig")

print("✅ 정규시즌 경기 일정 저장 완료: kbo_regular_season_schedule.csv")

# 브라우저 종료
driver.quit()