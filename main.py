import time
import schedule
from storage.excel_writer import init_excel
from email_service.email_client import check_emails


if __name__ == "__main__":

    init_excel()

    check_emails()

    schedule.every(5).minutes.do(check_emails)

    print("Monitoring inbox every 5 minutes")

    while True:
        schedule.run_pending()
        time.sleep(30)