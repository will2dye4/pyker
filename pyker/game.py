import weakref

from collections import defaultdict, deque
from itertools import cycle
from typing import Collection, List, Optional, Tuple, Type

from pyker.cards import Card, Deck
from pyker.cli import print_player_info, print_winner_info
from pyker.constants import HAND_SIZE
from pyker.player import Action, Player, Position
from pyker.rating import HandRating, rate_hand


__all__ = ['Game', 'get_winners']


class Game(object):

    class Hand(object):
        def __init__(self, game: Optional['Game']) -> None:
            if game is None:
                self.game = None
            else:
                self.game = weakref.ref(game)
            self.pot = 0
            self.flop = None
            self.turn = None
            self.river = None
            self.muck = ()

        @property
        def board(self) -> Tuple[Card]:
            board = self.flop or ()
            if self.turn:
                board += (self.turn,)
            if self.river:
                board += (self.river,)
            return board

        @staticmethod
        def sorted_cards(cards: Collection[Card]) -> Collection[Card]:
            return tuple(sorted(cards, key=lambda c: (c.rank, c.suit), reverse=True))

    def __init__(self, ante: int = 0, blinds: Tuple[int, int] = (100, 200), players: Optional[List[Player]] = None,
                 player_type: Type[Player] = Player, num_players: int = 4):
        if not isinstance(ante, int):
            raise ValueError('Ante must be an integer')
        if not blinds or len(blinds) != 2:
            raise ValueError('Blinds must be a 2-item tuple')
        if not players:
            if num_players < 2:
                raise ValueError('Must have at least two players')
            players = [player_type(chips=10_000) for _ in range(num_players)]
        elif len(players) < 2:
            raise ValueError('Must have at least two players')
        self.ante = ante
        self.small_blind = blinds[0]
        self.big_blind = blinds[1]
        self.players = players
        self.deck = Deck()
        self.hands = []
        self.current_hand = None

    @property
    def num_players_in_hand(self) -> int:
        return sum(1 for player in self.players if player.hand is not None)

    def play_hand(self) -> None:
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
        if self.num_players_in_hand > 1:
            print('\n======== Flop ========')
            self.current_hand.flop = Game.Hand.sorted_cards(self.deck.draw_many(count=3))
            self._print_current_state()
            self._round_of_betting(pre_flop=False)
            if self.num_players_in_hand > 1:
                print('\n======== Turn ========')
                self.current_hand.turn = self.deck.draw()
                self._print_current_state()
                self._round_of_betting(pre_flop=False)
                if self.num_players_in_hand > 1:
                    print('\n======== River ========')
                    self.current_hand.river = self.deck.draw()
                    self._print_current_state()
                    self._round_of_betting(pre_flop=False)

        if self.num_players_in_hand == 1:
            print('\n======== Hand Finished ========')
            winner = next(player for player in self.players if player.hand is not None)
            print(f'{winner.name} wins')
            self._award_winnings(winner, self.current_hand.pot)
        else:
            print('\n======== Showdown ========')
            winners = get_winners(self.players, self.current_hand.board)
            print_winner_info(winners)
            if len(winners) == 1:
                winner, _ = winners.pop()
                self._award_winnings(winner, self.current_hand.pot)
            else:
                pass  # TODO - split pot

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
        if player.check_bet(amount):
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

    def _player_position(self, player: Player) -> Optional[Position]:
        if player is self.dealer:
            return Position.dealer
        if player is self.small_blind_player:
            return Position.small_blind
        if player is self.big_blind_player:
            return Position.big_blind
        return None

    def _player_at_index_relative_to_dealer(self, relative_index: int) -> Player:
        # use len(self.hands) as a counter that increments after each hand
        return self.players[(len(self.hands) + relative_index) % len(self.players)]

    def _index_relative_to_dealer(self, relative_index: int) -> int:
        # use len(self.hands) as a counter that increments after each hand
        return (len(self.hands) + relative_index) % len(self.players)

    def _dealer_index(self) -> int:
        return self._index_relative_to_dealer(relative_index=0)

    def _get_available_actions(self, player: Player, current_bet: int, pre_flop: bool = False) -> List[Action]:
        actions = [Action.fold]
        if not current_bet or (pre_flop and player is self.big_blind_player and current_bet == self.big_blind):
            actions += [Action.check, Action.bet]
        else:
            if player.chips >= current_bet:
                actions.append(Action.call)
            if player.chips > current_bet:
                actions.append(Action.raise_)
        return actions

    def _round_of_betting(self, pre_flop: bool = False) -> None:
        # put player to act first at the front of the list
        relative_index = 3 if pre_flop else 1
        players = deque(player for player in self.players if player.hand is not None)
        players.rotate(-self._index_relative_to_dealer(relative_index=relative_index))
        last_caller = players[0]

        if pre_flop:
            initial_bets = {self.small_blind_player: self.small_blind, self.big_blind_player: self.big_blind}
            current_bet, last_raiser = self.big_blind, self.big_blind_player
        else:
            initial_bets = {}
            current_bet = 0
            last_raiser = None
        player_bets = defaultdict(int, initial_bets)

        for i, player in enumerate(cycle(players)):
            if self.num_players_in_hand == 1:
                break
            if player.hand is None:
                continue
            if pre_flop and (player is last_raiser and current_bet > self.big_blind):
                break
            if not pre_flop and (player is last_raiser or (i > 0 and current_bet == 0 and player is last_caller)):
                break

            check_for_draw = not pre_flop and len(self.current_hand.board) < HAND_SIZE
            print_player_info(player, extra_cards=self.current_hand.board, check_for_draws=check_for_draw)

            allowed_actions = self._get_available_actions(player=player, current_bet=current_bet, pre_flop=pre_flop)
            position = self._player_position(player)
            player_bet = player_bets[player]
            player_action = player.get_action(allowed_actions=allowed_actions, position=position,
                                              current_bet=current_bet, player_bet=player_bet)

            if player_action.action == Action.fold:
                self.fold(player)
            elif player_action.action in [Action.bet, Action.raise_]:
                bet = player_action.bet
                self.bet(player=player, amount=bet - player_bet)
                current_bet = bet
                player_bets[player] = current_bet
                last_raiser = player
            elif player_action.action == Action.call:
                self.bet(player=player, amount=current_bet - player_bet)
                player_bets[player] = current_bet
                last_caller = player
            elif player_action.action == Action.check and pre_flop and player is self.big_blind_player:
                break

    @staticmethod
    def _award_winnings(player: Player, amount: int) -> None:
        player.chips += amount
        player.wins += 1

    def _print_current_state(self) -> None:
        print(f'{self.current_hand.board}\tPot: {self.current_hand.pot}')


def get_winners(players: Collection[Player], board: Collection[Card]) -> List[Tuple[Player, HandRating]]:
    top_rating = None
    winners = []
    for player in players:
        if player.hand is not None:
            hand_rating = rate_hand(player.hand + board)
            player_and_rating = (player, hand_rating)
            if top_rating is None or hand_rating > top_rating:
                top_rating = hand_rating
                winners = [player_and_rating]
            elif hand_rating == top_rating:
                winners.append(player_and_rating)
    return winners
