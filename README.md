# LinkedIn Job Automation with AI Resume Tailoring

Automatically apply to LinkedIn jobs daily with AI-tailored resumes using Google Gemini API.

## Features

✅ Searches LinkedIn jobs by keywords  
✅ AI tailors resume to each job description (Google Gemini)  
✅ Automatically applies to matching jobs  
✅ Tracks applied jobs (never applies twice)  
✅ Schedules daily runs automatically  
✅ Comprehensive logging for debugging  
✅ 100% FREE (uses Google Gemini free tier)  
✅ Works on Windows, Mac, and Linux  

## Prerequisites

- Python 3.8+
- Chrome/Chromium browser installed
- Google account (for Gemini API)
- LinkedIn account

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/sriram6103/linkedin-job-automation.git
cd linkedin-job-automation
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Free Gemini API Key

1. Visit https://makersuite.google.com
2. Sign in with your Google account
3. Click "Get API Key"
4. Select "Create API key in new project"
5. Copy your API key

### 5. Setup Configuration

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
# Add your LinkedIn email, password, and Gemini API key
```

### 6. Add Your Resume

Create `resume.txt` with your resume in plain text format.

### 7. Run the Automation

```bash
# Run immediately
python linkedin_job_automation.py

# Run in background (Windows)
start python linkedin_job_automation.py

# Run in background (Mac/Linux)
python linkedin_job_automation.py &
```

## Configuration (.env file)

```env
LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_linkedin_password
GEMINI_API_KEY=your_gemini_api_key_here
RESUME_PATH=./resume.txt
JOB_KEYWORDS=Data Engineer,Backend Engineer,Software Engineer
MAX_APPLICATIONS_PER_DAY=10
```

## Schedule Daily Runs

### Windows Task Scheduler

1. Create batch file `run_automation.bat`:
```batch
@echo off
cd %~dp0
call venv\Scripts\activate.bat
python linkedin_job_automation.py
pause
```

2. Open Task Scheduler:
   - Win + R → taskschd.msc
   - Create Basic Task
   - Name: "LinkedIn Job Automation"
   - Trigger: Daily at 9:00 AM
   - Action: Run `run_automation.bat`

### Mac/Linux Cron Job

```bash
crontab -e

# Add this line (runs at 9 AM daily):
0 9 * * * /usr/bin/python3 /path/to/linkedin_job_automation.py
```

## Monitoring

```bash
# View logs
tail -f job_automation.log

# View applied jobs
cat applied_jobs.json
```

## Security Notes

⚠️ **IMPORTANT:**
- Never commit `.env` file to GitHub
- Add `.env` to `.gitignore`
- Don't share your credentials
- Use strong passwords
- Enable 2FA on LinkedIn
- Keep API keys secret

## Project Structure

```
linkedin-job-automation/
├── linkedin_job_automation.py      # Main automation script
├── requirements.txt                # Python dependencies
├── .env.example                    # Configuration template
├── resume.txt                      # Your resume (plain text)
├── applied_jobs.json              # Auto-created tracking file
├── job_automation.log             # Auto-created log file
├── README.md                      # This file
└── .gitignore                     # Git ignore file
```

## Troubleshooting

### Selenium can't find Chrome
- Download ChromeDriver: https://chromedriver.chromium.org/
- Place in project folder
- Update script: `webdriver.Chrome('./chromedriver')`

### LinkedIn login fails
- Verify email/password in `.env`
- LinkedIn may require 2FA
- Run manually first to handle 2FA
- Check `job_automation.log` for errors

### Gemini API errors
- Verify API key is correct
- Check internet connection
- Ensure API key has no extra spaces
- Check Google Cloud quota

## Cost

**FREE!**
- Selenium: Free
- Python: Free
- Google Gemini: Free (60 requests/min)
- APScheduler: Free

## Disclaimer

This tool automates job applications. Use responsibly:
- Don't spam applications
- Follow LinkedIn's terms of service
- Use realistic job keywords
- Keep resume truthful
- LinkedIn may flag unusual activity

## Contributing

Feel free to fork and improve this project!

## License

MIT License - Use freely for personal and commercial use.

---

**Ready to automate your job search?** Clone this repo and get started! 🚀
