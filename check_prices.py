import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
DEST_EMAIL = os.environ.get('DEST_EMAIL')
PORTFOLIO_FILE = 'portfolio.json'

def fetch_price(ticker):
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + ticker + '?interval=1d&range=1d'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return float(price)
    except Exception as e:
        print('  Erreur prix ' + ticker + ': ' + str(e))
        return None

def send_email(alerts):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not DEST_EMAIL:
        print('Variables email manquantes')
        return

    subject = 'TRACKER ' + str(len(alerts)) + ' objectif(s) x2 atteint(s) !'
    body = '<html><body style="font-family:Arial,sans-serif;background:#080c12;color:#e8eaf0;padding:20px;">'
    body += '<div style="max-width:500px;margin:auto;">'
    body += '<h2 style="color:#f0b429;">TRACKER BOURSE</h2>'
    body += '<p style="color:#9aa5be;">Les positions suivantes ont atteint votre objectif x2 :</p>'

    for a in alerts:
        pct = ((a['valeurActuelle'] - a['montantInvesti']) / a['montantInvesti']) * 100
        gain = a['valeurActuelle'] - a['montantInvesti']
        body += '<div style="background:#111827;border:1px solid #1e2d42;border-radius:12px;padding:16px;margin:12px 0;border-left:3px solid #f0b429;">'
        body += '<div style="font-size:18px;font-weight:bold;">' + a['name'] + '</div>'
        body += '<div style="color:#9aa5be;">' + a['ticker'] + '</div>'
        body += '<div>Investi: ' + str(round(a['montantInvesti'], 2)) + ' EUR</div>'
        body += '<div style="color:#22c55e;">Valeur: ' + str(round(a['valeurActuelle'], 2)) + ' EUR</div>'
        body += '<div style="color:#f0b429;">Gain: +' + str(round(gain, 2)) + ' EUR (+' + str(round(pct, 1)) + '%)</div>'
        body += '</div>'

    body += '<p style="color:#6b7a99;font-size:12px;">Marquez ces positions comme Objectif atteint dans votre app.</p>'
    body += '</div></body></html>'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = DEST_EMAIL
    msg.attach(MIMEText(body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, DEST_EMAIL, msg.as_string())
        print('Email envoye a ' + DEST_EMAIL)
    except Exception as e:
        print('Erreur email : ' + str(e))

def main():
    print('Verification des prix en cours...')

    if not os.path.exists(PORTFOLIO_FILE):
        print('Fichier portfolio.json introuvable.')
        return

    with open(PORTFOLIO_FILE, 'r') as f:
        portfolio = json.load(f)

    if not portfolio:
        print('Portefeuille vide.')
        return

    alerts = []

    for p in portfolio:
        ticker = p.get('ticker')
        name = p.get('name', ticker)
        montant_investi = float(p.get('montantInvesti', 0))
        qty = float(p.get('qty', 0))
        objectif = montant_investi * 2

        if not ticker or montant_investi <= 0:
            continue

        print(name + ' (' + ticker + ')')
        prix_actuel = fetch_price(ticker)

        if prix_actuel is None:
            print('  Prix non disponible')
            continue

        valeur_actuelle = qty * prix_actuel if qty > 0 else montant_investi
        gain = valeur_actuelle - montant_investi
        pct = (gain / montant_investi) * 100

        print('  Investi: ' + str(round(montant_investi, 2)) + ' | Valeur: ' + str(round(valeur_actuelle, 2)) + ' | Gain: ' + str(round(gain, 2)) + ' (' + str(round(pct, 1)) + '%)')
        print('  Objectif x2: ' + str(round(objectif, 2)))

        if valeur_actuelle >= objectif:
            print('  OBJECTIF x2 ATTEINT !')
            alerts.append({
                'name': name,
                'ticker': ticker,
                'montantInvesti': montant_investi,
                'valeurActuelle': valeur_actuelle,
                'objectif': objectif
            })
        else:
            progress = (valeur_actuelle / objectif) * 100
            print('  Progression : ' + str(round(progress, 1)) + '%')

    print('Verification terminee : ' + str(len(alerts)) + ' alerte(s)')

    if alerts:
        print('Envoi email...')
        send_email(alerts)
    else:
        print('Aucune alerte.')

if __name__ == '__main__':
    main()
