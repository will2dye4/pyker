from collections import defaultdict
from typing import Collection, Tuple

from pyker.cards import Card, Deck
from pyker.cli import print_player_info, print_winner_info
from pyker.game import Game, Player, get_winners
from pyker.rating import HandType, rate_hand


__all__ = ['play_game', 'run_hand', 'run_hands']


def play_game():
    print('Welcome! A new game is starting.\n')
    game = Game()
    response = ''
    while response not in ('n', 'no'):
        game.play_hand()
        response = input('\nWould you like to play another hand? ').strip().lower()
    print('Goodbye!')


def run_hand(players=None, deck=None):
    def sorted_cards(cards: Collection[Card]) -> Tuple[Card]:
        return tuple(sorted(cards, key=lambda c: (c.rank, c.suit), reverse=True))

    def print_all_player_info(extra_cards=None, check_for_draws=True):
        for player in players:
            print_player_info(player, extra_cards, check_for_draws)

    if players is None:
        players = [Player() for _ in range(4)]
    if deck is None:
        deck = Deck()

    # deal hand to each player, print hands
    for player in players:
        player.hand = sorted_cards(deck.draw_many(count=2))
        print_player_info(player)

    # deal the flop, re-evaluate hands
    flop = sorted_cards(deck.draw_many(count=3))
    print('\nFlop\n', flop, '\n', sep='')
    print_all_player_info(extra_cards=flop)

    # deal the turn, re-evaluate hands
    turn = deck.draw()
    print('\nTurn\n', flop + (turn,), '\n', sep='')
    print_all_player_info(extra_cards=flop + (turn,))

    # deal the river, re-evaluate hands
    river = deck.draw()
    print('\nRiver\n', flop + (turn, river), '\n', sep='')
    print_all_player_info(extra_cards=flop + (turn, river), check_for_draws=False)

    # print results
    print('\nResults')
    winners = get_winners(players, flop + (turn, river))
    print_winner_info(winners)
    print()

    # return cards to deck and reshuffle
    deck.add(flop + (turn, river))
    deck.add([card for hand in map(lambda p: p.hand, players) for card in hand])
    deck.shuffle()
    for player in players:
        player.hand = None


def run_hands(n=1000, num_players=4):
    def show_outcomes(outcomes, all_hands):
        total = n * num_players if all_hands else n
        occurrence_total = 0
        frequency_total = 0
        for hand_type in sorted(HandType):
            occurrences = len(outcomes[hand_type])
            occurrence_total += occurrences
            frequency = (occurrences / total) * 100
            frequency_total += frequency
            print(f'{hand_type.name:16} {occurrences:8,}      ({frequency:0.2f}%)')
        print('-' * 40)
        print(f'Total            {occurrence_total:8,}     ({frequency_total:0.2f}%)')

    players = [Player() for _ in range(num_players)]
    deck = Deck()
    all_outcomes = defaultdict(list)
    winning_outcomes = defaultdict(list)

    for _ in range(n):
        for player in players:
            player.hand = tuple(deck.draw_many(count=2))
        board = tuple(deck.draw_many(count=5))
        for player in players:
            hand_rating = rate_hand(player.hand + board)
            all_outcomes[hand_rating.hand_type].append(hand_rating)
        winners = get_winners(players, board)
        for _, hand_rating in winners:
            winning_outcomes[hand_rating.hand_type].append(hand_rating)

        deck.add(board)
        deck.add([card for hand in map(lambda p: p.hand, players) for card in hand])
        deck.shuffle()

    print('============= All Outcomes =============')
    show_outcomes(all_outcomes, all_hands=True)

    print('\n\n=========== Winning Outcomes ===========')
    show_outcomes(winning_outcomes, all_hands=False)

    print('\n\n============== Hand Strength ==============')
    for hand_type in sorted(HandType):
        all_occurrences = len(all_outcomes[hand_type])
        winning_occurrences = len(winning_outcomes[hand_type])
        win_frequency = (winning_occurrences / all_occurrences) * 100 if all_occurrences > 0 else 0
        ratio = f'{winning_occurrences:,} / {all_occurrences:,}'
        print(f'{hand_type.name:16} {ratio:12}      ({win_frequency:0.2f}%)')
