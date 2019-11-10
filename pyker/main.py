from typing import Collection, Tuple

from pyker.cards import Card, Deck
from pyker.cli import print_player_info
from pyker.game import Game, Player


__all__ = ['play_game', 'run_hand']


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

    def print_all_player_info(extra_cards=None):
        for player in players:
            print_player_info(player, extra_cards)

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
    print_all_player_info(extra_cards=flop + (turn, river))

    # return cards to deck and reshuffle
    deck.add(flop + (turn, river))
    deck.add([card for hand in map(lambda p: p.hand, players) for card in hand])
    deck.shuffle()
    for player in players:
        player.hand = None
