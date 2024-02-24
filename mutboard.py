import gspread as gs
import setup
import time

gc = gs.service_account_from_dict(setup.credentials)
sh = gc.open("Mutboard")

creature_num = len(sh.sheet1.col_values(1))

cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'AA', 'AB', 'AC', 'AD']

version = '0.0.0'

def create_creature_dict():
    """
    Returns a dictionary with the keys as the names of each creature in the game
    and the values as the current number of open bounties on the respective
    creature.

    Args:
        None

    Returns:
        dict (string : int)
    """
    keys = sh.sheet1.get_all_values(f"A1:A{creature_num}")
    values = sh.sheet1.get_all_values(f"B1:B{creature_num}")
    creature_dict = {}
    iteration = 0

    for i in keys:
        creature_dict[i[0]] = int(values[iteration][0])
        iteration +=1
    return creature_dict

def get_lowest_open_index(creature_dict):
    """
    Finds the lowest available worksheet index for a bounty page.

    Args:
        creature_dict (dict - (string : int))

    Returns:
        int
    """
    lowest_num = 0

    for i in creature_dict:
        if creature_dict[i] > lowest_num: lowest_num = creature_dict[i]

    return lowest_num + 1

def get_column_num_from_letter(column):
    """
    Returns the column id from its respective letter.

    Args:
        column (str) - A column header letter, from A to AD.

    Returns:
        int
    """
    return cols.index(column) + 1


def get_first_open_column(bounty_page):
    """
    Returns the first empty column in the given worksheet based on the top cell.

    Args:
        bounty_page (worksheet)

    Returns:
        str
        None (if worksheet is full)
    """
    first_empty_column = 0
    top_row = bounty_page.row_values(1)

    for i in top_row:
        if i == '': break
        elif i == 'END': return None
        first_empty_column += 1

    return cols[first_empty_column]

def create_new_bounty_page(lister, display, creature, payment, mutations, index):
    """
    Creates a bounty worksheet for a creature that does not already have a
    bounty page. Places listing information in the first three rows of column A.

    Args:
        lister (str) - Username of lister
        display (str) - Display name of lister
        creature (str) - Name of creature being listed
        payment (str) - Reward given for completing bounty
        mutations (str) - A series of characters with each individual character
            representing some mutation or trait that is requested by the lister.
        index (int) - The index of the worksheet for the bounty page.

    Returns:
        None
    """
    bounty_page = sh.add_worksheet(title=creature,
                                   rows=80,
                                   cols=31,
                                   index=index)
    bounty_page.update('A1:A5',
                       [[lister],
                        [display],
                        [payment],
                        [mutations],
                        [time.time()]])
    bounty_page.update_acell('AE1', 'END')

def add_bounty_to_page(lister, display, payment, mutations, index):
    """
    Adds a new bounty to a pre-existing bounty page for a creature.

    Args:
        lister (str) - Username of lister
        display (str) - Display name of lister
        payment (str) - Reward given for completing bounty
        mutations (str) - A series of characters with each individual character
            representing some mutation or trait that is requested by the lister.
        index (int) - The index of the worksheet for the bounty page.

    Returns:
        None
    """
    bounty_page = sh.get_worksheet(index)
    column = get_first_open_column(bounty_page)
    bounty_page.update(f'{column}1:{column}5',
                       [[lister],
                        [display],
                        [payment],
                        [mutations],
                        [time.time()]])

def list_bounty(lister, display, creature, payment, mutations):
    """
    Lists a new bounty on the bounty board for the specified creature.

    Args:
        lister (str) - Username of lister
        display (str) - Display name of lister
        creature (str) - Name of creature being listed
        payment (str) - Reward given for completing bounty
        mutations (str) - A series of characters with each individual character
            representing some mutation or trait that is requested by the lister.

    Returns:
        None
    """
    creature_dict = create_creature_dict()

    if creature_dict[creature] == 0:
        create_new_bounty_page(lister=lister,
                               display=display,
                               creature=creature,
                               payment=payment,
                               mutations=mutations,
                               index=get_lowest_open_index(creature_dict))

        sh.sheet1.update_acell(f"B{list(creature_dict.keys()).index(creature)+1}",
                               get_lowest_open_index(creature_dict))

    else:
        add_bounty_to_page(lister=lister,
                           display=display,
                           payment=payment,
                           mutations=mutations,
                           index=creature_dict[creature])

def delist_bounty(creature, column):
    """
    Removes a bounty listed on the bounty board. If it is the only bounty listed
    for that creature, it deletes the bounty page.

    Args:
        creature (str) - Name of creature being delisted
        column (str) - The column (A - AD) of the bounty being delisted.

    Returns:
        None
    """

    creature_dict = create_creature_dict()
    bounty_page = sh.get_worksheet(creature_dict[creature])
    bounty_page.batch_clear([f'{column}:{column}'])

    top_row = bounty_page.row_values(1)
    empty_board = False

    for i in top_row:
        if i == '': continue
        elif i == 'END': empty_board = True
        else: break

    if empty_board:
        sh.del_worksheet(bounty_page)
        sh.sheet1.update_acell(f"B{list(creature_dict.keys()).index(creature)+1}",
                               0)

def add_bounty_hunter(hunter, display, creature, obtained, time, column):
    """
    Assigns a bounty hunter to a listed bounty.

    Args:
        hunter (str) - Name of the person attempting the bounty.
        display (str) - Display name of the person attempting the bounty.
        creature (str) - Name of the creature the bounty is listed for.
        obtained (bool) - Whether or not the bounty has been completed.
        time (int) - The time at which the bounty was accepted.
        column (str) - The column (A - AD) of the bounty.

    Returns:
        None
    """

    creature_dict = create_creature_dict()
    bounty_page = sh.get_worksheet(creature_dict[creature])
    column_entries = bounty_page.col_values(get_column_num_from_letter(column))
    nonlinear_placement = False

    if '' in column_entries:
        nonlinear_placement = True

    if hunter not in column_entries:
        if nonlinear_placement:
            row = column_entries.index('')+1
            bounty_page.update(f'{column}{row}:{column}{row+3}',
                               [[hunter], [display], [obtained], [time]])
        elif len(column_entries) < 75 and len(column_entries) != 0:
            row = len(column_entries)+1
            bounty_page.update(f'{column}{row}:{column}{row+3}',
                               [[hunter], [display], [obtained], [time]])

def cancel_bounty_hunter(hunter, creature, column):
    """
    Removes a bounty hunter from a listed bounty.

    Args:
        hunter (str) - Name of the bounty hunter to be removed.
        creature (str) - Name of the creature.
        column (str) - The column (A - AD) of the bounty.
    """

    bounty_page = sh.get_worksheet(create_creature_dict()[creature])
    column_entries = bounty_page.col_values(get_column_num_from_letter(column))
    row = column_entries.index(hunter) + 1

    bounty_page.batch_clear([f'{column}{row}:{column}{row+3}'])