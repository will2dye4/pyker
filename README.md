# pyker

Pyker is a rudimentary poker engine written in Python.

**NOTE:** This project is a work in progress. It is currently not very fully featured. Sorry about that.

## Installing

```
$ make install
```

### Requirements

Pyker requires **Python 3.6** or newer.

## Playing a Hand

Create a game by instantiating a `pyker.Game` object. By default, the game will have four players
who all start with 10,000 chips. The `play_hand` method of the `Game` will deal a hand to all players
and prompt for input asking how each player should act at each stage of the game.

The game will tell you what actions are legal for a given player. For example, if the prompt says `Player 4 may fold,
call, raise`, then you may type `fold` to fold Player 4's hand, `call` to call the current bet, or `raise N` to raise
the current bet by `N` chips. (You may also say `raise to N` to raise the current bet to exactly `N` chips.) Betting
works the same: type `bet N` to make an initial bet of `N` chips. The other option that is sometimes available is `check`,
which means to pass the action to the next player without folding or betting (only allowed when there are no previous
bets in the current round of betting).

### Example

```
$ python3.8 -q
>>> import pyker
>>> game = pyker.Game()
>>> game.play_hand()
======== Ante / Blinds ========
--> Player 2 bets 100
--> Player 3 bets 200

======== Pre-Flop ========
Player 4     (10♥︎, 2♠︎)     10000 	 
[200] Player 4 may fold, call, raise: fold
--> Player 4 folds
Player 1     (K♦︎, 9♥︎)      10000 	 
[200] Player 1 (D) may fold, call, raise: call
--> Player 1 bets 200
Player 2     (5♥︎, 3♣)      9900 	 
[200] Player 2 (SB) may fold, call, raise: call
--> Player 2 bets 100
Player 3     (5♣, 2♣)      9800 	 
[200] Player 3 (BB) may fold, check, bet: check

======== Flop ========
(K♥︎, 9♦︎, 9♣)     Pot: 600
Player 2     (5♥︎, 3♣)     9800     Pair
[0] Player 2 (SB) may fold, check, bet: check
Player 3     (5♣, 2♣)     9800     Pair
[0] Player 3 (BB) may fold, check, bet: check
Player 1     (K♦︎, 9♥︎)     9800     Full house
[0] Player 1 (D) may fold, check, bet: bet 600
--> Player 1 bets 600
Player 2     (5♥︎, 3♣)     9800     Pair
[600] Player 2 (SB) may fold, call, raise: call
--> Player 2 bets 600
Player 3     (5♣, 2♣)     9800     Pair
[600] Player 3 (BB) may fold, call, raise: fold
--> Player 3 folds

======== Turn ========
(K♥︎, 9♦︎, 9♣, Q♥︎)     Pot: 1800
Player 2     (5♥︎, 3♣)     9200     Pair
[0] Player 2 (SB) may fold, check, bet: check
Player 1     (K♦︎, 9♥︎)     9200     Full house
[0] Player 1 (D) may fold, check, bet: bet 800 
--> Player 1 bets 800
Player 2     (5♥︎, 3♣)     9200     Pair
[800] Player 2 (SB) may fold, call, raise: raise to 1200 
--> Player 2 bets 1200
Player 1     (K♦︎, 9♥︎)     8400     Full house
[1200] Player 1 (D) may fold, call, raise: call
--> Player 1 bets 400

======== River ========
(K♥︎, 9♦︎, 9♣, Q♥︎, 8♦︎)     Pot: 4200
Player 2     (5♥︎, 3♣)     8000     Pair
[0] Player 2 (SB) may fold, check, bet: check
Player 1     (K♦︎, 9♥︎)     8000     Full house
[0] Player 1 (D) may fold, check, bet: check

======== Showdown ========
Player 1 wins with a full house
--> Player 1 folds
--> Player 2 folds
>>>
```

To play another hand, just type `game.play_hand()` again at the Python interpreter prompt (`>>>`).
