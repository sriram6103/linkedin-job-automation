import os
import time
import logging
import random
from pathlib import Path
from dotenv import load_dotenv

# PDF Generation
from fpdf import FPDF

# AI Clients
from google import genai
from groq import Groq

# Scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Load Environment Variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('job_automation.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class LinkedInJobAutomation:
    def __init__(self):
        # --- Config ---
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.resume_path = os.path.abspath(os.getenv('RESUME_PATH', './resume.txt'))
        
        # --- YOUR PERSONAL KNOWLEDGE BASE (AI Context) ---
        # The AI will use these facts to answer ANY question intelligently
        self.user_profile = """
        - Expected Salary (CTC): 18,00,000 INR (18 LPA)
        - Notice Period: 60 Days (Negotiable)
        - Current Location: Hyderabad, India
        - Relocation: Open to relocate
        - Work Authorization: Authorized to work in India
        - Education: B.Tech in Computer Science
        """
        
        # Output Folder
        self.base_apps_path = Path(r"C:\Users\srira\OneDrive\Desktop\Automation\linkedin-job-automation\Applications")
        self.base_apps_path.mkdir(parents=True, exist_ok=True)

        # --- AI Setup ---
        self.gemini_client = None
        self.groq_client = None

        # Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1'})
                logger.info("Gemini AI Client Loaded")
            except Exception as e:
                logger.warning(f"Gemini Init Failed: {e}")

        # Groq
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
                logger.info("Groq AI Client Loaded")
            except Exception as e:
                logger.warning(f"Groq Init Failed: {e}")

        # Job Settings
        raw_keywords = os.getenv('JOB_KEYWORDS', 'Software Engineer')
        self.job_keywords = [k.strip().strip('"') for k in raw_keywords.split(',')]
        self.max_apps = int(os.getenv('MAX_APPLICATIONS_PER_DAY', '20'))
        self.applied_count = 0
        self.driver = None
        
        # Load Resume Text
        try:
            with open(self.resume_path, 'r', encoding='utf-8') as f:
                self.resume_text = f.read()
        except: self.resume_text = ""

    def setup_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("Browser initialized.")

    def login(self):
        logger.info("Navigating to LinkedIn Login...")
        self.driver.get("https://www.linkedin.com/login")
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            WebDriverWait(self.driver, 20).until(EC.url_contains("feed"))
            logger.info("Login successful.")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def get_ai_answer(self, question):
        """
        Uses AI to read the specific question and answer using your Knowledge Base (18LPA/60Days).
        """
        prompt = (
            f"You are a smart job applicant. Answer this form question based on your profile facts.\n"
            f"Question: {question}\n\n"
            f"YOUR FACTS:\n{self.user_profile}\n\n"
            f"Resume Snippet:\n{self.resume_text[:1500]}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. If asking for Salary/CTC number, output ONLY the number: '1800000'.\n"
            f"2. If asking for Notice Period, output '60 Days'.\n"
            f"3. If asking for Location, output 'Hyderabad'.\n"
            f"4. If asking for Years of Experience, calculate roughly from resume or say '0' if fresher.\n"
            f"5. Keep answer extremely concise (1-5 words).\n"
            f"Answer:"
        )

        try:
            answer = ""
            # Try Gemini (v1/Pro)
            if self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model='gemini-pro', contents=prompt
                )
                answer = response.text.strip().replace('"', '')
            
            # Try Groq (Llama 3.3)
            elif self.groq_client:
                chat = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                answer = chat.choices[0].message.content.strip().replace('"', '')
            
            return answer
        except Exception:
            return ""

    def answer_form_questions(self):
        """Scans page for visible text inputs and fills them using AI"""
        
        try:
            # Find visible text inputs
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], textarea")
            
            for field in inputs:
                if not field.is_displayed(): continue
                # Skip if pre-filled
                if field.get_attribute('value'): continue 
                
                # Identify Question Label
                question = ""
                try:
                    f_id = field.get_attribute("id")
                    if f_id:
                        labels = self.driver.find_elements(By.CSS_SELECTOR, f"label[for='{f_id}']")
                        if labels: question = labels[0].text
                except: pass
                
                if not question:
                    question = field.get_attribute("aria-label")

                # Ask AI and Fill
                if question:
                    answer = self.get_ai_answer(question)
                    if answer:
                        field.send_keys(answer)
                        time.sleep(0.5)
        except Exception: pass

    def create_pdf(self, text, output_path):
        """Converts text to PDF"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=10)
            safe_text = text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, txt=safe_text)
            pdf.output(output_path)
            return True
        except Exception: return False

    def tailor_resume(self, job_desc, company_name):
        """Generates PDF resume via AI"""
        prompt = (
            f"Role: {company_name}\n"
            f"Task: Rewrite resume to match JD. Return ONLY clean text body.\n"
            f"JD: {job_desc}\n"
            f"Resume: {self.resume_text}"
        )
        
        tailored_text = None
        
        # AI Generation Logic (Gemini -> Groq)
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-pro', contents=prompt
                )
                tailored_text = response.text
            except: pass
            
        if not tailored_text and self.groq_client:
            try:
                chat = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                tailored_text = chat.choices[0].message.content
            except: pass

        # Save PDF
        if tailored_text:
            clean_name = "".join([c for c in company_name if c.isalnum() or c in (' ', '_')]).strip() or "Unknown"
            folder = self.base_apps_path / clean_name
            folder.mkdir(parents=True, exist_ok=True)
            pdf_path = folder / f"resume_{clean_name}.pdf"
            
            if self.create_pdf(tailored_text, str(pdf_path)):
                return str(pdf_path.absolute())
        
        return self.resume_path

    def fill_application_steps(self, resume_path):
        """Handles Form: Answer Questions -> Upload -> Submit"""
        try:
            for _ in range(6):
                time.sleep(2)
                
                # 1. Answer Questions (Uses your 18LPA/60Days logic)
                self.answer_form_questions()
                
                # 2. Upload Resume
                try:
                    file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                    if file_inputs: file_inputs[0].send_keys(resume_path)
                except: pass

                # 3. Navigation
                buttons = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Continue') or contains(@aria-label, 'Next') or contains(@aria-label, 'Review') or contains(@aria-label, 'Submit')]")
                if not buttons: break
                
                submit_btn = [b for b in buttons if "Submit" in b.text or "Submit application" in b.get_attribute("aria-label")]
                if submit_btn:
                    submit_btn[0].click()
                    return True
                
                buttons[0].click()
            return False
        except: return False

    def apply_to_jobs(self):
        for keyword in self.job_keywords:
            if self.applied_count >= self.max_apps: break
            logger.info(f"--- Searching: {keyword} ---")
            search_url = f"https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r86400&keywords={keyword.replace(' ', '%20')}&location=India"
            self.driver.get(search_url)
            time.sleep(5)

            try:
                job_cards = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container"))
                )
                
                for card in job_cards[:3]:
                    if self.applied_count >= self.max_apps: break
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView();", card)
                        card.click()
                        time.sleep(2)
                        
                        try: company_name = self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text
                        except: company_name = "Unknown"
                        
                        try: jd_text = self.driver.find_element(By.ID, "job-details").text
                        except: jd_text = ""

                        apply_btns = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button')]")
                        if apply_btns and "Easy Apply" in apply_btns[0].text:
                            logger.info(f"Applying to {company_name}...")
                            apply_btns[0].click()
                            time.sleep(1)
                            
                            resume_to_use = self.tailor_resume(jd_text, company_name)
                            
                            if self.fill_application_steps(resume_to_use):
                                self.applied_count += 1
                                logger.info(f"SUCCESS: Applied to {company_name}!")
                            else:
                                try:
                                    self.driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']").click()
                                    time.sleep(1)
                                    self.driver.find_element(By.XPATH, "//button[@data-control-name='discard_application_confirm_btn']").click()
                                    logger.info(f"Skipped {company_name}")
                                except: pass
                    except: continue
            except: logger.info(f"No jobs found for {keyword}")

    def run_cycle(self):
        try:
            self.setup_driver()
            self.login()
            self.apply_to_jobs()
        except Exception as e:
            logger.error(f"Cycle Error: {e}")
        finally:
            if self.driver: self.driver.quit()

    def start(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.run_cycle, CronTrigger(hour=9, minute=0))
        scheduler.start()
        logger.info("Bot started. Running initial cycle now...")
        self.run_cycle()
        try:
            while True: time.sleep(1)
        except: scheduler.shutdown()

if __name__ == "__main__":
    bot = LinkedInJobAutomation()
    bot.start()
