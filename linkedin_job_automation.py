import os
import time
import logging
import random
from pathlib import Path
from dotenv import load_dotenv
from google import genai  # Modern 2025 SDK
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 1. Path-Aware Env Loading (Critical for EC2)
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2. Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('job_automation.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class LinkedInJobAutomation:
    def __init__(self):
        # Credentials
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.resume_path = os.path.abspath(os.getenv('RESUME_PATH', './resume.txt'))
        
        # Verify API Key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        self.ai_client = genai.Client(api_key=api_key)
        
        # Config
        raw_keywords = os.getenv('JOB_KEYWORDS', 'Data Engineer')
        self.job_keywords = [k.strip().strip('"') for k in raw_keywords.split(',')]
        self.max_apps = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '20'))
        self.applied_count = 0
        self.driver = None

    def setup_driver(self):
        """Optimized for AWS EC2 and Bot Detection Avoidance"""
        chrome_options = Options()
        
        # Cloud/Headless Arguments
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--no-sandbox")   
        chrome_options.add_argument("--disable-dev-shm-usage") 
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Bypass Detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Headless Browser initialized for Cloud.")

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            WebDriverWait(self.driver, 15).until(EC.url_contains("feed"))
            logger.info("Login successful.")
        except Exception as e:
            logger.error(f"Login failed. Check credentials or CAPTCHA: {e}")
            raise

    def tailor_resume(self, job_desc):
        try:
            with open(self.resume_path, 'r', encoding='utf-8') as f:
                base_resume = f.read()
            
            prompt = f"Tailor this resume for the JD. Use keywords. Max 3000 chars.\nRESUME:\n{base_resume}\n\nJD:\n{job_desc}"
            
            response = self.ai_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            
            tailored_file = os.path.abspath("tailored_resume.txt")
            with open(tailored_file, "w", encoding='utf-8') as f:
                f.write(response.text)
            return tailored_file
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return self.resume_path

    def fill_application_steps(self):
        try:
            for _ in range(6): # Max steps
                time.sleep(2)
                buttons = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue') or contains(@aria-label, 'Next') or contains(@aria-label, 'Review') or contains(@aria-label, 'Submit')]")
                
                if not buttons: break
                
                # Check for Submit
                submit_btn = [b for b in buttons if "Submit" in b.text or "Submit application" in b.get_attribute("aria-label")]
                if submit_btn:
                    submit_btn[0].click()
                    return True
                
                buttons[0].click() 
            return False
        except Exception:
            return False

    def apply_to_jobs(self):
        for keyword in self.job_keywords:
            if self.applied_count >= self.max_apps: break
            
            logger.info(f"Searching: {keyword}")
            search_url = f"https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r86400&keywords={keyword.replace(' ', '%20')}&location=India"
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))

            try:
                job_cards = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container"))
                )
                
                for card in job_cards[:3]:
                    if self.applied_count >= self.max_apps: break
                    try:
                        card.click()
                        time.sleep(3)
                        
                        jd = self.driver.find_element(By.ID, "job-details").text
                        apply_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
                        
                        if "Easy Apply" in apply_btn.text:
                            self.tailor_resume(jd)
                            apply_btn.click()
                            time.sleep(2)
                            
                            if self.fill_application_steps():
                                self.applied_count += 1
                                logger.info(f"Applied! Total: {self.applied_count}")
                            else:
                                # Close the modal if failed
                                self.driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']").click()
                                self.driver.find_element(By.XPATH, "//button[@data-control-name='discard_application_confirm_btn']").click()
                    except Exception: continue
            except Exception: logger.info(f"No results for {keyword}")

    def run_cycle(self):
        try:
            self.setup_driver()
            self.login()
            self.apply_to_jobs()
        finally:
            if self.driver: self.driver.quit()

    def start(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.run_cycle, CronTrigger(hour=9, minute=0))
        scheduler.start()
        logger.info("Bot is active and scheduled for 9 AM. Running a test cycle now...")
        self.run_cycle() # Initial run test
        
        try:
            while True: time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

if __name__ == "__main__":
    bot = LinkedInJobAutomation()
    bot.start()
