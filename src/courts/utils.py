from datetime import timedelta
from .models import Reservation

def check_player_reservation_limits(player, date_time):
    """
    Vérifie si un joueur respecte les limites de réservation pour la semaine donnée.
    
    Règles par semaine (du dimanche matin au samedi soir) :
    - Au maximum deux heures de réservation en simple (2 réservations de 1h)
    - Au maximum quatre heures de réservation en double (2 réservations de 2h)
    - Une heure de réservation en simple ET deux heures de réservation en double (1 simple et 1 double max)
    
    Retourne :
        (is_eligible, error_message) : (bool, str ou None)
    """
    # Déterminer la plage de la semaine (du dimanche matin au samedi soir)
    # weekday() : 0 = lundi, 6 = dimanche.
    # On veut que le dimanche soit le début (offset 0), le lundi offset 1, etc.
    offset = (date_time.weekday() + 1) % 7
    start_of_week = date_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=offset)
    end_of_week = start_of_week + timedelta(days=7)

    # Récupérer le nombre de réservations en simple pour ce joueur dans la semaine
    existing_simple_count = Reservation.objects.filter(
        players=player,
        type='simple',
        date_time__gte=start_of_week,
        date_time__lt=end_of_week
    ).count()

    # Récupérer le nombre de réservations en double pour ce joueur dans la semaine
    existing_double_count = Reservation.objects.filter(
        players=player,
        type='double',
        date_time__gte=start_of_week,
        date_time__lt=end_of_week
    ).count()

    # Vérification des limites
    if existing_simple_count >= 2:
        return False, f"Le joueur {player.first_name} {player.last_name} a atteint le nombre maximum de réservations en simple (2h) pour cette semaine."
        
    if existing_double_count >= 2:
        return False, f"Le joueur {player.first_name} {player.last_name} a atteint le nombre maximum de réservations en double (4h) pour cette semaine."
        
    if existing_simple_count >= 1 and existing_double_count >= 1:
        return False, f"Le joueur {player.first_name} {player.last_name} a atteint le nombre maximum de réservations combinées (simple et double) pour cette semaine."

    return True, None
