from collections import defaultdict, deque, namedtuple
from enum import Enum
from itertools import cycle
from typing import AnyStr, Callable, Collection, Dict, List, Optional, Sized, Tuple, Union

import random
import re
import weakref


__all__ = ['Suit', 'Rank', 'Card', 'Deck', 'Player', 'Game', 'find_highest_n_of_a_kind', 'has_pair', 'has_two_pair',
           'has_three_of_a_kind', 'has_four_of_a_kind', 'has_full_house', 'find_highest_straight',
           'find_longest_straight', 'has_straight', 'find_biggest_flush', 'has_flush', 'has_straight_flush',
           'rate_hand', 'play_hand']


HAND_SIZE = 5


# https://docs.python.org/3/library/enum.html#orderedenum
class OrderedEnum(Enum):
    def __ge__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering >= other.ordering
        return NotImplemented

    def __gt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering > other.ordering
        return NotImplemented

    def __le__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering <= other.ordering
        return NotImplemented

    def __lt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.ordering < other.ordering
        return NotImplemented

    @property
    def ordering(self) -> int:
        return self.value[0]

    @property
    def symbol(self) -> AnyStr:
        return self.value[1]


class Suit(OrderedEnum):
    spades = (4, '♠︎')
    hearts = (3, '♥︎')
    diamonds = (2, '♦︎')
    clubs = (1, '♣')


class Rank(OrderedEnum):
    two = (2, '2')
    three = (3, '3')
    four = (4, '4')
    five = (5, '5')
    six = (6, '6')
    seven = (7, '7')
    eight = (8, '8')
    nine = (9, '9')
    ten = (10, '10')
    jack = (11, 'J')
    queen = (12, 'Q')
    king = (13, 'K')
    ace = (14, 'A')


Card = namedtuple('Card', ['suit', 'rank'])
Card.__str__ = lambda c: f'{c.rank.symbol}{c.suit.symbol}'
Card.__repr__ = Card.__str__


class Deck(object):
    def __init__(self, shuffle=True):
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank]
        if shuffle:
            self.shuffle()

    def __iter__(self):
        return iter(self.cards)

    def __getitem__(self, item):
        return self.cards[item]

    def __len__(self):
        return len(self.cards)

    def __add__(self, other):
        self.add(cards=other)
        return self

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self) -> Card:
        return self.cards.pop()

    def draw_many(self, count: int) -> List[Card]:
        return [self.draw() for _ in range(count)]

    def add(self, cards: Union[Card, Collection[Card]]) -> None:
        if isinstance(cards, Card):
            cards = [cards]
        self.cards += cards


class Player(object):
    player_id = 1   # don't create players in different threads simultaneously or multiple players may get the same ID

    def __init__(self, name: AnyStr = None, chips: int = 0):
        self.hand = None
        self.hands_played = 0
        self.wins = 0
        self.chips = chips
        self.player_id = Player.player_id
        self.name = name or f'Player {self.player_id}'
        Player.player_id += 1

    def __str__(self):
        return f'Player(name={self.name!r}, chips={self.chips})'


def find_highest_n_of_a_kind(cards: Collection[Card], n: int) -> Optional[Tuple[Card]]:
    if n is None or n < 2 or not has_enough_cards(cards, n):
        return None
    sorted_cards = sorted(cards, key=lambda c: c.rank, reverse=True)
    tuples = [
        tuple(sorted_cards[i:(i + n)])
        for i in range(len(sorted_cards) - n + 1)
        if len(set(map(lambda c: c.rank, sorted_cards[i:(i + n)]))) == 1
    ]
    return tuples[0] if tuples else None


def has_pair(cards: Collection[Card]) -> bool:
    return find_highest_n_of_a_kind(cards, n=2) is not None


def has_two_pair(cards: Collection[Card]) -> bool:
    return has_pair(cards) and has_pair(set(cards) - set(find_highest_n_of_a_kind(cards, n=2)))


def has_three_of_a_kind(cards: Collection[Card]) -> bool:
    return find_highest_n_of_a_kind(cards, n=3) is not None


def has_four_of_a_kind(cards: Collection[Card]) -> bool:
    return find_highest_n_of_a_kind(cards, n=4) is not None


def has_full_house(cards: Collection[Card]) -> bool:
    return has_three_of_a_kind(cards) and has_pair(set(cards) - set(find_highest_n_of_a_kind(cards, n=3)))


def find_best_straight(cards: Collection[Card], rank_fn: Callable[[List[Card], List[Card]], int]) -> List[Card]:
    sorted_cards = sorted(cards, key=lambda c: c.rank)
    cards = [card for i, card in enumerate(sorted_cards) if i == 0 or sorted_cards[i - 1].rank != card.rank]
    aces = [card for card in cards if card.rank == Rank.ace]
    if aces:
        cards.insert(0, aces.pop())    # stash an ace at the beginning to check for a wheel

    best_straight = []
    current_straight = [cards[0]]

    for previous, current in zip(cards[:-1], cards[1:]):
        rank_delta = current.rank.ordering - previous.rank.ordering
        if rank_delta == 1 or (current.rank == Rank.two and previous.rank == Rank.ace):
            current_straight.append(current)
        else:
            if rank_fn(current_straight, best_straight) > 0:
                best_straight = current_straight
            current_straight = [current]

    if rank_fn(current_straight, best_straight) > 0:
        best_straight = current_straight

    return best_straight


def find_highest_straight(cards: Collection[Card]) -> List[Card]:
    def rank_function(current: List[Card], best_so_far: List[Card]) -> int:
        if not best_so_far or (len(best_so_far) == 1 and best_so_far[0].rank == Rank.ace):
            return 1
        return current[0].rank.ordering - best_so_far[0].rank.ordering

    return find_best_straight(cards, rank_function)


def find_longest_straight(cards: Collection[Card]) -> List[Card]:
    return find_best_straight(cards, lambda c, b: len(c) - len(b))


def has_straight(cards: Collection[Card]) -> bool:
    return has_enough_cards(cards, size=HAND_SIZE) and len(find_longest_straight(cards)) >= HAND_SIZE


def find_biggest_flush(cards: Collection[Card]) -> List[Card]:
    suits = defaultdict(list)
    for card in cards:
        suits[card.suit].append(card)
    return max(suits.values(), key=lambda l: len(l))


def has_flush(cards: Collection[Card]) -> bool:
    return has_enough_cards(cards, size=HAND_SIZE) and len(find_biggest_flush(cards)) >= HAND_SIZE


def has_straight_flush(cards: Collection[Card]) -> bool:
    return has_flush(cards) and has_straight(find_biggest_flush(cards))


def has_enough_cards(cards: Sized, size: int = 1) -> bool:
    return cards is not None and len(cards) >= size


def rate_hand(cards: Collection[Card]) -> AnyStr:
    if has_straight_flush(cards):
        return 'Royal flush' if find_highest_straight(cards)[0].rank == Rank.ten else 'Straight flush'
    if has_four_of_a_kind(cards):
        return 'Four of a kind'
    if has_full_house(cards):
        return 'Full house'
    if has_flush(cards):
        return 'Flush'
    if has_straight(cards):
        return 'Straight'
    if has_three_of_a_kind(cards):
        return 'Three of a kind'
    if has_two_pair(cards):
        return 'Two pair'
    if has_pair(cards):
        return 'Pair'
    return 'High card'


class Game(object):

    class Hand(object):
        def __init__(self, game):
            self.game = weakref.ref(game)
            self.pot = 0
            self.flop = None
            self.turn = None
            self.river = None
            self.muck = ()

        @property
        def board(self):
            board = self.flop or ()
            if self.turn:
                board += (self.turn,)
            if self.river:
                board += (self.river,)
            return board

        @staticmethod
        def sorted_cards(cards: Collection[Card]) -> Tuple[Card]:
            return tuple(sorted(cards, key=lambda c: (c.rank, c.suit), reverse=True))

    def __init__(self, ante: int = 0, blinds: Tuple[int] = (100, 200), players: List[Player] = None):
        if not isinstance(ante, int):
            raise Exception('ante must be an integer')
        if not blinds or len(list(blinds)) != 2:
            raise Exception('blinds must be a 2-item tuple')
        if not players:
            players = [Player(chips=10000) for _ in range(4)]
        elif len(players) < 2:
            raise Exception('must have at least two players')
        self.ante = ante
        self.small_blind = blinds[0]
        self.big_blind = blinds[1]
        self.players = players
        self.deck = Deck()
        self.hands = []
        self.current_hand = None

    def play_hand(self):
        self.current_hand = Game.Hand(game=self)

        for player in self.players:
            player.hand = Game.Hand.sorted_cards(self.deck.draw_many(count=2))

        print('======== Ante / Blinds ========')
        for player in list(self.players):
            self.bet_or_fold(player=player, amount=self.ante)
            if player is self.small_blind_player:
                self.bet_or_fold(player=player, amount=self.small_blind)
            elif player is self.big_blind_player:
                self.bet_or_fold(player=player, amount=self.big_blind)

        print('======== Pre-Flop ========')
        self._round_of_betting(pre_flop=True)
        if len([player for player in self.players if player.hand is not None]) > 1:
            print('======== Flop ========')
            self.current_hand.flop = Game.Hand.sorted_cards(self.deck.draw_many(count=3))
            self.print_current_state()
            self._round_of_betting(pre_flop=False)
            if len([player for player in self.players if player.hand is not None]) > 1:
                print('======== Turn ========')
                self.current_hand.turn = self.deck.draw()
                self.print_current_state()
                self._round_of_betting(pre_flop=False)
                if len([player for player in self.players if player.hand is not None]) > 1:
                    print('======== River ========')
                    self.current_hand.river = self.deck.draw()
                    self.print_current_state()
                    self._round_of_betting(pre_flop=False)

        # TODO - determine winner, update stats
        print('======== Hand Finished ========')

        for player in self.players:
            if player.hand is not None:
                self.fold(player=player)

        self.deck += self.current_hand.muck + self.current_hand.board
        self.deck.shuffle()
        self.hands.append(self.current_hand)
        self.current_hand = None

    def bet_or_fold(self, player: Player, amount: int) -> None:
        if amount == 0:
            return
        if Game.check_bet(player=player, amount=amount):
            self.bet(player=player, amount=amount)
        else:
            self.all_in_or_fold(player=player)

    def all_in_or_fold(self, player: Player) -> None:
        if player.chips > 0:    # all in
            self.bet(player=player, amount=player.chips)
        else:
            self.fold(player)
            self.players.remove(player)

    def bet(self, player: Player, amount: int) -> None:
        print(f'--> {player.name} bets {amount}')
        player.chips -= amount
        self.current_hand.pot += amount

    def fold(self, player: Player) -> None:
        print(f'--> {player.name} folds')
        self.current_hand.muck += player.hand
        player.hand = None

    @property
    def dealer(self) -> Player:
        return self._player_at_index_relative_to_dealer(relative_index=0)

    @property
    def small_blind_player(self) -> Player:
        return self._player_at_index_relative_to_dealer(relative_index=1)

    @property
    def big_blind_player(self) -> Player:
        return self._player_at_index_relative_to_dealer(relative_index=2)

    @staticmethod
    def check_bet(player: Player, amount: int) -> bool:
        return player.chips >= amount

    def _player_at_index_relative_to_dealer(self, relative_index: int) -> Player:
        # use len(self.hands) as a counter that increments after each hand
        return self.players[(len(self.hands) + relative_index) % len(self.players)]

    def _index_relative_to_dealer(self, relative_index: int) -> int:
        # use len(self.hands) as a counter that increments after each hand
        return (len(self.hands) + relative_index) % len(self.players)

    def _dealer_index(self):
        return self._index_relative_to_dealer(relative_index=0)

    def _get_available_actions(self, player: Player, current_bet: int, pre_flop: bool = False) -> List[AnyStr]:
        actions = ['fold']
        if not current_bet or (pre_flop and player is self.big_blind_player and current_bet == self.big_blind):
            actions += ['check', 'bet']
        else:
            if player.chips >= current_bet:
                actions.append('call')
            if player.chips > current_bet:
                actions.append('raise')
        return actions

    def _get_action_from_user(self, player: Player, player_bets: Dict[Player, int],
                              current_bet: int, pre_flop: bool = False) -> Tuple[AnyStr, int]:
        actions = self._get_available_actions(player=player, current_bet=current_bet, pre_flop=pre_flop)
        action = None
        bet = None
        while action is None:
            player_annotation = ' (D)' if player is self.dealer else \
                ' (SB)' if player is self.small_blind_player else \
                ' (BB)' if player is self.big_blind_player else ''
            user_action = input(f'[{current_bet}] {player.name}{player_annotation} may {", ".join(actions)}: ')
            args = re.split(r'\s+', user_action)
            if args[0] not in actions:
                print('Invalid action!')
                continue
            elif args[0] == 'bet' or args[0] == 'raise':
                if len(args) < 2:
                    print('You must specify an amount!')
                else:
                    raise_to = args[:2] == ['raise', 'to']
                    try:
                        amount_arg = args[2 if raise_to else 1].replace(',', '')
                        amount = int(amount_arg) + (0 if raise_to or not current_bet else current_bet)
                    except ValueError:
                        print('Invalid amount - must be an integer')
                    else:
                        if amount <= 0:
                            print('Invalid amount - must be positive')
                        elif raise_to and amount <= current_bet:
                            print(f'Invalid amount - must be higher than the current bet ({current_bet})')
                        elif not Game.check_bet(player=player, amount=amount - player_bets[player]):
                            print(f'Invalid amount - {player.name} only has {player.chips} chips')
                        else:
                            action = args[0]
                            bet = amount
            else:
                action = args[0]
        return action, bet

    def _round_of_betting(self, pre_flop: bool = False):
        # put player to act first at the front of the list
        relative_index = 3 if pre_flop else 1
        players = deque(self.players)
        players.rotate(-self._index_relative_to_dealer(relative_index=relative_index))
        player_count = len(players)
        last_caller = next(player for player in players if player.hand is not None)

        if pre_flop:
            initial_bets = {self.small_blind_player: self.small_blind, self.big_blind_player: self.big_blind}
            current_bet, last_raiser = self.big_blind, self.big_blind_player
        else:
            initial_bets = {}
            current_bet = 0
            last_raiser = None
        player_bets = defaultdict(int, initial_bets)

        for i, player in enumerate(cycle(players)):
            if player_count == 1:
                break
            if player.hand is None:
                continue
            if pre_flop and (player is last_raiser and current_bet > self.big_blind):
                #    or (i > 0 and current_bet == self.big_blind and player is last_caller)):
                break
            if not pre_flop and (player is last_raiser or (i > 0 and current_bet == 0 and player is last_caller)):
                break
            print_player_info(player, extra_cards=self.current_hand.board)
            action, bet = self._get_action_from_user(player=player, player_bets=player_bets,
                                                     current_bet=current_bet, pre_flop=pre_flop)
            if action == 'fold':
                self.fold(player)
                player_count -= 1
            elif action in ['bet', 'raise']:
                self.bet(player=player, amount=bet - player_bets[player])
                current_bet = bet
                player_bets[player] = current_bet
                last_raiser = player
            elif action == 'call':
                self.bet(player=player, amount=current_bet - player_bets[player])
                player_bets[player] = current_bet
                last_caller = player
            elif action == 'check' and pre_flop and player is self.big_blind_player:
                break

    def print_current_state(self):
        print(f'{self.current_hand.board}\tPot: {self.current_hand.pot}')


def print_player_info(player, extra_cards=None):
    rating = rate_hand(player.hand + extra_cards) if extra_cards else ''
    print(player.name, '\t', player.hand, '\t', player.chips, '\t', rating)


def play_hand(players=None, deck=None):
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
