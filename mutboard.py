import gspread as gs
import setup
import time

creature_num = 0
gc = 0
sh = 0

cols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'AA', 'AB', 'AC', 'AD']

version = '0.0.0'

def startup():
    """
    Initializes necessary parts of the code. Called on start up.

    Args:
        None

    Returns:
        None
    """
    global creature_num, gc, sh
    gc = gs.service_account_from_dict(setup.credentials)
    sh = gc.open("Mutboard")
    creature_num = len(sh.sheet1.col_values(1))

def create_creature_dict():
    """
    Returns a dictionary with the keys as the names of each creature in the game
    and the values as a list containing the worksheet ID for and the current
    number of open bounties on the respective creature.

    Args:
        None

    Returns:
        dict (string : [int, int])
    """
    keys = sh.sheet1.get_all_values(f"A1:A{creature_num}")
    values = sh.sheet1.get_all_values(f"B1:B{creature_num}")
    bounties = sh.sheet1.get_all_values(f"C1:C{creature_num}")
    creature_dict = {}
    iteration = 0

    for i in keys:
        creature_dict[i[0]] = [int(values[iteration][0]), int(bounties[iteration][0])]
        iteration +=1
    return creature_dict

def get_lowest_open_index(creature_dict):
    """
    Finds the lowest available worksheet index for a bounty page.

    Args:
        creature_dict (dict - (string : [int, int])) - All bounty information
        for all creatures.

    Returns:
        int
    """
    lowest_num = 0

    for i in creature_dict:
        if creature_dict[i][0] > lowest_num: lowest_num = creature_dict[i][0]

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
    time.sleep(1)

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
    time.sleep(1)

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

    if creature_dict[creature][0] == 0:
        create_new_bounty_page(lister=lister,
                               display=display,
                               creature=creature,
                               payment=payment,
                               mutations=mutations,
                               index=get_lowest_open_index(creature_dict))

        sh.sheet1.update(f"B{list(creature_dict.keys()).index(creature)+1}:C{list(creature_dict.keys()).index(creature)+1}",
                         [[get_lowest_open_index(creature_dict), creature_dict[creature][1] + 1]])

    else:
        add_bounty_to_page(lister=lister,
                           display=display,
                           payment=payment,
                           mutations=mutations,
                           index=creature_dict[creature][0])
        sh.sheet1.update_acell(f"C{list(creature_dict.keys()).index(creature)+1}",
                         creature_dict[creature][1] + 1)
    time.sleep(2.5)

def delist_bounty(creature, column, creature_dict):
    """
    Removes a bounty listed on the bounty board. If it is the only bounty listed
    for that creature, it deletes the bounty page.

    Args:
        creature (str) - Name of creature being delisted
        column (str) - The column (A - AD) of the bounty being delisted.
        creature_dict (dict - (string : [int, int])) - All bounty information
        for all creatures.

    Returns:
        None
    """

    bounty_page = sh.get_worksheet(creature_dict[creature][0])
    bounty_page.batch_clear([f'{column}:{column}'])

    top_row = bounty_page.row_values(1)
    empty_board = False

    for i in top_row:
        if i == '': continue
        elif i == 'END': empty_board = True
        else: break

    if empty_board:
        sh.del_worksheet(bounty_page)
        sh.sheet1.update(f"B{list(creature_dict.keys()).index(creature)+1}:C{list(creature_dict.keys()).index(creature)+1}",
                               [[0, creature_dict[creature][1] - 1]])
    else:
        sh.sheet1.update_acell(f'C{list(creature_dict.keys()).index(creature)+1}',
                               creature_dict[creature][1] - 1)
    time.sleep(2)


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
    time.sleep(2)

def cancel_bounty_hunter(hunter, creature, column):
    """
    Removes a bounty hunter from a listed bounty.

    Args:
        hunter (str) - Name of the bounty hunter to be removed.
        creature (str) - Name of the creature.
        column (str) - The column (A - AD) of the bounty.

    Returns:
        None
    """

    bounty_page = sh.get_worksheet(create_creature_dict()[creature][0])
    column_entries = bounty_page.col_values(get_column_num_from_letter(column))
    row = column_entries.index(hunter) + 1

    bounty_page.batch_clear([f'{column}{row}:{column}{row+3}'])
    time.sleep(1)

def get_bounties(creature_dict):
    """
    Retrieves a dictionary of all currently posted bounties, with the keys as
    the creature names and the values as a nested list of bounty information.

    Args:
        creature_dict (dict - (string : [int, int])) - All bounty information
        for all creatures.

    Returns:
        dict ( str : list )
    """

    bounties = {}

    for i in creature_dict:
        if creature_dict[i][0] > 0:
            bounty_page = sh.get_worksheet(creature_dict[i][0])
            bounties_creature = []
            for j in range\
                     (get_column_num_from_letter\
                     (get_first_open_column((bounty_page))) - 1):
                bounties_creature.append(bounty_page.col_values(j+1))
                time.sleep(1)
            bounties[i] = bounties_creature

    return bounties

def get_bounties_per_creature(creature, creature_dict):
    """
    Retrieves a list of all currently posted bounties for the specified
    creature. If no bounties are posted, returns an empty list.

    Args:
        creature (str) - The name of the creature.
        creature_dict (dict - (string : [int, int])) - All bounty information
        for all creatures.

    Returns:
        list
    """

    bounty_list = []

    if creature_dict[creature][0] > 0:
        bounty_page = sh.get_worksheet(creature_dict[creature][0])
        for i in range\
                 (get_column_num_from_letter\
                 (get_first_open_column(bounty_page)) - 1):
            bounty_list.append(bounty_page.col_values(i+1))
            time.sleep(1)

    return bounty_list

def get_creatures_with_bounties(creature_dict):
    """
    Retrieves a list of all creatures that currently have bounties posted for
    them. If no creatures have bounties, returns an empty list.

    Args:
        creature_dict (dict - (string : [int, int])) - All bounty information
        for all creatures.

    Returns:
        list
    """
    creature_list = []

    for i in creature_dict:
        if creature_dict[i][0] > 0:
            creature_list.append(i)

    return creature_list

def get_creature_bounty_num(creature, creature_dict):
    """
    Returns the number of bounties currently open for the specified creature.

    Args:
        creature (str) - The name of the creature.
        creature_dict (dict - (string : [int, int])) - All bounty information
        for all creatures.

    Returns:
        int
    """
    return creature_dict[creature][0]

def is_valid_username(tag):
    """
    Determines if the given username has already been taken by another user.

    Args:
        tag (str) - The user's username.

    Returns:
        False (if username is already taken)
        True
    """
    tags = sh.sheet1.col_values(11)
    time.sleep(2)

    if tag in tags:
        return False
    return True

def add_new_user(name, tag):
    """
    Adds a new user to the worksheet.

    Args:
        name (str) - The given username.
    """
    user_count = len(sh.sheet1.col_values(10))+1
    sh.sheet1.update(f'J{user_count}:K{user_count}', [[name, tag]])