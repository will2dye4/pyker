import re

from typing import Collection, List, Optional, Tuple

from pyker.cards import Card
from pyker.player import Action, Player, PlayerAction, Position
from pyker.rating import HandRating, check_draws, rate_hand


__all__ = ['CLIPlayer', 'print_player_info', 'print_winner_info']


WHITESPACE_RE = re.compile(r'\s+')


def print_player_info(player: Player, extra_cards: Optional[Collection[Card]] = None,
                      check_for_draws: bool = True) -> None:
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


def print_winner_info(winners: List[Tuple[Player, HandRating]]) -> None:
    if len(winners) > 1:
        print('Tie!')

    for winner, hand_rating in winners:
        print(f'{winner.name} wins with {hand_rating}')


class CLIPlayer(Player):

    def get_action(self, allowed_actions: Collection[Action], position: Optional[Position],
                   current_bet: int, player_bet: int) -> PlayerAction:
        action_strs = [action.value for action in allowed_actions]
        action = None
        bet = 0

        while action is None:
            player_annotation = '' if position is None else f' ({position})'
            user_action = input(f'[{current_bet}] {self.name}{player_annotation} may {", ".join(action_strs)}: ')
            args = WHITESPACE_RE.split(user_action)
            if args[0] not in action_strs:
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
                        elif not self.check_bet(amount=amount - player_bet):
                            print(f'Invalid amount - {self.name} only has {self.chips} chips')
                        else:
                            action = args[0]
                            bet = amount
            else:
                action = args[0]

        return PlayerAction(action=Action.for_name(action), bet=bet)
