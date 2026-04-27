__doc__ = "Common functions for the formatting of academic reference citations."

article_cit_fmt = '{author}. {title}. {journal}. {year}; {volume}:{pages}.{doi}'
book_cit_fmt = '{author}. {book.title}. {cdate} (Update {mdate}). In: {editors}, editors. {book.journal} (Internet). {book.book_publisher}'
bibtex_fmt = '@{entrytype}{{{citeID},\n{author}{doi}{title}{abstract}{journal}{year}{volume}{pages}{url}}}'

# HTML format strings for citation_html functionality
article_cit_fmt_html = '{author}. {title}. <i>{journal}</i>. {year}; <b>{volume}</b>:{pages}.{doi}'
book_cit_fmt_html = '{author}. <i>{book.title}</i>. {cdate} (Update {mdate}). In: {editors}, editors. <i>{book.journal}</i> (Internet). {book.book_publisher}'


def author_str(author_list_or_string, as_html=False):
    """ Helper function for constructing article citations.

    :param author_list_or_string:
    :return: author(s) str suitable for printed citation
    """
    pass


def citation(**kwargs):
    """ Returns a formatted citation string built from this article's author(s), title,
    journal, year, volume, pages, and doi.

    see cite.article and cite.book for more specific use cases.

    Note that "authors" (as list) will be used preferentially over "author" (as str).

    Keywords:
        as_html: (bool) returns citation with light HTML formatting.
        author: (str) -- prints author as-is without modification
        authors: (list) -- prints as author1 (first in list) as "Lastname_FirstInitials, et al"
        title: (str)
        journal: (str)
        year: (str or int)
        volume: (str or int)
        pages: (str) should be formatted "nn-mm", e.g. "55-58"
        doi: (str)
        
    Returns:
        citation (str)
    """
    pass


def article(**kwargs):
    """ Returns a formatted citation string built from this article's author(s), title,
        journal, year, volume, pages, and doi.

        This function uses the Article format citation template. For example:

        McNally EM, et al. Genetic mutations and mechanisms in dilated cardiomyopathy. Journal of Clinical Investigation. 2013; 123:19-26. doi: 10.1172/JCI62862.

        Keywords:
            journal
            title
            doi
            authors (str or list) -- if str, prints authors without modification.

        Return:
            citation (str)
    """
    pass


def book(book, **kwargs):
    """ Takes a PubMedArticle "book" and formats a citation string.  This is a special type of citation
        built mostly for NCBI GeneReviews and not currently generalizable to other academic books (yet).

        Returns a formatted citation string for a book.  A "book" needs to contain the following attributes:

            author
            title
            book_date_revised
            book_contribution_date
            editors             
            journal
            book_publisher      (may be a URL)

        This function uses the Book format citation template: 

        book_cit_fmt = '{author}. {title}. {cdate} (Update {mdate}). In: {editors}, editors. {journal} (Internet). {book_publisher}'

        For example:

        Tranebjarg L, et al. Jervell and Lange-Nielsen syndrome. 2002 Jul 29 (Updated 2014 Nov 20). In: Pagon RA, et al., editors. GeneReviews (Internet). Seattle (WA): University of Washington, Seattle; 1993-2015. Available from: https://www.ncbi.nlm.nih.gov/books/NBK1405/.

        :param book: PubMedArticle of type "book"
        :param use_html: (bool) whether to return with light HTML formatting
        :return: formatted citation string
        :rtype: str
    """
    pass


def bibtex(**kwargs):
    """ Returns a BibTeX formatted citation string built from the book or article author(s), title,
    journal, year, volume, pages, and doi if the fields exist

    see cite.article and cite.book for more specific use cases.

    see https://ctan.org/tex-archive/biblio/bibtex/contrib/doc/ for more on the BibTeX format

    Note that "authors" (as list) will be used preferentially over "author" (as str).

    Keywords:
        isbook: (bool) returns citation with standard entry type as 'book'
        author: (str) -- prints author as-is without modification
        authors: (list) -- prints as author1 (first in list) as "Lastname_FirstInitials, et al"
        title: (str)
        journal: (str)
        year: (str or int)
        volume: (str or int)
        pages: (str) should be formatted "nn-mm", e.g. "55-58"
        doi: (str)
        
    Returns:
        bibtex citation (str)
    """
    pass


 

