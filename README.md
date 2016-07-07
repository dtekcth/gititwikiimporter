# GititWikiImporter

This project aims to be an importer for wiki pages to Gitit.
It is created to read files containing wiki page revisions encoded as JSON.

The expected JSON object representing a revision looks like this:

    {
        "diff": int,
        "author": "AuthorName",
        "comment": "Comment about revision",
        "content": "The content of the revision encoded as HTML"
    }

and we expect the files to contain a dictionary of string keys and revision values like:

       {
        "0":
            {
                "diff": int2,
                "author": "Last author",
                "comment": "Last comment",
                "content: "Last revision content"
            },
        "1":
            {
                "diff": int1,
                "author": "First author",
                "comment": "First comment",
                "content": "First revision content"
            }
       }

The [WikiPageConverter library](https://github.com/dtekcth/wikipageconverter) contains
exposed functions for reading files and parsing JSON revision. There are also functions for
converting the markup language to for instance Markdown. Since `WikiPageConverter` imports
[Pandoc](https:pandoc.org) it is easy to extend the translating features to fit your need.

## Set up

We use [Stack](https://github.com/commercialhaskell/stack) to manage dependencies and so on.
To install `stack` follow the [guide](http://docs.haskellstack.org/en/stable/README/).

When `stack` is all set we need to install the required haskell compiler and libraries
by running the command:

    $ stack setup

Next step is to install all required libraries:

    $ stack install

Now, if there were no errors or anything, the application is built and added to your output
directory, usually ~/.local/.

## Usage


    $ gititwikiimporter SRCDIR DESTDIR [PATTERN]

* SRCDIR is the directory containing the JSON files.
* DESTDIR is the git repo where you want to commit the files.
* [PATTERN] is a list of strings that a file must match at least one of.

Example usage:

    $ gititwikiimporter "path/to/wiki/export/files/" "path/to/git/repo/" "Profiles" "Public"

gititwikiimporter will now attempt to parse all files that contains either Profiles or Public or both inside the `path/to/wiki/export/files/` and commit them inside `path/to/git/repo`. It will keep the directory structure, and replace any '.' with '/'.


Happy hacking!
// Jsb
