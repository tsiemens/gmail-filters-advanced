# gmail-filters-advanced

A Python 3 script for updating my rediculously convoluted Gmail filters.

I've created the notion of "templates" in my filters, which are copied from
other filters that define the primary version.

Each template is marked with a meta tag in the following format:

`{(M3TA mytemplatename) "match against this stuff"}`

Other filters can reference this (it must be in the general "has text" field),
and running `gmail-filters update` will update these references. The primary
version is that which has only one group, like the example above. Usually I'll use
this to just apply a label.

## Other features
The `replace` command allows you do to do regex replacements on all filters.

# Set up
Install the contents of requirements.txt

Download a client_secret.json file from the Google App Developer Console's API Manager, for an app with just the Gmail API enabled. Put this file at ~/.gmail_filters/client_secret.json. 

# Development
```
make initenv
source env/bin/activate
make update
make test
```
