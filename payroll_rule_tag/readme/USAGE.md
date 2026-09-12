On the Salary Rules form, one or more tags can be selected and assigned to the
rule, on the "Tags" field.

In salary rules with Python code, totals for a tag can be accessed
using the `tags` browsable collection, with the tag code:

```
result = tags.TAXABLE
```

The code is the tag's Code field, or the tag name in uppercase when no code
is set. An unknown code evaluates to `0.0`, as for the other browsable
collections.

As with salary rule Categories, a tag total only aggregates the rules that
were computed before the rule reading it, so the rule computing a tag total
must have a higher sequence than the rules it is meant to sum up.

Amounts are added to the tag with the same value used for the salary rule
Categories, that is the line total (quantity x rate x amount), not the unit
amount.
