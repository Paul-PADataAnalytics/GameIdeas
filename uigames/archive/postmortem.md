# Postmortem

## Hero Adventure

Hero Adventure started out with the simple idea to make a game without animation that focussed on text for a small ereader I had built. The vision was something could be started up and played for a few turns, or in between books, or when tired, and that produced a feeling of a journey taken, step by step.

Hero Adventure is fully playable but I don't find it fun. I beleive there is vey little that seperates playing a game from busy work and, eventually, all games become busywork.

The AI agents did a fantastic job of realising my instruction, but not the vision. I was the weak link in this attempt. I pivotted to a story teller late on and all it did was make the game worse.

Balance was hard and I don't feel it ever reached a kind of reasonable balance. Fights were mostly binary affairs and cash amount scaled horribly. Some of my instructions were never realised into UI that the player could use, maybe this would have improved the game, but I think the rot had set in some time ago.

The idea still has value, but exploration and control need to be greatly increased along with adding a purpose for the exploration.

### Lessons

The lesson I've learnt from this was "big ideas need to be there from the begining, not added to the project later", and "balance is a measure of the soul of the game, if the balance is bad, and it's hard to calculate or control, the mechanisms are bad".

Simulation was a good advancement, it really helped to have a way to run a 1000 playthorughs and see the effect, at least for the bulk changes that gave the shape a form. It was less useful in tuning the game and hid that the game was bad to tune as it wasn't designed right.

The use of an abstracted UI layer and a bundle of values to populate the UI was, in my opinion, an advancement in my understanding of game UI and technique I'll use again.

AI can do a lot, but I can not, so in future, the structure of the program needs to come from me and I need to treat the AI as an report. I need to build the structure and have the AI build the implementation that fits within the struture.

The whole experience was worth the effort and it was less of a failure than a practice grounds. The only reason to stop was how large the code base became.
