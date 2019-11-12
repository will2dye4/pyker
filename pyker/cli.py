from pyker.rating import HandType, check_draws, rate_hand


def print_player_info(player, extra_cards=None, check_for_draws=True):
    if extra_cards:
        cards = player.hand + extra_cards
        hand_type = rate_hand(cards)
        rating = hand_type.name
        if check_for_draws:
            draws = check_draws(cards, hand_type)
            if draws:
                rating += f' ({", ".join(draws).capitalize()})'
    else:
        rating = ''
    print(player.name, '\t', player.hand, '\t', player.chips, '\t', rating)


def print_winner_info(top_rating, winners):
    if len(winners) == 1:
        rating = top_rating.name.lower()
        if top_rating == HandType.high_card:
            rating = 'nothing'
        elif top_rating in (HandType.pair, HandType.straight, HandType.flush, HandType.full_house,
                            HandType.straight_flush, HandType.royal_flush):
            rating = f'a {rating}'
        winner = winners[0]
        print(f'{winner.name} wins with {rating}')
    else:
        print('Tie!')  # TODO - check for (a) best hand of that type, (b) kicker or (c) split
