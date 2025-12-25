import os
import time
import logging
from datetime import datetime
import json
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import google.generativeai as genai

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class LinkedInJobAutomation:
    def __init__(self):
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        self.resume_path = os.getenv('RESUME_PATH', './resume.txt')
        self.job_keywords = os.getenv('JOB_KEYWORDS', 'Data Engineer').split(',')
        self.max_applications = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '10'))
        self.driver = None
        self.applied_jobs = self.load_applied_jobs()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome driver initialized")

    def login_to_linkedin(self):
        try:
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)

            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.send_keys(self.linkedin_email)

            password_input = self.driver.find_element(By.ID, "password")
            password_input.send_keys(self.linkedin_password)

            login_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Sign in']")
            login_button.click()

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/feed/')]"))
            )
            logger.info("Successfully logged into LinkedIn")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise

    def tailor_resume_with_ai(self, base_resume, job_description):
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""Tailor this resume for the job. Use keywords from job description. Keep it truthful.
            
RESUME:
{base_resume}

JOB DESCRIPTION:
{job_description}

Return only the tailored resume."""
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"AI tailoring failed: {str(e)}")
            return base_resume

    def read_base_resume(self):
        try:
            with open(self.resume_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading resume: {str(e)}")
            return ""

    def load_applied_jobs(self):
        try:
            with open('applied_jobs.json', 'r') as f:
                return json.load(f)
        except:
            return []

    def save_applied_jobs(self):
        try:
            with open('applied_jobs.json', 'w') as f:
                json.dump(self.applied_jobs, f)
        except Exception as e:
            logger.error(f"Error saving applied jobs: {str(e)}")

    def run_automation(self):
        try:
            self.setup_driver()
            self.login_to_linkedin()
            logger.info("Automation cycle started")
            time.sleep(3)
        except Exception as e:
            logger.error(f"Automation failed: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

    def schedule_daily_run(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            self.run_automation,
            trigger=CronTrigger(hour=9, minute=0),
            id='linkedin_job_automation'
        )
        scheduler.start()
        logger.info("Scheduler started. Runs daily at 9 AM")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.shutdown()


if __name__ == "__main__":
    automation = LinkedInJobAutomation()
    automation.schedule_daily_run()
