import requests
from icalendar import Calendar
from datetime import datetime, date

# Dictionnaire de correspondance (Mapping) simplifié
PLANNING_MAP = {
    "3ETI": "https://planning.cpe.fr/exportics.php?promo=3ETI",
    "4ETI": "https://planning.cpe.fr/exportics.php?promo=4ETI",
    "ETI_ROSE": "https://planning.cpe.fr/exportics.php?major=ETI_ROSE",
    "CGP_ENV": "https://planning.cpe.fr/exportics.php?major=CGP_ENV",
    "IRC_COMSC": "https://planning.cpe.fr/exportics.php?major=IRC_COMSC",
    "3IRC": "https://planning.cpe.fr/exportics.php?promo=3IRC",
    "4IRC": "https://planning.cpe.fr/exportics.php?promo=4IRC",
    "5IRC": "https://planning.cpe.fr/exportics.php?promo=5IRC",
    "3CGP": "https://planning.cpe.fr/exportics.php?promo=3CGP",
    "4CGP": "https://planning.cpe.fr/exportics.php?promo=4CGP",
    "5CGP": "https://planning.cpe.fr/exportics.php?promo=5CGP",
    "3CMH": "https://planning.cpe.fr/exportics.php?promo=3CMH",
    "4CMH": "https://planning.cpe.fr/exportics.php?promo=4CMH",
    "5CMH": "https://planning.cpe.fr/exportics.php?promo=5CMH",
    "3EBS": "https://planning.cpe.fr/exportics.php?promo=3EBS",
    "5ETI": "https://planning.cpe.fr/exportics.php?promo=5ETI",
    "6GPB": "https://planning.cpe.fr/exportics.php?promo=6GPB",
    "3GPI": "https://planning.cpe.fr/exportics.php?promo=3GPI",
    "4GPI": "https://planning.cpe.fr/exportics.php?promo=4GPI",
    "5GPI": "https://planning.cpe.fr/exportics.php?promo=5GPI",
    "3ICS": "https://planning.cpe.fr/exportics.php?promo=3ICS",
    "4ICS": "https://planning.cpe.fr/exportics.php?promo=4ICS",
    "5ICS": "https://planning.cpe.fr/exportics.php?promo=5ICS",
    "3PSM": "https://planning.cpe.fr/exportics.php?promo=3PSM",
    "4PSM": "https://planning.cpe.fr/exportics.php?promo=4PSM",
    "5PSM": "https://planning.cpe.fr/exportics.php?promo=5PSM",
    "CGP_F": "https://planning.cpe.fr/exportics.php?major=CGP_F",
    "CGP_GP": "https://planning.cpe.fr/exportics.php?major=CGP_GP",
    "CGP_SV": "https://planning.cpe.fr/exportics.php?major=CGP_SV",
    "ETI_CLBD": "https://planning.cpe.fr/exportics.php?major=ETI_CLBD",
    "ETI_ESE": "https://planning.cpe.fr/exportics.php?major=ETI_ESE",
    "ETI_IMI": "https://planning.cpe.fr/exportics.php?major=ETI_IMI",
    "ETI_INFRA": "https://planning.cpe.fr/exportics.php?major=ETI_INFRA",
    "IRC_COMSC_N": "https://planning.cpe.fr/exportics.php?major=IRC_COMSC_N",
    "IRC_INFRA": "https://planning.cpe.fr/exportics.php?major=IRC_INFRA",
    "IRC_INFRA_N": "https://planning.cpe.fr/exportics.php?major=IRC_INFRA_N",
    "IRC_ROB": "https://planning.cpe.fr/exportics.php?major=IRC_ROB",
    "IRC_ROB_N": "https://planning.cpe.fr/exportics.php?major=IRC_ROB_N",
    "IRC_SECU_N": "https://planning.cpe.fr/exportics.php?major=IRC_SECU_N",
}

def get_planning(promo_or_major):
    url = PLANNING_MAP.get(promo_or_major)
    if not url:
        return "Erreur : Code de formation inconnu."
    
    try:
        response = requests.get(url, timeout=5)
        gcal = Calendar.from_ical(response.content)
        
        today = date.today()
        courses_today = []

        for component in gcal.walk():
            if component.name == "VEVENT":
                start = component.get('dtstart').dt
                # On ne garde que les cours d'aujourd'hui
                if isinstance(start, datetime):
                    if start.date() == today:
                        summary = component.get('summary')
                        location = component.get('location')
                        time = start.strftime("%H:%M")
                        courses_today.append(f"- {time} : {summary} (Salle : {location})")
        
        if not courses_today:
            return "Aucun cours prévu pour aujourd'hui."
        
        return "\n".join(sorted(courses_today))
    except Exception as e:
        return f"Impossible de joindre le serveur de planning : {e}"