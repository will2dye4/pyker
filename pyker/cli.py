from pyker.rating import rate_hand


def print_player_info(player, extra_cards=None):
    rating = rate_hand(player.hand + extra_cards) if extra_cards else ''
    print(player.name, '\t', player.hand, '\t', player.chips, '\t', rating)
