import re
import weakref

from collections import defaultdict, deque
from itertools import cycle
from typing import Collection, Dict, List, Tuple

from pyker.cards import Card, Deck
from pyker.cli import print_player_info


class Player(object):
    player_id = 1   # don't create players in different threads simultaneously or multiple players may get the same ID

    def __init__(self, name: str = None, chips: int = 0):
        self.hand = None
        self.hands_played = 0
        self.wins = 0
        self.chips = chips
        self.player_id = Player.player_id
        self.name = name or f'Player {self.player_id}'
        Player.player_id += 1

    def __str__(self):
        return f'Player(name={self.name!r}, chips={self.chips})'


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

        print('\n======== Pre-Flop ========')
        self._round_of_betting(pre_flop=True)
        if len([player for player in self.players if player.hand is not None]) > 1:
            print('\n======== Flop ========')
            self.current_hand.flop = Game.Hand.sorted_cards(self.deck.draw_many(count=3))
            self.print_current_state()
            self._round_of_betting(pre_flop=False)
            if len([player for player in self.players if player.hand is not None]) > 1:
                print('\n======== Turn ========')
                self.current_hand.turn = self.deck.draw()
                self.print_current_state()
                self._round_of_betting(pre_flop=False)
                if len([player for player in self.players if player.hand is not None]) > 1:
                    print('\n======== River ========')
                    self.current_hand.river = self.deck.draw()
                    self.print_current_state()
                    self._round_of_betting(pre_flop=False)

        # TODO - determine winner, update stats
        print('\n======== Hand Finished ========')

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

    def _get_available_actions(self, player: Player, current_bet: int, pre_flop: bool = False) -> List[str]:
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
                              current_bet: int, pre_flop: bool = False) -> Tuple[str, int]:
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
