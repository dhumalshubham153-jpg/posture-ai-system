import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from datetime             import datetime

class EmailSender:

    def __init__(self):
        # Use Gmail SMTP
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    def send_report(self, to_email, sender_email,
                    sender_password, report_path,
                    result=None, risk=None):
        """Send posture report via email"""

        msg              = MIMEMultipart()
        msg['From']      = sender_email
        msg['To']        = to_email
        msg['Subject']   = f"PostureAI Report — {datetime.now().strftime('%B %d, %Y')}"

        score = result.get('score', 0) if result else 0
        sev   = risk.get('severity', 'N/A') if risk else 'N/A'

        body = f"""
Hello,

Your PostureAI analysis report is ready.

SUMMARY:
- Posture Score   : {score}/100
- Classification  : {result.get('classification', 'N/A') if result else 'N/A'}
- Spinal Risk     : {risk.get('risk_score', 0) if risk else 0}/100
- Risk Severity   : {sev}

Please find your detailed PDF report attached.

Stay healthy!
PostureAI System
        """

        msg.attach(MIMEText(body, 'plain'))

        # Attach PDF
        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename=posture_report.pdf'
                )
                msg.attach(part)

        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print(f"Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False