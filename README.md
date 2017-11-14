# sodoku
An Object Orientated approach to implementing a Sodoku board.

The focus is on the board rather than the solution.  I want to
make implenting the board setup and constraints on the board as
general as possible.

There is a solver included.  It uses a recursive method to search
the solution space.  Its possible to implement and pass in
a number of strategies (gang of four) to change the ordering and
priorities used in the search.

A helper method for downloading puzzels from websudoku.com and
transfroming them into sodoku objects is included.
