# gmail-filters-advanced
Script to generate an importable gmail filter XML file from a more manageable config file

It is partiularly useful if you've ever been annoyed by the update-order in which the filters are displayed in Gmail,
or if you perform multiple actions on emails with different combinations of other filters.

## Set up
In ~/.gmail_filters.json

Add something like the following, with your own email and name:
```
{
   "foo@bar.com": {
      "alias": "foo",
      "author": "John Doe",
      "filters": {
      },
      "actions": [
      ]
   }
}
```

Here, we have the ability to configure multiple email addresses, assign an alias to provide to the script, and your name,
which is just placed in the output XML file.

The `filters` dictionary will be keyed by a name given to each search filter,
and `actions` will be a list of applied filters with corresponding actions.

## Filters
A basic filter will have either a `filter` property, or an `extras` property, or both.
Both are strings. `filter` is a raw Gmail search string. `extras` is similar to a search string, what we will call a ref-string.

A ref-string looks like a gmail filter string, but all words that are not "AND", "OR", and only contain letters A-Z, a-z and _
are considered to be the name of another filter, which is substituted into the string.

For example, in this set of filters:
```
"filters": {
   "foo": {
      "filter": "from:foo@gmail.com"
   },
   "foo_bar": {
      "filter": "bar",
      "extras": "AND foo"
   }
},
```
the foo_bar filter will be expanded to "bar AND (from:foo@gmail.com)".
Note that extras is appended to the filter with a space.

The ref-strings can also contain their own parens, minus signs for canceling (like "AND -foo" in the previous example),
and most other gmail filter syntax, which uses special characters.

## Actions
An action is specified with the following format
(note any of these sub-actions can be excluded and that sub-actions with `true`
should simply be excluded if they are not desired):
```
"actions": [
   {
      "filters": [
         "foo OR bar",
         "foo_bar"
        ],
      "label": "FooBar",
      "archive": true,
      "markRead": true,
      "categorize": "updates|forums|personal|social|promotions",
      "star": true,
      "important": "always|never"
   }
]
```

Each item in `filters` in the action can be its own ref-string and is expanded into a seperate exported filter.
This allows for the same action to be applied to many filters, without growing a single filter string to be too large.

## Exporting
Simply run `gmail-filters <alias|email> > mailFilters.xml` and inport into Gmail through settings.
Don't forget to delete your old filters first, or select-all and delete them after.

