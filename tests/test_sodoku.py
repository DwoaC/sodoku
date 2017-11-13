from unittest import TestCase, main
from unittest import mock
import logging

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

from sodoku import Board, Cell, box_generator, ConstraintException, Cells, ConstraintExceptionRow
from sodoku import ConstraintExceptionCol, ConstraintExceptionBox, Position, RowConstraint
from sodoku import StrategyException, read_board, solve, download_board, parse_response

logger.setLevel(logging.WARN)

class TestBoard(TestCase):
    def test_complete(self):
        board = Board()
        self.assertFalse(board.is_complete)

    def test_board_cells(self):
        board = Board()
        self.assertEqual(81, len(board.cells))

        board[0][0].value = 1
        self.assertEqual(1, board[0][0].value)
        self.assertIsInstance(board[0][0], Cell)

        board[8][8].value = 2
        self.assertEqual(2, board[8][8].value)

    def test_constraints(self):
        board = Board()

        self.assertFalse(board.rows[0].is_complete)

        for index, cell in enumerate(board.rows[0]):
            cell.value = index + 1

        self.assertEqual(1, board[0][0].value)
        self.assertEqual(2, board[0][1].value)

        self.assertTrue(board.rows[0].is_complete)


        self.assertFalse(board.cols[0].is_complete)

        board = Board()
        for index, cell in enumerate(board.cols[0]):
            cell.value = index + 1

        self.assertEqual(1, board[0][0].value)
        self.assertEqual(2, board[1][0].value)

        self.assertTrue(board.cols[0].is_complete)

        self.assertFalse(board.boxes[0].is_complete)

        board = Board()
        for index, cell in enumerate(board.boxes[0]):
            cell.value = index + 1

        self.assertEqual(1, board[0][0].value)
        self.assertEqual(2, board[1][0].value)

        self.assertTrue(board.boxes[0].is_complete)

    def test_cell(self):
        cell = Cell(Position(0, 0, None))
        self.assertIsNone(cell.value)

        cell.value = 1
        self.assertEqual(1, cell.value)

        cell.value = 9
        self.assertEqual(9, cell.value)

        cell.value = None
        self.assertIsNone(cell.value)

        bad_values = [0, 10, -1, '1', int]
        for bad_value in bad_values:
            with self.assertRaises(Exception):
                cell.value = bad_value

    def test_boxes_generator(self):
        expected_box_indexes = [
                (0, 0), (1, 0), (2, 0),
                (0, 1), (1, 1), (2, 1),
                (0, 2), (1, 2), (2, 2),

                (3, 0), (4, 0), (5, 0),
                (3, 1), (4, 1), (5, 1),
                (3, 2), (4, 2), (5, 2),

                (6, 0), (7, 0), (8, 0),
                (6, 1), (7, 1), (8, 1),
                (6, 2), (7, 2), (8, 2),

                (0, 3), (1, 3), (2, 3),
                (0, 4), (1, 4), (2, 4),
                (0, 5), (1, 5), (2, 5),

                (3, 3), (4, 3), (5, 3),
                (3, 4), (4, 4), (5, 4),
                (3, 5), (4, 5), (5, 5),

                (6, 3), (7, 3), (8, 3),
                (6, 4), (7, 4), (8, 4),
                (6, 5), (7, 5), (8, 5),

                (0, 6), (1, 6), (2, 6),
                (0, 7), (1, 7), (2, 7),
                (0, 8), (1, 8), (2, 8),

                (3, 6), (4, 6), (5, 6),
                (3, 7), (4, 7), (5, 7),
                (3, 8), (4, 8), (5, 8),

                (6, 6), (7, 6), (8, 6),
                (6, 7), (7, 7), (8, 7),
                (6, 8), (7, 8), (8, 8),
            ]
        box_gen = box_generator()

        found_list_indexes  = list(box_gen)
        self.assertListEqual(
            expected_box_indexes,
            found_list_indexes,
            '\nExpected: %s\nFound:    %s' % (expected_box_indexes, found_list_indexes)
        )

    def test_board_str(self):
        board = Board()
        expected_str = ('      |       |      \n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '---------------------\n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '---------------------\n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '      |       |      ')
        self.assertEqual(expected_str, str(board),
                         '\nExpected:\n%s\nFound:\n%s' % (expected_str, str(board)))

        board.cells[0][0].value = 1

        expected_str = ('1     |       |      \n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '---------------------\n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '---------------------\n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '      |       |      ')
        self.assertEqual(expected_str, str(board),
                         '\nExpected:\n%s\nFound:\n%s' % (expected_str, str(board)))


        board.cells[-1][-1].value = 2
        expected_str = ('1     |       |      \n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '---------------------\n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '---------------------\n'
                        '      |       |      \n'
                        '      |       |      \n'
                        '      |       |     2')
        self.assertEqual(expected_str, str(board),
                         '\nExpected:\n%s\nFound:\n%s' % (expected_str, str(board)))

    def test_broadcast_change(self):
        cell = Cell(Position(0, 0, value=1))
        mock_listener = mock.Mock()
        cell.add_listener(mock_listener)
        mock_listener.assert_not_called()
        cell.value = 2
        mock_listener.cell_has_changed.assert_called_once()

    def test_cell_has_changed(self):
        cells = Cells(9, 1)
        constraint = RowConstraint(cells)
        other_cells = Cells(9, 1)
        other_cell = other_cells[0][0]
        other_cell.add_listener(constraint)
        other_cell.broadcast_change()

        cells[0][0].value = 1

        with self.assertRaises(ConstraintException):
            cells[1][0].value = 1

    def test_cell_eq(self):
        c = Cell(Position(0, 0, None))
        d = Cell(Position(0, 0, None))

        self.assertTrue(c == d)
        self.assertFalse(c != d)

        e = Cell(Position(0, 0, 1))
        self.assertFalse(c == e)

        f = Cell(Position(1, 0, None))
        self.assertFalse(c == f)


    def test_box_constraints(self):
        board = Board()

        self.assertListEqual(
            board.boxes[0].cells,
            [
                board[0][0], board[1][0], board[2][0],
                board[0][1], board[1][1], board[2][1],
                board[0][2], board[1][2], board[2][2],
            ]
        )

        self.assertListEqual(
            board.boxes[1].cells,
            [
                board[3][0], board[4][0], board[5][0],
                board[3][1], board[4][1], board[5][1],
                board[3][2], board[4][2], board[5][2],
            ]
        )

        logger.debug(board.cells_as_str(repr))

    def test_number_of_constraints(self):
        board = Board()

        for col in board:
            for cell in col:
                self.assertEqual(
                    len(cell.constraints),
                    3,
                    '{cell_repr}: {cell.constraints}'.format(cell=cell, cell_repr=repr(cell)))

    def test_each_constraint_type(self):
        board = Board()

        board.cells[0][0].value = 1
        with self.assertRaises(ConstraintExceptionRow):
            board.cells[0][4].value = 1

        with self.assertRaises(ConstraintExceptionCol):
            board.cells[4][0].value = 1

        with self.assertRaises(ConstraintExceptionBox):
            board.cells[1][1].value = 1

    def test_remaining_options(self):
        board = Board()

        board[0][0].value = 1
        self.assertEqual(len(board[0][1].constraints), 3)
        self.assertEqual(board.rows[0].remaining_options, {2, 3, 4, 5, 6, 7, 8, 9})
        self.assertEqual(board.cols[0].remaining_options, {2, 3, 4, 5, 6, 7, 8, 9})
        self.assertEqual(board.boxes[0].remaining_options, {2, 3, 4, 5, 6, 7, 8, 9})

        for constraint in board[0][0].constraints:
            self.assertEqual(constraint.remaining_options, {2, 3, 4, 5, 6, 7, 8, 9})

            for cell in constraint.cells:
                logger.debug('Cell constraints: \n\t%s' % '\n\t'.join(str(c) for c in cell.constraints))
                self.assertEqual(cell.remaining_options, {2, 3, 4, 5, 6, 7, 8, 9})

    def test_remaining_options_2(self):
        board = Board()
        board[0][0].value = 1
        board[1][1].value = 2

        self.assertEqual(
            board[2][2].remaining_options,
            {3,4,5,6,7,8,9}
        )

    def test_remaining_options_3(self):
        board = Board()
        board[0][0].value = 1
        board[1][1].value = 2

        self.assertEqual(
            board[2][2].remaining_options,
            {3,4,5,6,7,8,9}
        )

        board[3][2].value = 3
        board[2][3].value = 4

        self.assertEqual(
            board[2][2].remaining_options,
            {5,6,7,8,9}
        )

        self.assertEqual(
            board[8][8].remaining_options,
            {1,2,3,4,5,6,7,8,9}
        )

    def test_simple_game(self):
        board = Board()
        simple_game_0 = (
            Position(0, 0, 6),
            Position(2, 0, 4),
            Position(4, 0, 7),
            Position(6, 0, 2),
            Position(8, 0, 8),

            Position(2, 1, 3),
            Position(3, 1, 8),
            Position(7, 1, 7),
            Position(8, 1, 9),

            Position(1, 2, 7),
            Position(8, 2, 6),

            Position(2, 3, 1),
            Position(3, 3, 3),
            Position(4, 3, 9),
            Position(5, 3, 5),

            Position(1, 4, 3),
            Position(2, 4, 2),
            Position(3, 4, 6),
            Position(5, 4, 1),
            Position(6, 4, 9),
            Position(7, 4, 8),

            Position(3, 5, 7),
            Position(4, 5, 2),
            Position(5, 5, 8),
            Position(6, 5, 3),

            Position(0, 6, 9),
            Position(7, 6, 5),

            Position(0, 7, 2),
            Position(1, 7, 6),
            Position(5, 7, 7),
            Position(6, 7, 8),

            Position(0, 8, 3),
            Position(2, 8, 8),
            Position(4, 8, 5),
            Position(6, 8, 4),
            Position(8, 8, 7),
        )

        board.apply_positions(simple_game_0)
        self.assertEqual(board.cells[0][0].value, 6)
        print(board)
        print()
        print(board.cells_as_str(lambda x: len(x.remaining_options) if x.value is not None else '#'))

        not_finished = True
        while(not board.is_complete):
            board.solve_one_cell()
            print()
            print(board)
            print(board.history[-1])

        print('\n'.join(str(h) for h in board.history))


    def test_board_import(self):
        string =   ('# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #')

        board = read_board(string)

        for cell in board.cells:
            self.assertIsNone(cell.value)

    def test_blank_board(self):
        string =   ('# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #\n'
                    '# # # # # # # # #')

        board = read_board(string)

    def test_medium_board(self):
        string =   ('9 8 1 3 # # # # #\n'
                    '# # 5 # # # 8 # #\n'
                    '# # # # 5 # # # 4\n'

                    '5 # 8 # 3 1 # 6 #\n'
                    '# 4 3 # # # 1 9 #\n'
                    '# 6 # 7 4 # 3 # 5\n'

                    '6 # # # 7 # # # #\n'
                    '# # 4 # # # 6 # #\n'
                    '# # # # # 3 5 2 1')

        board = read_board(string)

        with self.assertRaises(StrategyException):
            while not board.is_complete:
                board.solve_one_cell()
                logger.debug('\n{}'.format(board.remaining_string))

    def test_guessing_strategy(self):
        string =   ('6 5 4 1 7 9 2 3 8\n'
                    '1 2 3 8 6 4 5 7 9\n'
                    '8 7 9 5 3 2 1 4 6\n'

                    '4 8 1 3 9 5 7 6 2\n'
                    '7 3 2 6 4 1 9 8 5\n'
                    '5 9 6 7 2 8 3 1 4\n'

                    '9 4 7 2 8 3 6 5 1\n'
                    '2 6 5 4 1 7 8 9 3\n'
                    '3 1 8 9 5 6 4 2 7')

        board = read_board(string)
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))

        self.assertTrue(solved_board.is_complete)

        logger.debug('==================')
        board[0][0].value = None
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)

        logger.debug('==================')
        board[0][1].value = None
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        logger.debug('\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)

        logger.debug('==================')
        board[5][0].value = None
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        logger.debug('\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)

        logger.debug('==================')
        board[7][1].value = None
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        logger.debug('\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)

        logger.debug('==================')
        board[5][2].value = None
        board[7][2].value = None
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        logger.debug('\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)

        logger.debug('==================')
        board[0][8].value = None
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        logger.debug('\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.debug('Solved!\n{}\n{}'.format(solved_board, '\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)

    def test_download_board(self):
        address = 'http://view.websudoku.com/?level=1'
        board = download_board(address)
        # print(board)

        logger.info('==================')
        self.assertFalse(board.is_complete, '\n{}'.format(board))
        logger.info('\n{}'.format(board))
        solved_board, solution = solve(board)
        logger.info('Solved!\n{solution}\n{board}'.format(
            board=solved_board,
            solution='\n'.join(str(s) for s in solution)))
        self.assertTrue(solved_board.is_complete)


    def test_parse_response(self):
        response = '''<html>
         <head>
          <title>
           Web Sudoku - Billions of Free Sudoku Puzzles to Play Online
          </title>
          <meta content="text/html; charset=utf-8" http-equiv="Content-Type"/>
          <meta content="width=device-width, initial-scale=1" id="mobileviewport" name="viewport"/>
          <link href="style24.css" rel="stylesheet" type="text/css"/>
          <script language="JavaScript">
           <!--
                    var w_c=1;
                    var w_s=0;
                    var e_m=0;
                    var m_c='<FONT COLOR=green><B>Back to the start, we go!</B></FONT>';
                    var m_m='<FONT COLOR=red><B>You have made some mistakes, highlighted in red!</B></FONT>';
                    var m_w='<FONT COLOR=purple><B>Something is not quite right in * of the cells!</B></FONT>';
                    var m_i='<FONT COLOR=blue><B>Everything is OK, you still have * to go!</B></FONT>';
                    var m_d='<B>Here is the puzzle. Good luck!</B>';
                    var s_c=false;
                    var cheat='173264895582379461496815372235697148714583926869421753928736514351942687647158239';
                    var prefix='8gvll';
                    var pid='7087200185';
                // -->
          </script>
          <script src="index29.js" type="text/javascript">
          </script>
          <!-- The HTML code and text in this document are copyright. Infringers of copyright will be prosecuted. -->
         </head>
         <body bgcolor="#F9F9FF" onload="j3(-1)">
          <table border="0" cellspacing="16" height="100%" width="100%">
           <tr>
            <td id="left-column" width="248">
             <table border="0" cellspacing="0" height="100%" width="248">
              <tr>
               <td align="center" valign="top">
                <script language="JavaScript">
                 <!--
                                j0();
                            // -->
                </script>
                <p style="font-size:8pt; margin:0;">
                 <b>
                  English
                 </b>
                 <a href="http://fr.websudoku.com/" target="_top" title="Web Sudoku - Des Milliards de Sudokus Gratuits pour Jouer en Ligne">
                  Français
                 </a>
                 <a href="http://de.websudoku.com/" target="_top" title="Web Sudoku - Milliarden Kostenlose Online-Sudokus">
                  Deutsch
                 </a>
                 <a href="http://es.websudoku.com/" target="_top" title="Web Sudoku - Billones de rompecabezas sudoku gratis a los que jugar en Línea">
                  Español
                 </a>
                </p>
                <p class="tm" style="margin:18px 0">
                 <img border="0" height="108" src="logo-108x108.gif" width="108"/>
                </p>
                <p class="tm" style="font-size:12pt">
                 <a href="http://www.websudoku.com/?level=1" target="_top">
                  <b>
                   Easy
                  </b>
                 </a>
                 <a href="http://www.websudoku.com/?level=2" target="_top">
                  <b>
                   Medium
                  </b>
                 </a>
                 <a href="http://www.websudoku.com/?level=3" target="_top">
                  <b>
                   Hard
                  </b>
                 </a>
                 <b>
                  Evil
                 </b>
                </p>
                <p class="tm" style="font-size:10pt">
                 <a href="http://www.jigsawdoku.com/" target="_top" title="Play Sudoku in color, plus 4x4 and 6x6 for beginners!">
                  <b>
                   JigSawDoku
                  </b>
                 </a>
                 <a href="http://www.websudoku.com/variation/" target="_top" title="Print a Sudoku variation! Samurai, Squiggly and more...">
                  <b>
                   Variations
                  </b>
                 </a>
                 <a href="http://www.websudoku.com/deluxe.php?l0" target="_top" title="Download Web Sudoku Deluxe to Play Offline!">
                  <b>
                   Download
                  </b>
                 </a>
                 <p class="tm" style="font-size:9pt;">
                  <a href="http://www.websudoku.com/?pic-a-pix" target="_top">
                   <b>
                    Pic-a-Pix
                   </b>
                  </a>
                  <a href="http://www.websudoku.com/?fill-a-pix" target="_top">
                   <b>
                    Fill-a-Pix
                   </b>
                  </a>
                  <a href="http://www.websudoku.com/?hashi" target="_top">
                   <b>
                    Hashi
                   </b>
                  </a>
                  <a href="http://www.websudoku.com/?calcudoku" target="_top">
                   <b>
                    CalcuDoku
                   </b>
                  </a>
                 </p>
                </p>
                <p class="tm" style="padding-top:6px; padding-bottom:12px; margin:18px 0;">
                 Every
                 <a href="http://en.wikipedia.org/wiki/Sudoku" target="_top">
                  Sudoku
                 </a>
                 has a unique solution that can be reached logically. Enter numbers into the blank spaces so that each row, column and 3x3 box contains the numbers 1 to 9. For more help, try our
                 <a href="http://www.websudoku.com/tutorials/" target="_top">
                  interactive Sudoku tutorials
                 </a>
                 .
                </p>
                <p class="tm" style="font-size:10pt;">
                 <a href="http://www.websudoku.com/deluxe.php?l1" target="_top" title="Play Offline, Full Screen, Extra Features!">
                  <b>
                   <u>
                    Play Offline with Web Sudoku Deluxe
                   </u>
                  </b>
                  <br/>
                  <img align="baseline" border="0" height="11" src="green-arrow.gif" style="position:relative; top:1px; left:-5px;" width="11"/>
                  <font color="#006600">
                   Download for Windows and Mac
                  </font>
                 </a>
                </p>
                <p class="tm" style="font-size:10pt">
                 <a href="http://www.websudoku.com/ebook.php?l1" target="_top" title="Choose your own Puzzles and Levels!">
                  <b>
                   <u>
                    Create your own Sudoku Ebook
                   </u>
                  </b>
                 </a>
                </p>
                <p class="tm" style="font-size:10pt">
                 <a href="https://play.google.com/store/apps/details?id=com.websudoku.app&amp;referrer=utm_source%3Dwebsudoku%26utm_medium%3Dreferral%26utm_campaign%3Dleft_link" target="_top">
                  <b>
                   <u>
                    Web Sudoku for Android
                   </u>
                  </b>
                 </a>
                 and
                 <a href="https://itunes.apple.com/us/app/web-sudoku/id786161944?mt=8&amp;uo=4&amp;at=11l558" target="_top">
                  <b>
                   <u>
                    iPad
                   </u>
                  </b>
                 </a>
                 :
                </p>
                <p style="margin-top:6px;">
                 <a href="https://itunes.apple.com/us/app/web-sudoku/id786161944?mt=8&amp;uo=4&amp;at=11l558" target="_top">
                  <img border="0" height="40" src="download-app-store.png" title="Web Sudoku app for iPad" width="135"/>
                 </a>
                 <a href="https://play.google.com/store/apps/details?id=com.websudoku.app&amp;referrer=utm_source%3Dwebsudoku%26utm_medium%3Dreferral%26utm_campaign%3Dleft_button" target="_top">
                  <img border="0" height="40" src="get-it-google-play.png" title="Web Sudoku app for Android" width="117"/>
                 </a>
                </p>
                <script>
                 (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
          (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
          m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
          })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

          ga('create', 'UA-1165533-17', 'auto');
          ga('send', 'pageview');
                </script>
               </td>
              </tr>
              <tr>
               <td align="center" nowrap="" valign="bottom">
                <p class="tm">
                 <b>
                  <a href="http://www.websudoku.com/syndication.php" target="_top" title="Sudoku puzzle syndication for newspapers, magazines, websites, books and more.">
                   Syndication
                  </a>
                  |
                  <a href="http://www.websudoku.com/books/" target="_top" title="Our unique Sudoku books with online solving guides">
                   Books
                  </a>
                  |
                  <a href="http://www.websudoku.com/widget.php" target="_top" title="Add Sudoku to your website or blog">
                   Widget
                  </a>
                  |
                  <a href="http://www.websudoku.com/ipad-android.php" target="_top" title="Web Sudoku for iPad and Android">
                   iPad / Android
                  </a>
                 </b>
                </p>
                <p class="tm" style="margin-top:4pt;">
                 <b>
                  <a href="http://www.websudoku.com/about.php" target="_top" title="More information about Web Sudoku">
                   About Us
                  </a>
                  |
                  <a href="http://www.websudoku.com/faqs.php" target="_top" title="Frequently Asked Questions">
                   FAQs
                  </a>
                  |
                  <a href="http://www.websudoku.com/feedback.php" target="_top" title="Send feedback to Web Sudoku">
                   Feedback
                  </a>
                  |
                  <a href="http://www.websudoku.com/privacy.php" target="_top" title="Our full privacy statement">
                   Privacy Policy
                  </a>
                 </b>
                </p>
               </td>
              </tr>
             </table>
            </td>
            <td bgcolor="#999999" id="separator" width="1">
             <img src="http://www.websudoku.com/images/transparent.gif" width="1"/>
            </td>
            <td bgcolor="#F9F9FF" width="*">
             <table cellspacing="0" height="100%" width="100%">
              <tr>
               <td align="right" height="24" style="padding-bottom:12px;">
                <b>
                 <a href="http://www.websudoku.com/?register" target="_top">
                  Register Free
                 </a>
                 or
                 <a href="http://www.websudoku.com/?signin" target="_top">
                  Sign In to Web Sudoku
                 </a>
                </b>
               </td>
              </tr>
              <tr valign="middle">
               <td align="center">
                <form action="./" method="POST" name="board" style="margin:0;">
                 <script id="mNCC" language="javascript">
                  medianet_width='468';  medianet_height= '60';  medianet_crid='715873954';
                 </script>
                 <script id="mNSC" language="javascript" src="http://contextual.media.net/nmedianet.js?cid=8CU7UD0LJ">
                 </script>
                 <p style="margin-top:18px; margin-bottom:12px;">
                  <font style="font-size:133%;">
                   <span id="message">
                    <b>
                     Here is the puzzle. Good luck!
                    </b>
                   </span>
                  </font>
                 </p>
                 <p style="margin:0;">
                  <table cellpadding="0" cellspacing="0" class="t" id="puzzle_grid">
                   <tr>
                    <td class="g0" id="c00">
                     <input autocomplete="off" class="s0" id="f00" name="s8gvll11" readonly="" size="2" value="1"/>
                    </td>
                    <td class="f0" id="c10">
                     <input autocomplete="off" class="d0" id="f10" maxlength="1" name="8gvll21" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c20">
                     <input autocomplete="off" class="d0" id="f20" maxlength="1" name="8gvll31" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="g0" id="c30">
                     <input autocomplete="off" class="s0" id="f30" name="s8gvll41" readonly="" size="2" value="2"/>
                    </td>
                    <td class="f0" id="c40">
                     <input autocomplete="off" class="d0" id="f40" maxlength="1" name="8gvll51" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c50">
                     <input autocomplete="off" class="d0" id="f50" maxlength="1" name="8gvll61" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="g0" id="c60">
                     <input autocomplete="off" class="d0" id="f60" maxlength="1" name="8gvll71" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c70">
                     <input autocomplete="off" class="d0" id="f70" maxlength="1" name="8gvll81" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c80">
                     <input autocomplete="off" class="s0" id="f80" name="s8gvll91" readonly="" size="2" value="5"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="e0" id="c01">
                     <input autocomplete="off" class="d0" id="f01" maxlength="1" name="8gvll12" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c11">
                     <input autocomplete="off" class="s0" id="f11" name="s8gvll22" readonly="" size="2" value="8"/>
                    </td>
                    <td class="c0" id="c21">
                     <input autocomplete="off" class="d0" id="f21" maxlength="1" name="8gvll32" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c31">
                     <input autocomplete="off" class="s0" id="f31" name="s8gvll42" readonly="" size="2" value="3"/>
                    </td>
                    <td class="c0" id="c41">
                     <input autocomplete="off" class="d0" id="f41" maxlength="1" name="8gvll52" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c51">
                     <input autocomplete="off" class="s0" id="f51" name="s8gvll62" readonly="" size="2" value="9"/>
                    </td>
                    <td class="e0" id="c61">
                     <input autocomplete="off" class="d0" id="f61" maxlength="1" name="8gvll72" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c71">
                     <input autocomplete="off" class="s0" id="f71" name="s8gvll82" readonly="" size="2" value="6"/>
                    </td>
                    <td class="c0" id="c81">
                     <input autocomplete="off" class="d0" id="f81" maxlength="1" name="8gvll92" onblur="j8(this)" size="2"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="e0" id="c02">
                     <input autocomplete="off" class="d0" id="f02" maxlength="1" name="8gvll13" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c12">
                     <input autocomplete="off" class="s0" id="f12" name="s8gvll23" readonly="" size="2" value="9"/>
                    </td>
                    <td class="c0" id="c22">
                     <input autocomplete="off" class="d0" id="f22" maxlength="1" name="8gvll33" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c32">
                     <input autocomplete="off" class="s0" id="f32" name="s8gvll43" readonly="" size="2" value="8"/>
                    </td>
                    <td class="c0" id="c42">
                     <input autocomplete="off" class="d0" id="f42" maxlength="1" name="8gvll53" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c52">
                     <input autocomplete="off" class="d0" id="f52" maxlength="1" name="8gvll63" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c62">
                     <input autocomplete="off" class="d0" id="f62" maxlength="1" name="8gvll73" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c72">
                     <input autocomplete="off" class="d0" id="f72" maxlength="1" name="8gvll83" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c82">
                     <input autocomplete="off" class="s0" id="f82" name="s8gvll93" readonly="" size="2" value="2"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="g0" id="c03">
                     <input autocomplete="off" class="s0" id="f03" name="s8gvll14" readonly="" size="2" value="2"/>
                    </td>
                    <td class="f0" id="c13">
                     <input autocomplete="off" class="d0" id="f13" maxlength="1" name="8gvll24" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c23">
                     <input autocomplete="off" class="s0" id="f23" name="s8gvll34" readonly="" size="2" value="5"/>
                    </td>
                    <td class="g0" id="c33">
                     <input autocomplete="off" class="d0" id="f33" maxlength="1" name="8gvll44" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c43">
                     <input autocomplete="off" class="d0" id="f43" maxlength="1" name="8gvll54" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c53">
                     <input autocomplete="off" class="d0" id="f53" maxlength="1" name="8gvll64" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="g0" id="c63">
                     <input autocomplete="off" class="d0" id="f63" maxlength="1" name="8gvll74" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c73">
                     <input autocomplete="off" class="d0" id="f73" maxlength="1" name="8gvll84" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c83">
                     <input autocomplete="off" class="d0" id="f83" maxlength="1" name="8gvll94" onblur="j8(this)" size="2"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="e0" id="c04">
                     <input autocomplete="off" class="d0" id="f04" maxlength="1" name="8gvll15" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c14">
                     <input autocomplete="off" class="d0" id="f14" maxlength="1" name="8gvll25" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c24">
                     <input autocomplete="off" class="d0" id="f24" maxlength="1" name="8gvll35" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c34">
                     <input autocomplete="off" class="s0" id="f34" name="s8gvll45" readonly="" size="2" value="5"/>
                    </td>
                    <td class="c0" id="c44">
                     <input autocomplete="off" class="d0" id="f44" maxlength="1" name="8gvll55" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c54">
                     <input autocomplete="off" class="s0" id="f54" name="s8gvll65" readonly="" size="2" value="3"/>
                    </td>
                    <td class="e0" id="c64">
                     <input autocomplete="off" class="d0" id="f64" maxlength="1" name="8gvll75" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c74">
                     <input autocomplete="off" class="d0" id="f74" maxlength="1" name="8gvll85" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c84">
                     <input autocomplete="off" class="d0" id="f84" maxlength="1" name="8gvll95" onblur="j8(this)" size="2"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="e0" id="c05">
                     <input autocomplete="off" class="d0" id="f05" maxlength="1" name="8gvll16" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c15">
                     <input autocomplete="off" class="d0" id="f15" maxlength="1" name="8gvll26" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c25">
                     <input autocomplete="off" class="d0" id="f25" maxlength="1" name="8gvll36" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c35">
                     <input autocomplete="off" class="d0" id="f35" maxlength="1" name="8gvll46" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c45">
                     <input autocomplete="off" class="d0" id="f45" maxlength="1" name="8gvll56" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c55">
                     <input autocomplete="off" class="d0" id="f55" maxlength="1" name="8gvll66" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c65">
                     <input autocomplete="off" class="s0" id="f65" name="s8gvll76" readonly="" size="2" value="7"/>
                    </td>
                    <td class="c0" id="c75">
                     <input autocomplete="off" class="d0" id="f75" maxlength="1" name="8gvll86" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c85">
                     <input autocomplete="off" class="s0" id="f85" name="s8gvll96" readonly="" size="2" value="3"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="g0" id="c06">
                     <input autocomplete="off" class="s0" id="f06" name="s8gvll17" readonly="" size="2" value="9"/>
                    </td>
                    <td class="f0" id="c16">
                     <input autocomplete="off" class="d0" id="f16" maxlength="1" name="8gvll27" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c26">
                     <input autocomplete="off" class="d0" id="f26" maxlength="1" name="8gvll37" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="g0" id="c36">
                     <input autocomplete="off" class="d0" id="f36" maxlength="1" name="8gvll47" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c46">
                     <input autocomplete="off" class="d0" id="f46" maxlength="1" name="8gvll57" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c56">
                     <input autocomplete="off" class="s0" id="f56" name="s8gvll67" readonly="" size="2" value="6"/>
                    </td>
                    <td class="g0" id="c66">
                     <input autocomplete="off" class="d0" id="f66" maxlength="1" name="8gvll77" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="f0" id="c76">
                     <input autocomplete="off" class="s0" id="f76" name="s8gvll87" readonly="" size="2" value="1"/>
                    </td>
                    <td class="f0" id="c86">
                     <input autocomplete="off" class="d0" id="f86" maxlength="1" name="8gvll97" onblur="j8(this)" size="2"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="e0" id="c07">
                     <input autocomplete="off" class="d0" id="f07" maxlength="1" name="8gvll18" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c17">
                     <input autocomplete="off" class="s0" id="f17" name="s8gvll28" readonly="" size="2" value="5"/>
                    </td>
                    <td class="c0" id="c27">
                     <input autocomplete="off" class="d0" id="f27" maxlength="1" name="8gvll38" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="e0" id="c37">
                     <input autocomplete="off" class="s0" id="f37" name="s8gvll48" readonly="" size="2" value="9"/>
                    </td>
                    <td class="c0" id="c47">
                     <input autocomplete="off" class="d0" id="f47" maxlength="1" name="8gvll58" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c57">
                     <input autocomplete="off" class="s0" id="f57" name="s8gvll68" readonly="" size="2" value="2"/>
                    </td>
                    <td class="e0" id="c67">
                     <input autocomplete="off" class="d0" id="f67" maxlength="1" name="8gvll78" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="c0" id="c77">
                     <input autocomplete="off" class="s0" id="f77" name="s8gvll88" readonly="" size="2" value="8"/>
                    </td>
                    <td class="c0" id="c87">
                     <input autocomplete="off" class="d0" id="f87" maxlength="1" name="8gvll98" onblur="j8(this)" size="2"/>
                    </td>
                   </tr>
                   <tr>
                    <td class="i0" id="c08">
                     <input autocomplete="off" class="s0" id="f08" name="s8gvll19" readonly="" size="2" value="6"/>
                    </td>
                    <td class="h0" id="c18">
                     <input autocomplete="off" class="d0" id="f18" maxlength="1" name="8gvll29" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="h0" id="c28">
                     <input autocomplete="off" class="d0" id="f28" maxlength="1" name="8gvll39" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="i0" id="c38">
                     <input autocomplete="off" class="d0" id="f38" maxlength="1" name="8gvll49" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="h0" id="c48">
                     <input autocomplete="off" class="d0" id="f48" maxlength="1" name="8gvll59" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="h0" id="c58">
                     <input autocomplete="off" class="s0" id="f58" name="s8gvll69" readonly="" size="2" value="8"/>
                    </td>
                    <td class="i0" id="c68">
                     <input autocomplete="off" class="d0" id="f68" maxlength="1" name="8gvll79" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="h0" id="c78">
                     <input autocomplete="off" class="d0" id="f78" maxlength="1" name="8gvll89" onblur="j8(this)" size="2"/>
                    </td>
                    <td class="h0" id="c88">
                     <input autocomplete="off" class="s0" id="f88" name="s8gvll99" readonly="" size="2" value="9"/>
                    </td>
                   </tr>
                  </table>
                  <input id="prefix" name="prefix" type="hidden" value="8gvll"/>
                  <input name="start" type="hidden" value="1496416377"/>
                  <input name="inchallenge" type="hidden" value=""/>
                  <input name="level" type="hidden" value="4"/>
                  <input id="pid" name="id" type="hidden" value="7087200185"/>
                  <input id="cheat" name="cheat" type="hidden" value="173264895582379461496815372235697148714583926869421753928736514351942687647158239"/>
                  <input id="editmask" type="hidden" value="011011110101010101101011110010111111111010111111111010011110101101010101011110110"/>
                  <input name="options" type="hidden" value="4"/>
                  <input id="errors" name="errors" type="hidden" value="0"/>
                  <input name="layout" type="hidden" value=""/>
                  <p style="margin-top:12pt; margin-bottom:0pt;">
                   <input id="jstimer" name="jstimer" type="hidden"/>
                   <font style="font-size:111%">
                    <a href="http://www.websudoku.com/?level=4&amp;set_id=7087200185" target="_top" title="Copy link for this puzzle">
                     Evil Puzzle 7,087,200,185
                    </a>
                    -
                    <span id="timer">
                    </span>
                    -
                    <a href="http://www.websudoku.com/?select=1&amp;level=4" target="_top">
                     Select a puzzle...
                    </a>
                   </font>
                  </p>
                  <p style="margin-top: 9pt;">
                   <input name="submit" onclick="j12(); return j1();" type="submit" value=" How am I doing? "/>
                   <input name="pause" onclick="return j12();" type="submit" value=" Pause "/>
                   <input name="printopts" onclick="return j12();" type="submit" value=" Print... "/>
                   <input name="clear" onclick="j12(); return j7(2);" type="submit" value=" Clear "/>
                   <input name="showopts" onclick="return j12();" type="submit" value=" Options... "/>
                  </p>
                  <input id="jscheat" name="jscheat" type="hidden"/>
                 </p>
                </form>
               </td>
              </tr>
             </table>
            </td>
           </tr>
          </table>
         </body>
        </html>

        '''
        parse_response(response)

if __name__ == '__main__':
    main()