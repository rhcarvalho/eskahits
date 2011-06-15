from smtplib import SMTP
from email.mime.text import MIMEText


def sendmail(from_addr, to_addrs, subject, text):
    msg = MIMEText(text)
    msg['From'] = from_addr
    msg['To'] = ", ".join(to_addrs)
    msg['Subject'] = subject

    s = SMTP()
    s.connect('smtp.webfaction.com')
    s.login('quoter', open('/home/rodolfo/quoter').read().strip())
    s.sendmail(from_addr, to_addrs, msg.as_string())
    s.quit()

