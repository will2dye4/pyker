from pyker.rating import check_draws, rate_hand


def print_player_info(player, extra_cards=None, check_for_draws=True):
    if extra_cards:
        cards = player.hand + extra_cards
        hand_rating = rate_hand(cards)
        rating = hand_rating.hand_type.name
        if check_for_draws:
            draws = check_draws(cards, hand_rating.hand_type)
            if draws:
                rating += f' ({", ".join(draws).capitalize()})'
    else:
        rating = ''
    print(player.name, '\t', player.hand, '\t', player.chips, '\t', rating)


def print_winner_info(winners):
    if len(winners) > 1:
        print('Tie!')

    for winner, hand_rating in winners:
        print(f'{winner.name} wins with {hand_rating}')
