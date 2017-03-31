import sys
from utils import *
from htmldiff import diff

warc_one = "./assets/sample_sites/wapo/RCH3-889C.warc.gz"
warc_two = "./assets/sample_sites/wapo/NTN7-ADFS.warc.gz"
submitted_url = 'https://www.washingtonpost.com/news/wonk/wp/2013/06/06/how-congress-unknowingly-legalized-prism-in-2007/'

def compare_warcs(warc_one, warc_two, submitted_url_one, submitted_url_two, deletions_file=None, insertions_file=None, both_file=None):
    warc_one_index, urls_one = get_warc_parts(warc_one, submitted_url_one)
    warc_two_index, urls_two = get_warc_parts(warc_two, submitted_url_two)

    warc_one_text = html_to_text(warc_one_index)
    warc_two_text = html_to_text(warc_two_index)

    text_simhash_distance = get_simhash_distance(warc_one_text, warc_two_text)
    missing_resources, added_resources, common_resources = sort_resources(urls_one, urls_two)

    write_diffs(warc_one_index, warc_two_index, deletions_file=None, insertions_file=None, both_file=None)

def write_diffs(a, b, deletions_file=None, insertions_file=None, both_file=None):
    deletions, insertions, both = diff.text_diff(a, b)
    if deletions_file:
        with open(deletions_file, 'rb+') as f:
            f.write(deletions)

    if insertions_file:
        with open(insertions_file, 'rb+') as f:
            f.write(insertions)

    if both_file:
        with open(both_file, 'rb+') as f:
            f.write(both)

if __name__ == '__main__':
    warc_one = sys.argv[1]
    warc_two = sys.argv[2]
    submitted_url_one = sys.argv[3]
    submitted_url_two = sys.argv[4]
    deletions_file = sys.argv[5]
    insertions_file = sys.argv[6]
    both_file = sys.argv[7]

    compare_warcs(warc_one, warc_two, submitted_url_one, submitted_url_two, deletions_file=deletions_file, insertions_file=insertions_file, both_file=both_file)
