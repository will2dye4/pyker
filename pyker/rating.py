from collections import defaultdict
from functools import total_ordering
from typing import Any, Callable, Collection, List, Optional, Sized, Tuple

from pyker.cards import Card, Rank
from pyker.constants import HAND_SIZE
from pyker.utils import OrderedEnum


__all__ = ['HandRating', 'HandType', 'check_draws', 'rate_hand']


class HandType(OrderedEnum):
    royal_flush = (10, 'Royal flush')  # technically just a nut straight flush, but modeled this way for simplicity
    straight_flush = (9, 'Straight flush')
    four_of_a_kind = (8, 'Four of a kind')
    full_house = (7, 'Full house')
    flush = (6, 'Flush')
    straight = (5, 'Straight')
    three_of_a_kind = (4, 'Three of a kind')
    two_pair = (3, 'Two pair')
    pair = (2, 'Pair')
    high_card = (1, 'High card')

    @property
    def name(self) -> str:
        return self.symbol

    @property
    def indefinite_form(self) -> str:
        term = self.name.lower()
        if self in (self.pair, self.straight, self.flush, self.full_house, self.straight_flush, self.royal_flush):
            term = f'a {term}'
        return term


@total_ordering
class HandRating(object):

    def __init__(self, cards: Collection[Card]) -> None:
        self.cards = cards

        if has_straight_flush(cards):
            flush = find_biggest_flush(cards)
            straight_flush = find_longest_straight(flush)
            self.participating_cards = tuple(straight_flush[-HAND_SIZE:])
            if self.participating_cards[0].rank == Rank.ten:
                self.hand_type = HandType.royal_flush
            else:
                self.hand_type = HandType.straight_flush
        elif has_four_of_a_kind(cards):
            self.hand_type = HandType.four_of_a_kind
            self.participating_cards = find_highest_n_of_a_kind(cards, n=4)
        elif has_full_house(cards):
            self.hand_type = HandType.full_house
            three_of_a_kind = find_highest_n_of_a_kind(cards, n=3)
            pair = find_highest_n_of_a_kind(set(cards) - set(three_of_a_kind), n=2)
            self.participating_cards = three_of_a_kind + pair
        elif has_flush(cards):
            self.hand_type = HandType.flush
            flush = sorted(find_biggest_flush(cards))
            self.participating_cards = tuple(flush[-HAND_SIZE:])
        elif has_straight(cards):
            self.hand_type = HandType.straight
            straight = find_longest_straight(cards)
            self.participating_cards = tuple(straight[-HAND_SIZE:])
        elif has_three_of_a_kind(cards):
            self.hand_type = HandType.three_of_a_kind
            self.participating_cards = find_highest_n_of_a_kind(cards, n=3)
        elif has_two_pair(cards):
            self.hand_type = HandType.two_pair
            first_pair = find_highest_n_of_a_kind(cards, n=2)
            second_pair = find_highest_n_of_a_kind(set(cards) - set(first_pair), n=2)
            self.participating_cards = first_pair + second_pair
        elif has_pair(cards):
            self.hand_type = HandType.pair
            self.participating_cards = find_highest_n_of_a_kind(cards, n=2)
        else:
            self.hand_type = HandType.high_card
            self.participating_cards = ()

        self.kickers = tuple(sorted(set(self.cards) - set(self.participating_cards), reverse=True))

    def __eq__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            raise NotImplemented
        if self.hand_type != other.hand_type:
            return False
        if self.ranks != other.ranks:
            return False
        if self.num_kickers == 0:
            return True
        my_kicker_ranks, their_kicker_ranks = self.get_distinct_kicker_ranks(other)
        return my_kicker_ranks == their_kicker_ranks

    def __gt__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            raise NotImplemented
        if self.hand_type > other.hand_type:
            return True
        if self.hand_type < other.hand_type:
            return False
        if self.ranks > other.ranks:
            return True
        if self.ranks < other.ranks:
            return False
        if self.num_kickers == 0:
            return False
        my_kicker_ranks, their_kicker_ranks = self.get_distinct_kicker_ranks(other)
        return my_kicker_ranks > their_kicker_ranks

    def __str__(self) -> str:
        if self.hand_type == HandType.high_card:
            return 'nothing'

        rating = self.hand_type.indefinite_form
        if self.hand_type == HandType.pair:
            rating += f' of {self.participating_cards[0].rank.plural_name}'
        elif self.hand_type == HandType.three_of_a_kind:
            rating = f'three {self.participating_cards[0].rank.plural_name}'
        elif self.hand_type == HandType.four_of_a_kind:
            rating = f'four {self.participating_cards[0].rank.plural_name}'
        elif self.hand_type == HandType.two_pair:
            first_pair_rank = self.participating_cards[0].rank.plural_name
            second_pair_rank = self.participating_cards[-1].rank.plural_name
            rating += f' ({first_pair_rank} and {second_pair_rank})'
        elif self.hand_type == HandType.full_house:
            three_of_a_kind_rank = self.participating_cards[0].rank.plural_name
            pair_rank = self.participating_cards[-1].rank.plural_name
            rating += f' ({three_of_a_kind_rank} full of {pair_rank})'
        elif self.hand_type in (HandType.straight, HandType.flush, HandType.straight_flush, HandType.royal_flush):
            rating += f' {self.participating_cards}'
        return rating

    @property
    def ranks(self) -> List[Rank]:
        return [card.rank for card in self.participating_cards]

    @property
    def num_kickers(self) -> int:
        return HAND_SIZE - len(self.participating_cards)

    def get_distinct_kicker_ranks(self, other: 'HandRating') -> Tuple[List[Rank], List[Rank]]:
        my_kickers = sorted(set(self.kickers) - set(other.kickers), reverse=True)
        their_kickers = sorted(set(other.kickers) - set(self.kickers), reverse=True)
        my_kicker_ranks = [card.rank for card in my_kickers[:self.num_kickers]]
        their_kicker_ranks = [card.rank for card in their_kickers[:self.num_kickers]]
        return my_kicker_ranks, their_kicker_ranks


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
    cards = _get_sorted_cards_for_straight_check(cards)
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


def has_straight_draw(cards: Collection[Card]) -> bool:
    num_cards_needed = HAND_SIZE - 1
    longest_straight_size = len(find_longest_straight(cards))
    if longest_straight_size == num_cards_needed:
        return True
    if longest_straight_size > num_cards_needed:
        return False  # already has a straight!

    cards = _get_sorted_cards_for_straight_check(cards)
    i = 0
    j = num_cards_needed
    while j <= len(cards):
        current_cards = cards[i:j]
        gaps = []
        for previous, current in zip(current_cards[:-1], current_cards[1:]):
            previous_rank_ordering = 1 if previous.rank == Rank.ace else previous.rank.ordering
            delta = current.rank.ordering - previous_rank_ordering
            if delta > 1:
                gaps.append(delta)
        if len(gaps) == 1 and gaps.pop() == 2:
            return True
        i += 1
        j += 1
    return False


def find_biggest_flush(cards: Collection[Card]) -> List[Card]:
    suits = defaultdict(list)
    for card in cards:
        suits[card.suit].append(card)
    return max(suits.values(), key=lambda l: len(l))


def has_flush(cards: Collection[Card]) -> bool:
    return has_enough_cards(cards, size=HAND_SIZE) and len(find_biggest_flush(cards)) >= HAND_SIZE


def has_straight_flush(cards: Collection[Card]) -> bool:
    return has_flush(cards) and has_straight(find_biggest_flush(cards))


def has_flush_draw(cards: Collection[Card]) -> bool:
    return len(find_biggest_flush(cards)) == HAND_SIZE - 1


def has_enough_cards(cards: Sized, size: int = 1) -> bool:
    return cards is not None and len(cards) >= size


def rate_hand(cards: Collection[Card]) -> HandRating:
    return HandRating(cards)


def check_draws(cards: Collection[Card], hand_type: HandType) -> List[str]:
    draws = []
    if hand_type <= HandType.straight:
        if has_flush_draw(cards):
            draws.append('Flush draw')
        if has_straight_draw(cards):
            draws.append('Straight draw')
    return draws


def _get_sorted_cards_for_straight_check(cards: Collection[Card]) -> List[Card]:
    # sort by rank, deduplicate, and stash an ace at the beginning (if appropriate) to check for a wheel
    sorted_cards = sorted(cards, key=lambda c: c.rank)
    cards = [card for i, card in enumerate(sorted_cards) if i == 0 or sorted_cards[i - 1].rank != card.rank]
    aces = [card for card in cards if card.rank == Rank.ace]
    if aces:
        cards.insert(0, aces.pop())
    return cards
