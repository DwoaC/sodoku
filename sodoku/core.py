import urllib
from datetime import datetime
from urllib import request

import random
from bs4 import BeautifulSoup

from collections import namedtuple

import numpy as np
import logging
import math
import copy

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

ALL_VALUES = {1, 2, 3, 4, 5, 6, 7, 8, 9}


class SodokuException(Exception):
    pass


class ConstraintException(SodokuException):
    pass


class ConstraintExceptionRow(ConstraintException):
    pass


class ConstraintExceptionCol(ConstraintException):
    pass


class ConstraintExceptionBox(ConstraintException):
    pass


class CellNotInConstaint(SodokuException):
    pass


class Strategy():
    def __init__(self, board):
        self.board = board
        self.history = []


class StrategyException(SodokuException):
    pass


class NoGuessing(Strategy):
    def solve_one_cell(self):
        if self.board.is_complete:
            return

        for cell in self.board.cells:
            if len(cell.remaining_options) == 1 and cell.value is None:
                cell.value = cell.remaining_options.pop()
                self.history.append(Position(cell.col, cell.row, cell.value))
                return

        raise StrategyException('No cell has just one remaining option.\n%s' % self.board.remaining_string)


class Guessing(Strategy):
    def __init__(self, board):
        super().__init__(board)
        self.no_guessing = NoGuessing

    def solve(self, board=None, history=None):
        logger.debug('Starting to solve: {}\n{}'.format(repr(board)), history)
        if history is None:
            history = []
        while not board.is_complete:
            try:
                no_guessing = self.no_guessing(board)
                logger.debug('Solving obvious cases')
                no_guessing.solve_one_cell()
                history += self.no_guessing.history
                logger.debug('\t{}'.format(self.history[-1]))
            except StrategyException:
                logger.debug('Exhausted obvious cases, guessing\n{}'.format(board))
                logger.debug('Options remaining:\n{}'.format(board.remaining_string))
                ranked_options = sorted([c for c in board.cells if c.value is None],
                                        key=lambda c: len(c.remaining_options))

                for option in ranked_options:
                    new_board = copy.deepcopy(board)
                    cell = min(board.cells, key=lambda c: len(c.remaining_options) if c.remaining_options else 10)
                    cell.value = random.choice(list(cell.remaining_options))
                    history.append(Position(cell.col, cell.row, cell.value))
                    logger.debug('Guessing {}'.format(strategy.history[-1]))
                    strategy.solve()


class Constraint:
    def __init__(self, cells):
        self.cells = cells
        for cell in self.cells:
            cell.add_constraint(self)

    @property
    def is_complete(self):
        return ALL_VALUES == set([c.value for c in self.cells])

    def __iter__(self):
        return iter(self.cells)

    def __contains__(self, item):
        return item in self.cells

    def cell_has_changed(self, cell):
        if cell not in self:
            raise CellNotInConstaint()

        if cell.value is None:
            return

        if not self.is_value_unique(cell):
            msg = 'Tried to set a value {} on a constrain that all ready exists: {}'.format(
                cell,
                [other_cell.value for other_cell in self.cells])
            logger.error(msg)
            raise self.constraint_exception(msg)

    def is_value_unique(self, cell):
        return not cell.value in [other_cell.value for other_cell in self.cells
                                  if other_cell is not cell
                                  and other_cell.value is not None]

    @property
    def remaining_options(self):
        return set([1, 2, 3, 4, 5, 6, 7, 8, 9]) - set([c.value for c in self])

    def __str__(self):
        return 'Constraint: remaining options: %s - cells %s' % (
            self.remaining_options,
            [str(c) for c in self.cells])

    @property
    def uncompleted_cells(self):
        return [c for c in self.cells if c.value is None]


class BoxConstraint(Constraint):
    constraint_exception = ConstraintExceptionBox


class RowConstraint(Constraint):
    constraint_exception = ConstraintExceptionRow


class ColConstraint(Constraint):
    constraint_exception = ConstraintExceptionCol


class Board:
    def __init__(self, strategy=NoGuessing):
        self.cells = Cells(9, 9)
        self.rows = []
        self.cols = []
        self.boxes = []
        self.setup_constraints()
        self.strategy = strategy(self)

    @property
    def is_complete(self):
        return all(constraint.is_complete for constraint in self.all_constraints)

    @property
    def all_constraints(self):
        return self.rows + self.cols + self.boxes

    @property
    def remaining_string(self):
        return self.cells_as_str(lambda x: len(x.remaining_options) if x.value is None else ' ')

    @property
    def history(self):
        return self.strategy.history

    def solve_one_cell(self):
        self.strategy.solve_one_cell()

    def setup_constraints(self):
        self.setup_rows()
        self.setup_cols()
        self.setup_boxes()

    def apply_positions(self, positions):
        for position in positions:
            self.cells[position.row][position.col].value = position.value

    def __getitem__(self, col_index):
        return self.cells[col_index]

    @property
    def size_x(self):
        return self.cells.size_x

    @property
    def size_y(self):
        return self.cells.size_y

    def setup_rows(self):
        self.rows = []
        for r in range(self.size_x):
            self.rows.append(RowConstraint(self.cells[r][:]))

    def setup_cols(self):
        self.cols = []
        for r in range(self.size_y):
            self.cols.append(ColConstraint([self.cells[c][r] for c in range(9)]))

    def setup_boxes(self):
        self.boxes = [
            BoxConstraint(
                [
                    self[0][0], self[1][0], self[2][0],
                    self[0][1], self[1][1], self[2][1],
                    self[0][2], self[1][2], self[2][2],
                ]
            ),
            BoxConstraint(
                [
                    self[3][0], self[4][0], self[5][0],
                    self[3][1], self[4][1], self[5][1],
                    self[3][2], self[4][2], self[5][2],
                ]
            ),
            BoxConstraint(
                [
                    self[6][0], self[7][0], self[8][0],
                    self[6][1], self[7][1], self[8][1],
                    self[6][2], self[7][2], self[8][2],
                ]
            ),

            BoxConstraint(
                [
                    self[0][3], self[1][3], self[2][3],
                    self[0][4], self[1][4], self[2][4],
                    self[0][5], self[1][5], self[2][5],
                ]
            ),
            BoxConstraint(
                [
                    self[3][3], self[4][3], self[5][3],
                    self[3][4], self[4][4], self[5][4],
                    self[3][5], self[4][5], self[5][5],
                ]
            ),
            BoxConstraint(
                [
                    self[6][3], self[7][3], self[8][3],
                    self[6][4], self[7][4], self[8][4],
                    self[6][5], self[7][5], self[8][5],
                ]
            ),

            BoxConstraint(
                [
                    self[0][6], self[1][6], self[2][6],
                    self[0][7], self[1][7], self[2][7],
                    self[0][8], self[1][8], self[2][8],
                ]
            ),
            BoxConstraint(
                [
                    self[3][6], self[4][6], self[5][6],
                    self[3][7], self[4][7], self[5][7],
                    self[3][8], self[4][8], self[5][8],
                ]
            ),
            BoxConstraint(
                [
                    self[6][6], self[7][6], self[8][6],
                    self[6][7], self[7][7], self[8][7],
                    self[6][8], self[7][8], self[8][8],
                ]
            )
        ]

    def __str__(self):
        return self.cells_as_str(str)

    def cells_as_str(self, func):
        output = []
        template = '{} {} {} | {} {} {} | {} {} {}'
        for row_index, row in enumerate(self.rows):
            if row_index % 3 == 0 and output != []:
                output.append('-' * 21)
            output.append(template.format(*[func(c) for c in row]))
        return '\n'.join(output)


class Cells:
    def __init__(self, size_x, size_y):
        self.size_x = size_x
        self.size_y = size_y
        self._cells = np.array([[Cell(Position(c, r, None)) for c in range(size_y)]
                                for r in range(size_x)])

    def __len__(self):
        return self.size_x * self.size_y

    def __getitem__(self, item):
        return self._cells[item]

    def __iter__(self):
        for row in self._cells:
            for cell in row:
                yield cell


class Cell:
    def __init__(self, position):
        self.listeners = set()
        self.constraints = set()
        self._value = None
        self.value = position.value
        self.col = position.col
        self.row = position.row

    @property
    def is_impossible(self):
        if self.value is None and len(self.remaining_options) == 0:
            logger.debug('Cell {0} is impossible to solve. Remaining: {0.remaining_options}'.format(self))
            return True
        else:
            return False

    def __eq__(self, other):
        return (self.value == other.value and
                self.row == other.row and
                self.col == other.col
                )

    def __hash__(self):
        return hash((self.value, self.col, self.row))

    def add_constraint(self, constraint):
        self.constraints.add(constraint)
        self.add_listener(constraint)

    def add_listener(self, listener):
        self.listeners.add(listener)

    def broadcast_change(self):
        for listener in self.listeners:
            listener.cell_has_changed(self)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value is None or (1 <= value <= 9):
            self._value = value
        else:
            raise Exception('Value is not in range 1-9 or None: %d' % value)

        self.broadcast_change()

    def __repr__(self):
        return 'Cell({0.col}, {0.row}, value={0.value})'.format(self)

    def __str__(self):
        if self.value is None:
            return ' '
        return str(self.value)

    @property
    def remaining_options(self):
        remaining_options = {1, 2, 3, 4, 5, 6, 7, 8, 9}
        for constraint in self.constraints:
            remaining_options -= ALL_VALUES - constraint.remaining_options
        return remaining_options

    @property
    def reasons(self):
        reasons = []
        for constraint in self.constraints:
            for cell in constraint.cells:
                reasons.append('Cell {} constraints: '.format(repr(self)))
                reasons.append('\n\t%s' % '\n\t'.join(str(c) for c in cell.constraints))
        return '\n'.join(reasons)

    @property
    def col_constraint(self):
        return [c for c in self.constraints if isinstance(c, ColConstraint)][0]

    @property
    def row_constraint(self):
        return [c for c in self.constraints if isinstance(c, RowConstraint)][0]

    @property
    def box_constraint(self):
        return [c for c in self.constraints if isinstance(c, BoxConstraint)][0]


def box_generator():
    for r in range(9):
        for y in range(3):
            yb = y + (math.floor(r / 3) % 3) * 3
            for x in range(3):
                xb = x + ((r % 3) * 3)
                yield (xb, yb)


Position = namedtuple('Position', ('col', 'row', 'value'))


def read_board(string):
    board = Board()
    for row, line in enumerate(string.split('\n')):
        for col, value in enumerate(line.split(' ')):
            board[row][col].value = None if value == '#' else int(value)
    return board


def concat_board_str(a, b):
    a_split = a.split('\n')
    b_split = b.split('\n')
    return '\n'.join('{} || {}'.format(a_line, b_line) for a_line, b_line in zip(a_split, b_split))


class Displayer:
    def __init__(self, line_len):
        self.line_len = line_len
        self.total_string = []
        self.no_of_updates = 0

    def __call__(self, string):
        if string == '\b':
            self.total_string = self.total_string[:-1]
        else:
            self.total_string.append(string)
        self.no_of_updates += 1
        if self.no_of_updates % self.line_len == 0:
            print(''.join(self.total_string))


def total_options(cell):
    return len(cell.remaining_options) + len(cell.row_constraint.uncompleted_cells)


def uncompleted(cell):
    return len(cell.row_constraint.uncompleted_cells)


def easy_first(cell):
    return len(cell.remaining_options)


def hard_first(cell):
    return 9 - len(cell.remaining_options)


def solve(board, history=None, max_rank_to_try=9, displayer=None):
    if board.is_complete:
        return board, []

    if displayer is None:
        displayer = Displayer(30)
    displayer('.')
    starting_time = None
    if history is None:
        logger.info('Starting to solve')
        starting_time = datetime.now()
    logger.debug('Starting recursion\n{}\n{}'.format(
        concat_board_str(str(board), board.remaining_string),
        history))
    if history is None:
        history = []
    ranked_cells = sorted([c for c in board.cells if c.value is None],
                          key=easy_first)

    logger.debug('Ranked Cells: {}'.format(ranked_cells))
    for ranked_cell in [c for c in ranked_cells if len(c.remaining_options) <= max_rank_to_try]:
        for option in ranked_cell.remaining_options:
            logger.debug('Trying {} in [{cell.col}][{cell.row}]={cell.value}'.format(option, cell=ranked_cell))
            new_board = copy.deepcopy(board)
            new_move = Position(ranked_cell.col, ranked_cell.row, option)
            new_history = history + [new_move]
            new_board[new_move.row][new_move.col].value = new_move.value
            logger.debug('Move seems reasonable\n{}'.format(
                concat_board_str(str(new_board), new_board.remaining_string)))
            if new_board.is_complete:
                logger.info('Found a solution, returning')
                return (new_board, new_history)
            elif any(c.is_impossible for c in new_board.cells):
                logger.debug('No solution is possible, trying next possibility')
                continue
            else:
                logger.debug('Move looks reasonable, going deeper.')
                try:
                    solved_board, solution = solve(new_board, new_history, displayer=displayer)
                except StrategyException:
                    # displayer('/')
                    continue
                if solved_board.is_complete:
                    logger.debug('Going deeper found a solution, passing it back up.')
                    if starting_time is not None:
                        logger.info('Competled solution in {}'.format(datetime.now() - starting_time))
                    displayer('\b')
                    return solved_board, solution
    displayer('\b')

    raise StrategyException('Ran out of ideas.')


def download_board(address):
    response = request.urlopen(address)
    board = parse_response(response.read())
    return board


def parse_response(response):
    soup = BeautifulSoup(response, 'html.parser')
    board = Board()
    for col in range(9):
        for row in range(9):
            c = soup.find(id='f{}{}'.format(col, row))
            try:
                board[col][row].value = int(c['value'])
            except KeyError:
                pass
    return board


