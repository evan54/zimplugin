#!/usr/bin/python3
import sys
import os
from pathlib import Path
import glob
import re
import datetime as dtt

from zim.formats.wiki import Parser, Dumper
from zim.formats import UNCHECKED_BOX, CHECKED_BOX, XCHECKED_BOX, MIGRATED_BOX


NOTEBOOK_PN = Path(sys.argv[1])
JOURNAL_PN = NOTEBOOK_PN / 'Journal'

MIGRATED_HEADER = '==== Migrated ====\n'
VALID = [UNCHECKED_BOX, CHECKED_BOX, XCHECKED_BOX, MIGRATED_BOX]


def migrate_task(el):
    if el.attrib['bullet'] == UNCHECKED_BOX:
        el.attrib['bullet'] = MIGRATED_BOX
    return el 


def is_migrated_line(line):
    return re.match('^ *\[>\].*$', line, re.MULTILINE)


def get_tasks(fn):
    """
    Open file and get list of of pending tasks ('UNCHECKED_BOX')
    Reidentify those tasks as postponed ('MIGRATED_BOX') as overwrite file
    """
    
    # open file and mark all pending as migrated
    with open(fn, 'r') as f:
        tree = Parser().parse(f.read())
    tasks = [t for t in tree.findall('li') if t.attrib['bullet'] == UNCHECKED_BOX]
    tree.replace('li', migrate_task)

    # Write new file while deleting old migrated tasks
    new_lines = Dumper().dump(tree)
    after_migrated = False
    lines_to_keep = []
    for ln in new_lines:
        if not after_migrated or not is_migrated_line(ln):
            lines_to_keep.append(ln)
        after_migrated = ln == MIGRATED_HEADER or after_migrated

    with open(fn, 'w') as f:
        f.writelines(lines_to_keep)
    return tasks


def get_date(fn):
    """parse date from pathname"""
    *_, year, month, day = fn.split('/')
    day = day[:2]
    date = dtt.date(int(year), int(month), int(day))
    return date


def main():
    # load all journal files
    pnfns = glob.glob(str(JOURNAL_PN / '**/*.txt'), recursive=True)
    pnfns.sort()
    all_tasks = []

    # for each file get the tasks that are on the page
    for fn in pnfns:
        date = get_date(fn)
        if date < dtt.date.today():
            tasks = get_tasks(fn)
            if len(tasks) > 0:
                date = get_date(fn)
                all_tasks.append((fn, date, tasks))

    # Update today's file
    pnfn_tdy = str(JOURNAL_PN / dtt.date.today().strftime('%Y/%m/%d')) + '.txt'
    with open(pnfn_tdy, 'r') as f:
        tree = Parser().parse(f.read())
    d = Dumper()
    zim_dump = d.dump(tree)

    # append "migrated" to today's file if not there
    if MIGRATED_HEADER not in zim_dump:
        zim_dump.append(MIGRATED_HEADER)
    i_header = zim_dump.index(MIGRATED_HEADER)

    # Append the tasks under a date header depending where the task came from
    for tasks in all_tasks:
        dt_str = tasks[1].strftime('%Y-%m-%d')
        task = tasks[2]
        for i, t in enumerate(task):
            zim_dump.insert(i_header+1+i, d.dump(t)[0])
    with open(pnfn_tdy, 'w') as f:
        f.writelines(zim_dump)
    
    return all_tasks


if __name__ == '__main__':
    test()
