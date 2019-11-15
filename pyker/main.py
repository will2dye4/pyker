from collections import defaultdict
from typing import Collection, Tuple

from pyker.cards import Card, Deck
from pyker.cli import print_player_info, print_winner_info
from pyker.game import Game, Player, get_winners


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
    players = [Player() for _ in range(num_players)]
    deck = Deck()
    outcomes = defaultdict(list)

    for _ in range(n):
        for player in players:
            player.hand = tuple(deck.draw_many(count=2))
        board = tuple(deck.draw_many(count=5))
        winners = get_winners(players, board)
        for _, hand_rating in winners:
            outcomes[hand_rating.hand_type].append(hand_rating)

        deck.add(board)
        deck.add([card for hand in map(lambda p: p.hand, players) for card in hand])
        deck.shuffle()

    for hand_type in sorted(outcomes.keys()):
        occurrences = len(outcomes[hand_type])
        frequency = (occurrences / n) * 100
        print(f'{hand_type.name:16} {len(outcomes[hand_type]):8,}     ({frequency:0.2f}%)')
