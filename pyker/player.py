from enum import Enum
from typing import Collection, Optional


__all__ = ['Action', 'Player', 'PlayerAction', 'Position']


class Action(Enum):
    bet = 'bet'
    call = 'call'
    check = 'check'
    fold = 'fold'
    raise_ = 'raise'

    def __str__(self) -> str:
        return self.value

    @classmethod
    def for_name(cls, name: str) -> Optional['Action']:
        return next((action for action in cls if action.value == name), None)


class Position(Enum):
    big_blind = 'BB'
    dealer = 'D'
    small_blind = 'SB'

    def __str__(self) -> str:
        return self.value


class PlayerAction(object):

    def __init__(self, action: Action, bet: int = 0):
        if action == Action.fold and bet != 0:
            raise ValueError('May not place a bet when folding')
        if action in (Action.bet, Action.raise_) and bet <= 0:
            raise ValueError(f'Invalid bet (must be > 0): {bet}')
        self.action = action
        self.bet = bet


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
        return f'{self.__class__.__name__}(name={self.name!r}, chips={self.chips})'

    def check_bet(self, amount: int) -> bool:
        return self.chips >= amount

    def get_action(self, allowed_actions: Collection[Action], position: Optional[Position],
                   current_bet: int, player_bet: int) -> PlayerAction:
        raise NotImplemented
