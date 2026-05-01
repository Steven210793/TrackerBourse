import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.error

# ── CONFIG ──
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
DEST_EMAIL = os.environ.get("DEST_EMAIL")
PORTFOLIO_FILE = "portfolio.json"

def fetch_price(ticker):
    """Récupère le prix actuel via Yahoo Finance."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price)
    except Exception as e:
        print(f"  ⚠️  Erreur prix {ticker}: {e}")
        return None

def send_email(alerts):
    """Envoie un email récapitulatif des alertes x2."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not DEST_EMAIL:
        print("⚠️  Variables email manquantes (GMAIL_USER, GMAIL_APP_PASSWORD, DEST_EMAIL)")
        return

    subject = f"🚀 TRACKER — {len(alerts)} objectif(s) x2 atteint(s) !"

    body_html = """
    <html><body style="font-family:Arial,sans-serif;background:#080c12;color:#e8eaf0;padding:20px;">
    <div style="max-width:500px;margin:auto;">
      <h2 style="color:#f0b429;letter-spacing:2px;">📈 TRACKER BOURSE</h2>
      <p style="color:#9aa5be;">Les positions suivantes ont atteint votre objectif x2 :</p>
    """

    for a in alerts:
        pct = ((a['current'] - a['buyPrice']) / a['buyPrice']) * 100
        body_html += f"""
      <div style="background:#111827;border:1px solid #1e2d42;border-radius:12px;padding:16px;margin:12px 0;border-left:3px solid #f0b429;">
        <div style="font-size:18px;font-weight:bold;">{a['name']}</div>
        <div style="color:#9aa5be;font-size:13px;margin-bottom:10px;">{a['ticker']}</div>
        <div style="display:flex;justify-content:space-between;">
          <div>
            <div style="font-size:11px;color:#6b7a99;">PRIX D'ACHAT</div>
            <div style="font-family:monospace;color:#e8eaf0;">{a['buyPrice']:.2f} €</div>
          </div>
          <div>
            <div style="font-size:11px;color:#6b7a99;">PRIX ACTUEL</div>
            <div style="font-family:monospace;color:#22c55e;font-size:18px;">{a['current']:.2f} €</div>
          </div>
          <div>
            <div style="font-size:11px;color:#6b7a99;">PROGRESSION</div>
            <div style="font-family:monospace;color:#f0b429;font-size:18px;">+{pct:.1f}%</div>
          </div>
        </div>
      </div>
        """

    body_html += """
      <p style="color:#6b7a99;font-size:12px;margin-top:20px;">
        Pensez à marquer ces positions comme "Objectif atteint" dans votre app Tracker.
      </p>
    </div></body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = DEST_EMAIL
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, DEST_EMAIL, msg.as_string())
        print(f"✅ Email envoyé à {DEST_EMAIL}")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

def main():
    print("🔍 Vérification des prix en cours...\n")

    # Charger le portefeuille
    if not os.path.exists(PORTFOLIO_FILE):
        print(f"❌ Fichier {PORTFOLIO_FILE} introuvable.")
        return

    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)

    if not portfolio:
        print("ℹ️  Portefeuille vide.")
        return

    alerts = []

    for p in portfolio:
        ticker = p.get("ticker")
        name = p.get("name", ticker)
        buy_price = float(p.get("buyPrice", 0))
        objectif = buy_price * 2

        if not ticker or buy_price <= 0:
            continue

        print(f"📊 {name} ({ticker})")
        current = fetch_price(ticker)

        if current is None:
            print(f"  → Prix non disponible\n")
            continue

        pct = ((current - buy_price) / buy_price) * 100
        print(f"  Achat: {buy_price:.2f} € | Actuel: {current:.2f} € | Progression: {pct:+.1f}%")
        print(f"  Objectif x2: {objectif:.2f} €")

        if current >= objectif:
            print(f"  🚀 OBJECTIF x2 ATTEINT !")
            alerts.append({
                "name": name,
                "ticker": ticker,
                "buyPrice": buy_price,
                "current": current,
                "objectif": objectif
            })
        else:
            remaining = ((objectif - current) / objectif) * 100
            print(f"  ⏳ Il manque {remaining:.1f}% pour atteindre x2")

        print()

    print(f"─────────────────────────────")
    print(f"✅ Vérification terminée : {len(alerts)} alerte(s) sur {len(portfolio)} position(s)")

    if alerts:
        print(f"\n📧 Envoi de l'email d'alerte...")
        send_email(alerts)
    else:
        print("📭 Aucune alerte à envoyer.")

if __name__ == "__main__":
    main()
