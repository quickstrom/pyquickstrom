# TodoMVC Testing Notes

## Results (pending)

- Allows adding a blank TODO item (new bug since [showdown][])
    - reagent
- "Toggle all" doesn't untoggle all items when in the "Completed" or "Active" filters (in Completed it circles the state of the first, in Active it toggles just the first one) (new bug since [showdown][])
    - dojo
- doesn't activate the edit input after double click
    - angular2 (failed)
- clears pending input on filter change (or removal of last item)
    - angularjs
    - duel
    - mithril
    - lavaca_require
- no checkboxes
    - angular2_es2015
- no filters
    - knockoutjs_require
    - dijon
- adds pending item on other interaction (double-click other item, change filter, etc)
    - vanillajs
    - vanilla-es6
- no `<strong>` in the todo count
    - vanilla-es6
- adding a new item first shows an empty state (not explictly forbidden by official spec)
    - angular-dart
- commiting an empty todo in edit mode doesn't fully delete it (even if it's hidden), it can be restored with toggle all later
    - backbone_marionette
- incorrect pluralization of "N items left"
    - polymer

### Excluded?

- doesn't run (exception in console)
  - cujo
- not available/compiled
   - react-hooks
   - emberjs_require
- invalid markup (not matching the standard selectors)
   - gwt
- dubious:
  - firebase-angular (async state updates, complicates spec too much)

### Formal Spec Notes

The "app spec" is the plain-English specification.

- We've freely interpreted what correct behavior should be when the app spec
leaves it undefined.

    For instance, the app spec specifies what items should be shown when the
    All/Active/Completed filter changes and that it should be represented with a
    unique route, but it doesn't say what happens to the _rest_ of the UI. We're
    saying that the pending input shouldn't be modified when switching between
    filters, even though the app spec admits that behavior.

    On the other hand, the app spec says nothing about which filter should be
    active after you've removed all todo items and then created a new one, and
    our spec does the same, i.e. it leaves it undefined. Interestingly, there
    seems to be a de facto correct behavior (https://github.com/tastejs/todomvc/pull/1871),
    that the filter should be the same as it was before removing all todo items.
    We have not adopted it in our spec so far.

- We have not formalized the "Persistence" aspect yet.

[showdown]: https://wickstrom.tech/programming/2020/07/02/the-todomvc-showdown-testing-with-webcheck.html
