from pyker.rating import rate_hand


def print_player_info(player, extra_cards=None):
    if extra_cards:
        hand_type = rate_hand(player.hand + extra_cards)
        rating = hand_type.name
    else:
        rating = ''
    print(player.name, '\t', player.hand, '\t', player.chips, '\t', rating)
